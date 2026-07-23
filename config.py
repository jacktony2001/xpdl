import os
from dotenv import load_dotenv

load_dotenv()

# اسم متغیرها با workflow هماهنگ شد
BOT_TOKEN = os.getenv("BOT_TOKEN")  # از workflow میاد
CHAT_ID = os.getenv("CHAT_ID")      # از workflow میاد
WEBSITE_URL = os.getenv("WEBSITE_URL", "https://example.com")

# تنظیمات کروم (برای محیط گیتهاب)
CHROME_OPTIONS = [
    "--headless",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--window-size=1920,1080"
]
