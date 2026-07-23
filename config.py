import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
WEBSITE_URL = os.getenv("WEBSITE_URL", "https://example.com")

SCRAPER_CONFIG = {
    "wait_time": 10,
    "scroll_pages": 2,
    "video_selectors": [
        "p.text-center.download-ready a",
        "a[href$='.mp4']",
        "a[href$='.webm']",
        ".download-btn",
        "a[download]",
        "video",
        "video[src]",
        "[data-src*='.mp4']",
        "a[href*='mp4-cdn']"
    ],
    "exclude_patterns": [
        "ads",
        "advertisement",
        "sponsor",
        "banner",
        "popup"
    ],
    # تنظیمات فشرده‌سازی - نسخه نهایی
    "compression": {
        "enabled": True,
        "max_size_mb": 48,           # حداکثر حجم نهایی (کمی کمتر از 50)
        "scale": "480:320",          # رزولوشن پایین (برای فشرده‌سازی بیشتر)
        "crf": 35,                   # کیفیت پایین‌تر (عدد بیشتر = کیفیت کمتر)
        "audio_bitrate": "48k",      # بیت‌ریت پایین‌تر
        "preset": "fast"
    }
}

CHROME_OPTIONS = [
    "--headless",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--window-size=1920,1080",
    "--disable-blink-features=AutomationControlled",
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]
