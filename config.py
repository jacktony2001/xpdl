import os
from dotenv import load_dotenv

load_dotenv()

# متغیرهای اصلی
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
# WEBSITE_URL رو حتماً چک کن که آدرس درست باشه (مثلا https://www.xnxx.com/search/milf)
WEBSITE_URL = os.getenv("WEBSITE_URL", "https://example.com") 

# تنظیمات پیشرفته اسکرپر (می‌تونی خودت تغییر بدی)
SCRAPER_CONFIG = {
    "wait_time": 5,  # زمان انتظار برای بارگذاری صفحه (ثانیه)
    "scroll_pages": 2,  # تعداد دفعات اسکرول برای بارگذاری بیشتر (اگه نیاز بود بیشتر کن)
    # "max_videos_to_process": 10, # این خط الان در scraper.py مستقیم نوشته شده، ولی میتونی اینجا هم بذاری
    "video_selectors": [
        # سلکتورهای رایج برای پیدا کردن ویدیو (در صورت نیاز)
        "video",
        "a[href$='.mp4']",
        "a[href$='.webm']",
        ".video-container video",
        ".video-wrapper video",
        "[data-src*='.mp4']",
        ".download-btn",
        "a[download]",
        ".video-link",
        ".player-container video",
        ".video-player video",
        "iframe[src*='youtube']",
        "iframe[src*='vimeo']",
        "iframe[src*='dailymotion']",
    ],
    "exclude_patterns": [
        "ads", "advertisement", "sponsor", "banner"  # حذف تبلیغات
    ]
}

# تنظیمات کروم (برای محیط گیتهاب)
CHROME_OPTIONS = [
    "--headless",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--window-size=1920,1080",
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]
