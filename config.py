import os
from dotenv import load_dotenv

load_dotenv()

# متغیرهای اصلی
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
WEBSITE_URL = os.getenv("WEBSITE_URL", "https://example.com")

# ===== این بخش رو اضافه کن =====
SCRAPER_CONFIG = {
    "wait_time": 5,  # زمان انتظار برای بارگذاری صفحه (ثانیه)
    "scroll_pages": 2,  # تعداد دفعات اسکرول برای بارگذاری بیشتر
    "video_selectors": [
        # سلکتورهای رایج برای پیدا کردن ویدیو توی صفحه اختصاصی
        "video",
        "a[href$='.mp4']",
        "a[href$='.webm']",
        ".download-btn",
        "a[download]",
        "[data-src*='.mp4']",
        ".video-container video",
        ".video-wrapper video",
        "iframe[src*='youtube']",
        "iframe[src*='vimeo']",
    ],
    "exclude_patterns": [
        "ads", "advertisement", "sponsor", "banner"
    ]
}
# ===== تا اینجا =====

# تنظیمات کروم
CHROME_OPTIONS = [
    "--headless",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--window-size=1920,1080"
]
