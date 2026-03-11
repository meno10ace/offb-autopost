import os
import datetime
import time
import requests
import base64
from PIL import Image, ImageDraw, ImageFont
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

# === 1. 設定と準備 ===
load_dotenv()

# Googleカレンダー設定
CALENDAR_ID = os.getenv('CALENDAR_ID')
CREDENTIALS_FILE = os.getenv('CREDENTIALS_FILE', 'credentials.json')

# Instagram & ImgBB 設定 (すべて環境変数から取得)
IG_ACCESS_TOKEN = os.getenv('IG_ACCESS_TOKEN')
IG_ACCOUNT_ID = os.getenv('IG_ACCOUNT_ID')
IMGBB_API_KEY = os.getenv('IMGBB_API_KEY')

if not all([CALENDAR_ID, IG_ACCESS_TOKEN, IG_ACCOUNT_ID, IMGBB_API_KEY]):
    print("❌ エラー: 必要な環境変数が設定されていません！")
    exit()
# Instagram & ImgBB 設定
# ⚠️ 本番運用時はこれらのキーも .env ファイルに隠すことをおすすめします！
IG_ACCESS_TOKEN = 'EAAcZAChsJaa8BQyzMdWZBxYNX5jpFp1KeSLJrJwnP78lZBjNdrqZBZBgdqjVDDPCessia3N0LmLSbTZBVkYW9juqtrkQavUiFnnBNU5b6jtC6P3GN6deFkq9Rs3Fm3Wzm8vFu1uipPeTePXeClQkEfoUgUo8dHZC3ZCPlj1lrjfie6HIcpMQKUgoNEievJBZCrZA0f6QdC1QawadZBVV1fHU8v4rOFVj1JeYgZBzFwVhYwQfx3cbZAs8ZCCmWu7zeVCQvM05Xa3XLAAtsKDIlc'
IG_ACCOUNT_ID = '17841471455745641'
IMGBB_API_KEY = 'ここにImgBBのAPIキーを貼り付けてください' # ★ImgBBのサイトで取得したキーを貼ってください

