import os
import datetime
from PIL import Image, ImageDraw, ImageFont
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()
CALENDAR_ID = os.getenv('CALENDAR_ID')
CREDENTIALS_FILE = os.getenv('CREDENTIALS_FILE', 'credentials.json')

def get_todays_classes():
    print("📅 カレンダー取得中...")
    scopes = ['https://www.googleapis.com/auth/calendar.readonly']
    try:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
        service = build('calendar', 'v3', credentials=creds)
        now = datetime.datetime.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        events = service.events().list(
            calendarId=CALENDAR_ID, timeMin=start_of_day.isoformat() + '+09:00',
            timeMax=end_of_day.isoformat() + '+09:00', singleEvents=True, orderBy='startTime'
        ).execute().get('items', [])
        
        return [{'time': f"{e['start']['dateTime'][11:16]} - {e['end']['dateTime'][11:16]}",
                 'name': e.get('summary', ''),
                 'comment': e.get('description', '').strip().split('\n')[0]} 
                for e in events if 'dateTime' in e['start']]
    except Exception as e:
        print(f"❌ 取得失敗: {e}")
        return []


# --- 3. 画像生成関数 ---
def generate_image(today_classes, output_path='final_stories.png'):
    canvas_size = (1080, 1920)
    base_image_path = 'base_image.jpg' 
    font_path = 'font.ttf' 
    black, white, red = (0, 0, 0, 255), (255, 255, 255, 255), (220, 0, 0, 255)

    if os.path.exists(base_image_path):
        bg_image = Image.open(base_image_path).convert('RGBA').resize(canvas_size, Image.Resampling.LANCZOS)
    else:
        bg_image = Image.new('RGBA', canvas_size, white)
    
    draw = ImageDraw.Draw(bg_image)
    
    try:
        font_day = ImageFont.truetype(font_path, 200)
        font_date = ImageFont.truetype(font_path, 60)
        font_class_name = ImageFont.truetype(font_path, 90)
        font_class_time = ImageFont.truetype(font_path, 65)
        font_comment = ImageFont.truetype(font_path, 50)
    except:
        print("⚠️ フォント読み込み失敗。デフォルトを使用します。")
        font_day = font_date = font_class_name = ImageFont.load_default()

    now = datetime.datetime.now()
    day_str = now.strftime("%A")
    draw.text(((canvas_size[0] - draw.textlength(day_str, font=font_day)) / 2, 80), day_str, font=font_day, fill=black)

    y_offset = 550
    for cls in today_classes:
        draw.text((150, y_offset), cls['name'], font=font_class_name, fill=black)
        draw.text((150, y_offset + 85), cls['time'].replace("-", "〜"), font=font_class_time, fill=black)
        if cls['comment']:
            draw.text((150, y_offset + 155), f"※{cls['comment']}", font=font_comment, fill=red)
            y_offset += 240
        else:
            y_offset += 200

    bg_image.convert('RGB').save(output_path, quality=95)
    print(f"✅ 画像生成完了: {output_path}")

# def generate_image(classes):
#     print("🎨 画像生成中...")
#     bg = Image.open('base_image.jpg').convert('RGBA').resize((1080, 1920)) if os.path.exists('base_image.jpg') else Image.new('RGBA', (1080, 1920), (255,255,255,255))
#     draw = ImageDraw.Draw(bg)
#     font = ImageFont.truetype('font.ttf', 90)
#     font_s = ImageFont.truetype('font.ttf', 65)
    
#     y = 550
#     for c in classes:
#         draw.text((150, y), c['name'], font=font, fill=(0,0,0,255))
#         draw.text((150, y+85), c['time'], font=font_s, fill=(0,0,0,255))
#         y += 200

#     bg.convert('RGB').save('final_stories.png', quality=95)
#     print("✅ final_stories.png を作成しました！")

if __name__ == '__main__':
    classes = get_todays_classes()
    generate_image(classes)