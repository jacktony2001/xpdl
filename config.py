import os
from dotenv import load_dotenv

load_dotenv()

# ==============================================
# متغیرهای اصلی (از Secrets گیت‌هاب می‌آیند)
# ==============================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
WEBSITE_URL = os.getenv("WEBSITE_URL", "https://example.com")

# ==============================================
# تنظیمات اسکرپر
# ==============================================
SCRAPER_CONFIG = {
    # زمان انتظار برای بارگذاری صفحات (ثانیه)
    "wait_time": 10,
    
    # تعداد دفعات اسکرول برای بارگذاری بیشتر (صفحه اصلی)
    # اگه سایتت بی‌نهایت اسکرول داره، بذار 3 یا 5
    # اگه صفحه‌بندی داره، بذار 0
    "scroll_pages": 2,
    
    # سلکتورهای دانلود (برای صفحه اختصاصی ویدیو)
    # اگه سلکتور جدیدی پیدا کردی، اینجا اضافه کن
    "video_selectors": [
        "p.text-center.download-ready a",  # سلکتور اصلی سایت شما
        "a[href$='.mp4']",
        "a[href$='.webm']",
        ".download-btn",
        "a[download]",
        "video",
        "video[src]",
        "[data-src*='.mp4']",
        "a[href*='mp4-cdn']"
    ],
    
    # الگوهای تبلیغاتی برای حذف
    "exclude_patterns": [
        "ads",
        "advertisement",
        "sponsor",
        "banner",
        "popup"
    ]
}

# ==============================================
# تنظیمات کروم (برای محیط گیت‌هاب)
# ==============================================
CHROME_OPTIONS = [
    "--headless",  # بدون نمایش مرورگر (اجباری برای گیت‌هاب)
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--window-size=1920,1080",
    "--disable-blink-features=AutomationControlled",
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]
