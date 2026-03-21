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
     "https://share.google/l56si6WvWzWhAbhlr",
    "https://share.google/oad4TKOTOeP3pmMdY",
    "https://www.izumi-tta.com/taikaiyotei_2026.html",
    "https://share.google/OmlEa7PjGO09b9hIx",
    "https://share.google/helpbNNIdjkP1yc8g",
    "https://share.google/FcReuhJMFCitnELOk",
    "https://share.google/zkAIpAHVkfpUf46m7"
]

KEYWORDS = ["卓球大会", "要項", "申込", "案内"]

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
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        text = soup.get_text()
        lines = text.splitlines()

        # ▼ キーワード含む行だけ抽出
        matched_lines = []
        for line in lines:
            line = line.strip()
            if any(keyword in line for keyword in KEYWORDS):
                matched_lines.append(line)

        # まとめてハッシュ化
        content = "\n".join(matched_lines)
        current_hash = hashlib.md5(content.encode()).hexdigest()

        # 前回と比較
        if url not in state:
            state[url] = current_hash

        elif state[url] != current_hash:
            message = f"🔔 更新検知！\n{url}\n\n該当内容:\n" + "\n".join(matched_lines[:5]) + f"\n\n{datetime.now()}"

            line_bot_api.push_message(
                LINE_USER_ID,
                TextSendMessage(text=message)
            )

            state[url] = current_hash

    except Exception as e:
        print(f"Error: {e}")

# ===== 状態保存 =====
with open(STATE_FILE, "w") as f:
    json.dump(state, f)
