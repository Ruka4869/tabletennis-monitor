import requests
from bs4 import BeautifulSoup
import hashlib
import json
import os
from datetime import datetime
from linebot import LineBotApi
from linebot.models import TextSendMessage
from urllib.parse import urljoin

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

        file_links = []

        # ▼ aタグからファイルリンク抽出
        for a in soup.find_all("a", href=True):
            href = a["href"]

            if any(href.lower().endswith(ext) for ext in FILE_EXTENSIONS):
                full_url = urljoin(url, href)
                file_links.append(full_url)

        # ▼ share.google対策：本文中のURLも拾う
        text = soup.get_text()
        for word in text.split():
            if any(ext in word.lower() for ext in FILE_EXTENSIONS):
                file_links.append(word)

        # 重複除去
        file_links = sorted(set(file_links))

        # ▼ ファイルが1つも取れない場合はスキップ（誤検知防止）
        if not file_links:
            continue

        current_hash = hashlib.md5("\n".join(file_links).encode()).hexdigest()

        # 初回登録
        if url not in state:
            state[url] = {
                "hash": current_hash,
                "files": file_links
            }

        else:
            old_files = state[url].get("files", [])

            # ▼ 新規追加のみ検知
            new_files = list(set(file_links) - set(old_files))

            if new_files:
                message = (
                    f"📄 新しいファイルが追加されました！\n{url}\n\n"
                    + "\n".join(new_files[:5]) +
                    f"\n\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )

                line_bot_api.push_message(
                    LINE_USER_ID,
                    TextSendMessage(text=message)
                )

            # 状態更新
            state[url] = {
                "hash": current_hash,
                "files": file_links
            }

    except Exception as e:
        print(f"Error ({url}): {e}")

# ===== 状態保存 =====
with open(STATE_FILE, "w") as f:
    json.dump(state, f, ensure_ascii=False, indent=2)