# --- 2. カレンダーから今日の予定を取得する関数 ---
def get_todays_classes():
    print("📅 Googleカレンダーから本日の予定を取得しています...")
    scopes = ['https://www.googleapis.com/auth/calendar.readonly']
    try:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
        service = build('calendar', 'v3', credentials=creds)
    except Exception as e:
        print(f"❌ 認証エラー: {e}")
        return []

    now = datetime.datetime.now()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    timeMin = start_of_day.isoformat() + '+09:00'
    timeMax = end_of_day.isoformat() + '+09:00'

    try:
        events_result = service.events().list(
            calendarId=CALENDAR_ID, timeMin=timeMin, timeMax=timeMax,
            singleEvents=True, orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        today_classes = []
        for event in events:
            if 'dateTime' not in event['start']:
                continue
                
            start_time = event['start']['dateTime'][11:16]
            end_time = event['end']['dateTime'][11:16]
            
            name = event.get('summary', 'タイトルなし')
            comment = event.get('description', '').strip()
            if '\n' in comment:
                comment = comment.split('\n')[0] 
                
            today_classes.append({
                'time': f"{start_time} - {end_time}",
                'name': name,
                'comment': comment
            })
            
        return today_classes

    except Exception as e:
        print(f"❌ カレンダー取得エラー: {e}")
        return []

# --- 3. 画像を生成する関数 ---
def generate_gym_stories_image(today_classes, output_path='final_stories.png'):
    print("🎨 スケジュール画像を生成しています...")
    canvas_size = (1080, 1920)
    base_image_path = 'base_image.jpg' 
    font_path = 'font.ttf'             
    
    black = (0, 0, 0, 255)
    white = (255, 255, 255, 255)
    red = (220, 0, 0, 255)

    if os.path.exists(base_image_path):
        bg_image = Image.open(base_image_path).convert('RGBA')
        bg_image = bg_image.resize(canvas_size, Image.Resampling.LANCZOS)
    else:
        bg_image = Image.new('RGBA', canvas_size, white)

    draw = ImageDraw.Draw(bg_image)

    try:
        font_day = ImageFont.truetype(font_path, 200)
        font_date = ImageFont.truetype(font_path, 60)
        font_greeting = ImageFont.truetype(font_path, 55)
        font_class_name = ImageFont.truetype(font_path, 90) 
        font_class_time = ImageFont.truetype(font_path, 65) 
        font_comment = ImageFont.truetype(font_path, 50)  
        font_footer = ImageFont.truetype(font_path, 80)
    except IOError:
        print(f"❌ Error: Font file not found at {font_path}")
        return False

    now = datetime.datetime.now()
    day_str = now.strftime("%A")
    w_day = draw.textlength(day_str, font=font_day)
    draw.text(((canvas_size[0] - w_day) / 2, 80), day_str, font=font_day, fill=black)

    date_str = f"{now.month}/{now.day}"
    w_date = draw.textlength(date_str, font=font_date)
    x_date = (canvas_size[0] - w_date) / 2
    y_date = 330
    draw.rounded_rectangle([x_date - 20, y_date - 10, x_date + w_date + 20, y_date + 70], radius=10, fill=black)
    draw.text((x_date, y_date), date_str, font=font_date, fill=white)

    greeting_str = "本日も宜しくお願い致します"
    w_greet = draw.textlength(greeting_str, font=font_greeting)
    x_greet = (canvas_size[0] - w_greet) / 2
    y_greet = 420
    draw.rounded_rectangle([x_greet - 30, y_greet - 10, x_greet + w_greet + 30, y_greet + 70], radius=10, fill=black)
    draw.text((x_greet, y_greet), greeting_str, font=font_greeting, fill=white)

    start_y = 550  
    y_offset = start_y
    
    if not today_classes:
        msg = "本日のクラスはありません"
        w = draw.textlength(msg, font=font_class_name)
        draw.text(((canvas_size[0] - w) / 2, y_offset + 200), msg, font=font_class_name, fill=black)
    else:
        max_overall_width = 0
        for cls in today_classes:
            name_str = cls['name']
            time_str = cls['time'].replace("-", "〜")
            w_name = draw.textlength(name_str, font=font_class_name)
            w_time = draw.textlength(time_str, font=font_class_time)
            w_comment = 0
            if cls.get('comment'):
                comment_str = f"※{cls['comment']}"
                w_comment = draw.textlength(comment_str, font=font_comment)
            max_overall_width = max(max_overall_width, w_name, w_time, w_comment)
        
        global_x_start = (canvas_size[0] - max_overall_width) / 2

        for cls in today_classes:
            name_str = cls['name']
            time_str = cls['time'].replace("-", "〜")
            draw.text((global_x_start, y_offset), name_str, font=font_class_name, fill=black)
            draw.text((global_x_start, y_offset + 85), time_str, font=font_class_time, fill=black)
            
            step_y = 200 
            if cls.get('comment'):
                comment_str = f"※{cls['comment']}"
                draw.text((global_x_start, y_offset + 155), comment_str, font=font_comment, fill=red)
                step_y = 240 
            y_offset += step_y 

    footer_str = "Omura Fight/Fit Base"
    w_foot = draw.textlength(footer_str, font=font_footer)
    draw.text(((canvas_size[0] - w_foot) / 2, canvas_size[1] - 180), footer_str, font=font_footer, fill=black)

    final_img = bg_image.convert('RGB')
    final_img.save(output_path, quality=95)
    print(f"✅ 画像生成完了: {output_path}")
    return True

# --- 4. 生成した画像を一時的にURL化する関数（ImgBB） ---
def upload_to_imgbb(image_path):
    print("☁️ 画像をURL化しています...")
    try:
        with open(image_path, "rb") as file:
            payload = {
                "key": IMGBB_API_KEY,
                "image": base64.b64encode(file.read()),
                "expiration": 600 # 10分で自動消去されるエコ設定
            }
            res = requests.post("https://api.imgbb.com/1/upload", payload)
            
            if res.status_code == 200:
                url = res.json()["data"]["url"]
                print(f"✅ URL化成功: {url}")
                return url
            else:
                print("❌ ImgBBアップロード失敗:", res.text)
                return None
    except Exception as e:
        print(f"❌ 画像読み込みエラー: {e}")
        return None

# --- 5. Instagramへ投稿する関数 ---
def post_to_instagram(image_url):
    print("🚀 Instagramへの投稿プロセスを開始します...")
    
    # 投稿のキャプション（文章）を生成
    now = datetime.datetime.now()
    caption = f"【本日のスケジュール】\n{now.month}月{now.day}日のクラス予定です🥊\n本日もよろしくお願いします！\n\n#OmuraFightFitBase #大村市 #キックボクシング"

    print("📸 1/2: Instagramサーバーへデータを送信中...")
    container_url = f"https://graph.facebook.com/v25.0/{IG_ACCOUNT_ID}/media"
    container_payload = {
        'image_url': image_url,
        'caption': caption,
        'access_token': IG_ACCESS_TOKEN
    }
    
    response = requests.post(container_url, data=container_payload)
    result = response.json()
    
    if 'id' not in result:
        print("❌ データの送信失敗:", result)
        return
        
    creation_id = result['id']
    print(f"✅ 送信完了！ (処理ID: {creation_id})")
    
    # Instagram側での画像処理を待つ
    time.sleep(8) 

    print("📢 2/2: フィードへ公開中...")
    publish_url = f"https://graph.facebook.com/v25.0/{IG_ACCOUNT_ID}/media_publish"
    publish_payload = {
        'creation_id': creation_id,
        'access_token': IG_ACCESS_TOKEN
    }
    
    publish_response = requests.post(publish_url, data=publish_payload)
    publish_result = publish_response.json()
    
    if 'id' in publish_result:
        print(f"🎉🎉🎉 大成功！！！ 今日のスケジュールがInstagramに投稿されました！ (投稿ID: {publish_result['id']})")
    else:
        print("❌ 公開失敗:", publish_result)

# --- メイン処理 ---
if __name__ == '__main__':
    print("="*40)
    print("🤖 ジム自動投稿エージェント 起動")
    print("="*40)
    
    # 1. カレンダー取得
    classes_data = get_todays_classes()
    print(f"取得したクラス数: {len(classes_data)}件")
    
    # 2. 画像生成
    image_filename = 'final_stories.png'
    if generate_gym_stories_image(classes_data, image_filename):
        # 3. 画像をURL化 (ImgBB API)
        public_image_url = upload_to_imgbb(image_filename)
        
        if public_image_url:
            # 4. Instagramへ投稿
            post_to_instagram(public_image_url)
            
    print("="*40)
    print("🏁 すべての処理が完了しました！")
    print("="*40)