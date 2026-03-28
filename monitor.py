import requests
from bs4 import BeautifulSoup
import hashlib
import json
import os
from datetime import datetime
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

KEYWORDS = ["要項", "大会", "杯", "案内"]
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

# ===== メイン処理 =====
for url in SITES:
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        found_items = []

        # ===== リンク検知 =====
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)

            # PDF / Excel
            if any(ext in href.lower() for ext in FILE_KEYWORDS):
                found_items.append(href)

            # キーワード含むリンク
            if any(keyword in text for keyword in KEYWORDS):
                found_items.append(text)

        # ===== 本文キーワード検知 =====
        full_text = soup.get_text()
        for keyword in KEYWORDS:
            if keyword in full_text:
                found_items.append(keyword)

        # ===== 重複削除 =====
        found_items = list(set(found_items))

        # ===== ハッシュ（ここ重要）=====
        content = full_text + "\n".join(sorted(found_items))
        current_hash = hashlib.md5(content.encode()).hexdigest()

        # ===== 初回登録 =====
        if url not in state:
            state[url] = current_hash
            continue

        # ===== 更新検知 =====
        if state[url] != current_hash:
            message = (
                f"🔔 更新検知！\n"
                f"{url}\n"
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            line_bot_api.push_message(
                LINE_USER_ID,
                TextSendMessage(text=message)
            )

            state[url] = current_hash

    except Exception as e:
        print(f"Error at {url}: {e}")

# ===== state保存 =====
with open(STATE_FILE, "w") as f:
    json.dump(state, f, indent=2, ensure_ascii=False)
