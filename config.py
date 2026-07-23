# config.py

# آدرس صفحه اصلی سایت
WEBSITE_URL = "https://www.xnxx.com" # مثال: آدرس سایت شما

# تنظیمات کروم
CHROME_OPTIONS = [
    "--headless",           # اجرای مرورگر در پس‌زمینه (بدون رابط گرافیکی)
    "--no-sandbox",         # برای اجرا در محیط‌های محدود (مثل Docker یا سرورها)
    "--disable-dev-shm-usage", # برای جلوگیری از خطای مربوط به حافظه اشتراکی
    "--disable-gpu",        # غیرفعال کردن شتاب‌دهنده گرافیکی
    "--window-size=1920,1080", # تنظیم اندازه پنجره مرورگر (برای Headless mode مهم است)
    "--disable-extensions", # غیرفعال کردن افزونه‌ها
    "--log-level=3",        # سطح لاگ مرورگر (3 یعنی فقط خطاها)
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36", # تنظیم User-Agent
]

# تنظیمات اسکرپر
SCRAPER_CONFIG = {
    # زمان انتظار بر حسب ثانیه برای بارگذاری کامل صفحات
    "wait_time_homepage": 7,           # زمان انتظار برای صفحه اصلی
    "wait_time_video_page": 15,          # زمان انتظار برای صفحه هر ویدیو (افزایش داده شده)
    "wait_time_scroll": 3,             # زمان انتظار بین هر بار اسکرول صفحه
    "extra_wait_for_download_content": 5, # انتظار اضافی بعد از لود صفحه ویدیو برای محتوای دانلود
    
    # تعداد ویدیوهایی که در هر بار اجرای اسکریپت پردازش می‌شوند
    "max_videos_per_run": 10,
    
    # تعداد دفعات اسکرول صفحه اصلی برای بارگذاری محتوای بیشتر
    "scroll_pages": 2,
}

