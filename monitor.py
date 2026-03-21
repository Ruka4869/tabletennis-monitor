import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime
from linebot import LineBotApi
from linebot.models import TextSendMessage
from urllib.parse import urljoin

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

KEYWORDS = ["要項", "大会", "杯", "案内"]
FILE_EXTENSIONS = [".pdf", ".xls", ".xlsx"]

STATE_FILE = "state.json"

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# ===== 状態読み込み =====
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
else:
    state = {}

# ===== メイン処理 =====
for url in SITES:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # =========================
        # ① PDF / Excel検知
        # =========================
        file_links = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if any(href.lower().endswith(ext) for ext in FILE_EXTENSIONS):
                file_links.add(urljoin(url, href))

        # =========================
        # ② キーワード検知
        # =========================
        text = soup.get_text()
        lines = text.splitlines()

        keyword_lines = set()

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if any(k in line for k in KEYWORDS):
                # 日時などノイズ除去
                cleaned = re.sub(r"\d{4}.*", "", line)
                cleaned = re.sub(r"\d{1,2}:\d{2}(:\d{2})?", "", cleaned)
                cleaned = cleaned.strip()

                if cleaned:
                    keyword_lines.add(cleaned)

        # =========================
        # 初期化
        # =========================
        if url not in state:
            state[url] = {
                "files": list(file_links),
                "keywords": list(keyword_lines)
            }
            continue

        old_files = set(state[url].get("files", []))
        old_keywords = set(state[url].get("keywords", []))

        # =========================
        # 差分検知
        # =========================
        new_files = file_links - old_files
        new_keywords = keyword_lines - old_keywords

        # =========================
        # 通知
        # =========================
        if new_files or new_keywords:
            message = f"🔔 更新検知\n{url}\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            line_bot_api.push_message(
                LINE_USER_ID,
                TextSendMessage(text=message)
            )

        # 状態更新
        state[url] = {
            "files": list(file_links),
            "keywords": list(keyword_lines)
        }

    except Exception as e:
        print(f"Error ({url}): {e}")

# ===== 保存 =====
with open(STATE_FILE, "w") as f:
    json.dump(state, f, ensure_ascii=False, indent=2)
