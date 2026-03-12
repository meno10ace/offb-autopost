import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()
IG_ACCESS_TOKEN = os.getenv('IG_ACCESS_TOKEN')
IG_ACCOUNT_ID = os.getenv('IG_ACCOUNT_ID')

# 📢 ここに自分のGitHubのRaw URLを入れてください
RAW_URL = 'https://raw.githubusercontent.com/meno10ace/offb-autopost/main/final_stories.png'
# キャッシュ回避のためにタイムスタンプを付ける
IMAGE_URL = f"{RAW_URL}?t={int(time.time())}"

def post_to_instagram():
    print(f"🚀 Instagramへ送信中: {IMAGE_URL}")
    
    # 1. コンテナ作成 (data= を使用)
    url1 = f"https://graph.facebook.com/v25.0/{IG_ACCOUNT_ID}/media"
    payload1 = {'image_url': IMAGE_URL, 'media_type': 'STORIES', 'access_token': IG_ACCESS_TOKEN}
    res1 = requests.post(url1, data=payload1).json()
    
    if 'id' not in res1:
        print(f"❌ Step 1 失敗: {res1}")
        return
        
    print(f"✅ 画像アップロード完了 (ID: {res1['id']})。15秒待ちます...")
    time.sleep(15)

    # 2. 公開
    url2 = f"https://graph.facebook.com/v25.0/{IG_ACCOUNT_ID}/media_publish"
    payload2 = {'creation_id': res1['id'], 'access_token': IG_ACCESS_TOKEN}
    res2 = requests.post(url2, data=payload2).json()
    
    if 'id' in res2:
        print("🎉🎉🎉 ストーリーズ投稿に大成功しました！")
    else:
        print(f"❌ Step 2 失敗: {res2}")

if __name__ == '__main__':
    post_to_instagram()