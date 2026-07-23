import os

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', 'YOUR_CHAT_ID')
BASE_URL = "https://www.xnxx.com/search/sexy"

SELECTORS = {
    'video_links': 'div.thumb a, a[href*="/video-"]',
    'title': 'h1.page-title, h1.title, h1',
    'video': 'video',
    'duration': 'span.duration, .video-duration',
}

EXCLUDE_PATTERNS = ['ad', 'sponsored', 'promo', 'advertisement']
MAX_FILE_SIZE_MB = 50
MAX_VIDEOS_PER_RUN = 5
HEADLESS = True
