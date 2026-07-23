import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import chromedriver_autoinstaller

from config import WEBSITE_URL, CHROME_OPTIONS, SCRAPER_CONFIG

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
            chromedriver_autoinstaller.install()
            options = Options()
            for arg in CHROME_OPTIONS:
                options.add_argument(arg)
            self.driver = webdriver.Chrome(options=options)
            logger.info("✅ درایور کروم با موفقیت راه‌اندازی شد")
        except Exception as e:
            logger.error(f"❌ خطا در راه‌اندازی کروم: {e}")
            raise

    def _find_elements(self, selectors):
        """پیدا کردن المان‌ها با استفاده از لیست سلکتورها"""
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    return elements
            except Exception as e:
                logger.debug(f"سلکتور {selector} کار نکرد: {e}")
        return []

    def _scroll_to_load_more(self):
        """اسکرول کردن صفحه برای بارگذاری محتوای بیشتر"""
        scroll_times = SCRAPER_CONFIG.get("scroll_pages", 0)
        if scroll_times > 0:
            logger.info(f"Scrolling down {scroll_times} times to load more content...")
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            for _ in range(scroll_times):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(SCRAPER_CONFIG.get("wait_time", 3))
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    logger.info("No more content loaded after scrolling.")
                    break
                last_height = new_height
                logger.info("Scrolled down, loading more...")

    def get_video_links_from_homepage(self):
        """گرفتن لینک ویدیوها از صفحه اصلی سایت"""
        video_page_links = []
        try:
            logger.info(f"🔄 در حال اتصال به صفحه اصلی: {WEBSITE_URL}")
            self.driver.get(WEBSITE_URL)
            time.sleep(SCRAPER_CONFIG.get("wait_time", 5))
            
            self._scroll_to_load_more() # اسکرول برای بارگذاری بیشتر

            # اینجا سلکتورهای مربوط به لینک هر ویدیو در صفحه اصلی رو پیدا کن
            # مثال: اگر لینک‌ها توی تگ <a> با کلاس 'video-link' هستن
            # این قسمت باید بر اساس سایت شما تنظیم بشه
            # برای شروع، از چند سلکتور رایج استفاده می‌کنیم
            homepage_selectors = [
                "a.video-link",
                "a.video-title",
                ".video-card a",
                ".thumbnail a",
                "a[href*='/watch']", # لینک‌هایی که "/watch" دارن
                "a[href*='/video/']" # لینک‌هایی که "/video/" دارن
            ]
            
            elements = self._find_elements(homepage_selectors)

            for el in elements:
                href = el.get_attribute("href")
                if href:
                    # اطمینان از اینکه لینک نسبی به آدرس سایت تبدیل بشه
                    if href.startswith('/'):
                        href = WEBSITE_URL.rstrip('/') + href
                    if href not in video_page_links:
                        video_page_links.append(href)

            if not video_page_links:
                logger.warning("⚠️ هیچ لینک ویدیویی در صفحه اصلی پیدا نشد!")
                logger.info(f"ساختار صفحه اصلی: {self.driver.page_source[:500]}...") # نمایش بخشی از کد صفحه برای دیباگ
            else:
                logger.info(f"✅ {len(video_page_links)} لینک صفحه ویدیو از صفحه اصلی پیدا شد.")
            
            return video_page_links

        except TimeoutException:
            logger.error("❌ زمان بارگذاری صفحه اصلی به اتمام رسید")
            return []
        except Exception as e:
            logger.error(f"❌ خطا در گرفتن لینک‌های صفحه اصلی: {e}")
            return []

    def get_final_video_url(self, video_page_url):
        """گرفتن لینک نهایی ویدیو از صفحه اختصاصی هر ویدیو"""
        final_url = None
        try:
            logger.info(f"🔄 در حال ورود به صفحه ویدیو: {video_page_url}")
            self.driver.get(video_page_url)
            time.sleep(SCRAPER_CONFIG.get("wait_time", 4))

            # اینجا سلکتورهایی رو باید تست کنیم که لینک دانلود یا پخش مستقیم ویدیو رو میدن
            # این بخش باید بر اساس ساختار صفحه ویدیوی سایت شما تنظیم بشه
            video_selectors = SCRAPER_CONFIG.get("video_selectors", [])
            
            # اول تگ <video> رو چک می‌کنیم
            video_tags = self.driver.find_elements(By.TAG_NAME, "video")
            for v in video_tags:
                src = v.get_attribute("src")
                if src and (src.endswith('.mp4') or src.endswith('.webm')):
                    final_url = src
                    logger.info(f"✅ لینک ویدیو از تگ <video> پیدا شد: {final_url}")
                    return final_url

            # اگر با تگ video پیدا نشد، از سلکتورهای دیگه استفاده می‌کنیم
            for selector in video_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    if selector.startswith("a[href"): # اگه تگ 'a' با href بود
                        href = el.get_attribute("href")
                        if href and (href.endswith('.mp4') or href.endswith('.webm')):
                            final_url = href
                            logger.info(f"✅ لینک ویدیو از سلکتور '{selector}' پیدا شد: {final_url}")
                            return final_url
                    elif selector.startswith(".download"): # اگه دکمه دانلود بود
                        href = el.get_attribute("href")
                        if href and (href.endswith('.mp4') or href.endswith('.webm')):
                            final_url = href
                            logger.info(f"✅ لینک ویدیو از دکمه دانلود '{selector}' پیدا شد: {final_url}")
                            return final_url
                    # برای موارد دیگه، باید منطق اضافه بشه (مثلاً استخراج src از attributes دیگه)

            if not final_url:
                logger.warning(f"⚠️ لینک ویدیوی نهایی برای {video_page_url} پیدا نشد.")
                # لاگ کردن بخشی از کد صفحه برای دیباگ
                logger.info(f"ساختار صفحه ویدیو: {self.driver.page_source[:500]}...")

            return final_url

        except TimeoutException:
            logger.error(f"❌ زمان بارگذاری صفحه ویدیو {video_page_url} به اتمام رسید")
            return None
        except Exception as e:
            logger.error(f"❌ خطا در گرفتن لینک نهایی ویدیو از {video_page_url}: {e}")
            return None

    def scrape(self):
        """متد اصلی برای شروع اسکرپ دو مرحله‌ای"""
        all_final_video_urls = []
        homepage_links = self.get_video_links_from_homepage()

        if not homepage_links:
            logger.warning("هیچ لینک ویدیویی برای پردازش بیشتر یافت نشد.")
            return []

        for link in homepage_links:
            final_url = self.get_final_video_url(link)
            if final_url:
                all_final_video_urls.append(final_url)
        
        if not all_final_video_urls:
            logger.warning("⚠️ هیچ لینک ویدیوی نهایی استخراج نشد.")
        else:
            logger.info(f"✅ در مجموع {len(all_final_video_urls)} لینک ویدیوی نهایی استخراج شد.")
            
        return list(set(all_final_video_urls)) # حذف موارد تکراری

    def __del__(self):
        """پاکسازی درایور هنگام اتمام کار"""
        if self.driver:
            self.driver.quit()
            logger.info("🚪 درایور بسته شد")

