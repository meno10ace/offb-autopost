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
                 'comment': e.get('description', '').strip()} 
                for e in events if 'dateTime' in e['start']]
    except Exception as e:
        print(f"❌ 取得失敗: {e}")
        return []


# --- 3. 画像を生成する関数 ---
def generate_image(today_classes, output_path='final_stories.png'):
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
                # 改行で分けて、一番長い行の横幅を採用する
                w_comment = max(draw.textlength(line, font=font_comment) for line in comment_str.split('\n'))
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
                
                # 改行(\n)の数を数えて、1行増えるごとに間隔を60px広げる
                line_count = cls['comment'].count('\n')
                step_y = 240 + (line_count * 60)
                
            y_offset += step_y

    footer_str = "Omura Fight/Fit Base"
    w_foot = draw.textlength(footer_str, font=font_footer)
    draw.text(((canvas_size[0] - w_foot) / 2, canvas_size[1] - 180), footer_str, font=font_footer, fill=black)

    final_img = bg_image.convert('RGB')
    final_img.save(output_path, quality=95)
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