import requests
from bs4 import BeautifulSoup
import hashlib
import json
import os
import re
from datetime import datetime
from urllib.parse import urljoin
from linebot import LineBotApi
from linebot.models import TextSendMessage

# ===== 設定 =====
SITES = [
    "https://www.sendai-tta.info/index.html",
    "http://www.miyagi-tta.com/",
    "https://miyagino-tta.jimdofree.com/",
    "https://tapinpon.wixsite.com/taihakutt",
    "https://tsuneminagasawa.wixsite.com/my-site",
    "https://www.izumi-tta.com/index.htm",
    "https://sayaiwagogo.wixsite.com/my-site/%E3%83%80%E3%82%A6%E3%83%B3%E3%83%AD%E3%83%BC%E3%83%89"
]

KEYWORDS = ["要項", "大会", "杯", "案内", "更新", "お知らせ"]
FILE_KEYWORDS = [".pdf", ".xls", ".xlsx"]

STATE_FILE = "state.json"

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# ===== state読み込み =====
try:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
    else:
        state = {}
except:
    state = {}

# ===== 意味のある文章か判定 =====
def is_meaningful_text(text):
    text = text.strip()

    # 日付のみ
    if re.fullmatch(r"\d{4}[/-]\d{1,2}[/-]\d{1,2}", text):
        return False

    if re.fullmatch(r"\d{4}年\d{1,2}月\d{1,2}日", text):
        return False

    # 「更新日：2026/03/28」など短い日付情報だけ
    if re.fullmatch(r".*(更新日|最終更新).*\d{4}.*", text) and len(text) < 20:
        return False

    return True

# ===== メイン処理 =====
for url in SITES:
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        detected_items = []

        # ===== ① リンク検知 =====
        for a in soup.find_all("a", href=True):
            href = urljoin(url, a["href"].strip())
            text = a.get_text(strip=True)

            # ファイル
            if any(ext in href.lower() for ext in FILE_KEYWORDS):
                detected_items.append(f"FILE::{href}")

            # キーワードリンク
            if any(keyword in text for keyword in KEYWORDS):
                if is_meaningful_text(text):
                    detected_items.append(f"TEXT::{text}")

        # ===== ② 本文検知 =====
        for t in soup.stripped_strings:
            if any(keyword in t for keyword in KEYWORDS):

                cleaned = t.strip()

                if not is_meaningful_text(cleaned):
                    continue

                if len(cleaned) > 5:
                    detected_items.append(f"BODY::{cleaned}")

        # ===== 整理 =====
        detected_items = sorted(list(set(detected_items)))

        content = "\n".join(detected_items)
        current_hash = hashlib.md5(content.encode()).hexdigest()

        # ===== 初回登録 =====
        if url not in state:
            state[url] = {
                "hash": current_hash,
                "items": detected_items
            }
            continue

        old_items = state[url]["items"]
        added = list(set(detected_items) - set(old_items))

        # ===== 更新検知 =====
        if added:
            message = (
                f"🔔 更新検知！\n{url}\n"
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                "▼追加内容\n" +
                "\n".join(added[:5])
            )

            line_bot_api.push_message(
                LINE_USER_ID,
                TextSendMessage(text=message)
            )

        # ===== state更新 =====
        state[url] = {
            "hash": current_hash,
            "items": detected_items
        }

    except Exception as e:
        print(f"Error at {url}: {e}")

# ===== 保存 =====
with open(STATE_FILE, "w") as f:
    json.dump(state, f, indent=2, ensure_ascii=False)
