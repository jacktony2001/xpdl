import os
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv()

# توکن ربات تلگرام (از محیط یا secrets)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
WEBSITE_URL = os.getenv("WEBSITE_URL", "https://example.com")

# تنظیمات کروم (برای محیط گیتهاب)
CHROME_OPTIONS = [
    "--headless",  # بدون نمایش مرورگر
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--window-size=1920,1080"
]
