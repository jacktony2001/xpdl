# config.py (نسخه ترکیبی و به‌روز شده)

# --- تنظیمات مربوط به ربات تلگرام (دست نخورده باقی بماند) ---
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN" 
CHAT_ID = "YOUR_CHAT_ID"

# --- تنظیمات کروم ---
CHROME_OPTIONS = [
    "--headless",           
    "--no-sandbox",         
    "--disable-dev-shm-usage", 
    "--disable-gpu",        
    "--window-size=1920,1080", 
    "--disable-extensions", 
    "--log-level=3",        
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36", 
]

# --- تنظیمات اسکرپر ---
SCRAPER_CONFIG = {
    "wait_time_homepage": 7,           
    "wait_time_video_page": 15,          
    "wait_time_scroll": 3,             
    "extra_wait_for_download_content": 5, 
    "max_videos_per_run": 10,
    "scroll_pages": 2,
}

# --- آدرس اصلی سایت ---
WEBSITE_URL = "https://www.xnxx.com" # آدرس سایت خود را اینجا قرار دهید

# ... ممکنه تنظیمات دیگه ای هم داشته باشید ... 
