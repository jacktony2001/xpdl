import os
from dotenv import load_dotenv

load_dotenv()

# اینجا اسم Secrets رو با اون چیزی که ساختید هماهنگ کنید
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # اسم جدید
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")      # اسم جدید
WEBSITE_URL = os.getenv("WEBSITE_URL", "https://example.com")

# تنظیمات کروم (برای محیط گیتهاب)
CHROME_OPTIONS = [
    "--headless",  # بدون نمایش مرورگر
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--window-size=1920,1080"
]
