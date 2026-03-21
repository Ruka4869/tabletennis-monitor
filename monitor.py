import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
from linebot import LineBotApi
from linebot.models import TextSendMessage

# LINE設定
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_USER_ID = os.environ.get('LINE_USER_ID')
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# 監視対象サイト
SITES = [
    "https://www.jtta.or.jp/",
    "https://tabletennisworld.com/",
    "https://example.com/tournaments",
]

# キーワード
KEYWORDS = ["大会", "要項", "申込", "案内"]

def load_state():
    """state.json から前回の状態を読み込み"""
    if os.path.exists('state.json'):
        with open('state.json', 'r') as f:
            return json.load(f)
    return {}

def save_state(state):
    """state.json に現在の状態を保存"""
    with open('state.json', 'w') as f:
        json.dump(state, f, indent=2)

def check_site(url):
    """サイトをチェック"""
    try:
        response = requests.get(url, timeout=10)
        response.encoding = 'utf-8'
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_keywords(content):
    """キーワードを抽出"""
    found = []
    for keyword in KEYWORDS:
        if keyword in content:
            found.append(keyword)
    return found

def send_line_message(message):
    """LINE通知を送信"""
    try:
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=message))
        print(f"LINE通知送信: {message}")
    except Exception as e:
        print(f"LINE送信エラー: {e}")

def main():
    state = load_state()
    
    for url in SITES:
        print(f"チェック中: {url}")
        content = check_site(url)
        
        if not content:
            continue
        
        # キーワード抽出
        keywords = extract_keywords(content)
        
        # ハッシュ値で変更検出
        import hashlib
        current_hash = hashlib.md5(content.encode()).hexdigest()
        
        if url not in state:
            state[url] = {"hash": None, "keywords": []}
        
        # 変更があったか確認
        if state[url]["hash"] != current_hash:
            message = f"🔔 {url} が更新されました！\n"
            if keywords:
                message += f"キーワード: {', '.join(keywords)}\n"
            message += f"更新時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            send_line_message(message)
            state[url]["hash"] = current_hash
            state[url]["keywords"] = keywords
    
    save_state(state)
    print("監視完了")

if __name__ == "__main__":
    main()
