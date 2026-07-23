# config.py
import os

# تنظیمات تلگرام
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', 'YOUR_CHAT_ID_HERE')

# تنظیمات هدف
BASE_URL = os.getenv('TARGET_URL', "https://www.xnxx.com/search/sexy")

# الگوهای regex برای استخراج ویدیو (اولویت بالا به پایین)
VIDEO_REGEX_PATTERNS = [
    r'"url":"(https?://[^"]+\.mp4[^"]*)"',
    r'"videoUrl":"(https?://[^"]+\.mp4[^"]*)"',
    r'"contentUrl":"(https?://[^"]+\.mp4[^"]*)"',
    r'"src":"(https?://[^"]+\.mp4[^"]*)"',
    r'html5player\.setVideoUrlHigh\([\'"]([^\'"]+)[\'"]\)',
    r'html5player\.setVideoUrlLow\([\'"]([^\'"]+)[\'"]\)',
    r'setVideoUrlHigh\([\'"]([^\'"]+)[\'"]\)',
    r'setVideoUrlLow\([\'"]([^\'"]+)[\'"]\)',
    r'"video":\s*{\s*"url":\s*"([^"]+)"',
    r'video_url\s*[=:]\s*["\']([^"\']+)["\']',
]

# سلکتورهای CSS
SELECTORS = {
    'video_links': 'div.thumb a, a[href*="/video-"]',
    'title': 'h1.page-title, h1.title, h1',
    'video': 'video',
    'duration': 'span.duration, .video-duration',
}

# تنظیمات فیلتر
EXCLUDE_PATTERNS = ['ad', 'sponsored', 'promo', 'advertisement', 'login', 'signup']
MIN_DURATION_SECONDS = 30
MAX_FILE_SIZE_MB = 50

# تنظیمات اجرا
CHECK_INTERVAL_HOURS = 6
MAX_VIDEOS_PER_RUN = 5
HEADLESS = True

# تنظیمات مرورگر
PAGE_LOAD_TIMEOUT = 30
IMPLICIT_WAIT = 10
