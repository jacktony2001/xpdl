import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import chromedriver_autoinstaller

from config import WEBSITE_URL, CHROME_OPTIONS

# تنظیم لاگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VideoScraper:
    def __init__(self):
        self.driver = None
        self.setup_driver()

    def setup_driver(self):
        """راه‌اندازی درایور کروم با تنظیمات مخصوص گیتهاب"""
        try:
            # نصب خودکار کروم‌درایور متناسب با سیستم
            chromedriver_autoinstaller.install()
            
            options = Options()
            for arg in CHROME_OPTIONS:
                options.add_argument(arg)
            
            # برای گیتهاب اکشن، از سرویس پیش‌فرض استفاده میکنیم
            self.driver = webdriver.Chrome(options=options)
            logger.info("✅ درایور کروم با موفقیت راه‌اندازی شد")
        except Exception as e:
            logger.error(f"❌ خطا در راه‌اندازی کروم: {e}")
            raise

    def get_video_links(self):
        """گرفتن لینک ویدیوها از سایت"""
        video_links = []
        try:
            logger.info(f"🔄 در حال اتصال به {WEBSITE_URL}")
            self.driver.get(WEBSITE_URL)
            time.sleep(3)  # منتظر بارگذاری اولیه
            
            # اینجا باید المنت‌های ویدیو رو پیدا کنی - بسته به ساختار سایت
            # مثال: پیدا کردن همه تگ‌های ویدیو یا لینک‌های دانلود
            # فعلاً یه نمونه ساده:
            elements = self.driver.find_elements(By.TAG_NAME, "a")
            for el in elements:
                href = el.get_attribute("href")
                if href and (".mp4" in href or "/video/" in href or "watch" in href):
                    video_links.append(href)
            
            # اگه هیچی پیدا نشد، خطا بده
            if not video_links:
                logger.warning("⚠️ هیچ ویدیویی پیدا نشد! شاید ساختار سایت عوض شده.")
                # اینجا می‌تونی از روش‌های جایگزین استفاده کنی
                
            logger.info(f"✅ {len(video_links)} ویدیو پیدا شد")
            return list(set(video_links))  # حذف موارد تکراری
            
        except TimeoutException:
            logger.error("❌ زمان بارگذاری سایت به اتمام رسید")
            return []
        except Exception as e:
            logger.error(f"❌ خطا در اسکرپ کردن: {e}")
            return []
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("🚪 درایور بسته شد")

    def scrape(self):
        """متد اصلی برای شروع اسکرپ"""
        return self.get_video_links()
