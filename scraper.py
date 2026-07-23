import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
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

    def get_video_page_links_from_homepage(self):
        """گرفتن لینک صفحه‌ی هر ویدیو از صفحه اصلی سایت"""
        video_page_links = []
        try:
            logger.info(f"🔄 در حال اتصال به صفحه اصلی: {WEBSITE_URL}")
            self.driver.get(WEBSITE_URL)
            time.sleep(SCRAPER_CONFIG.get("wait_time", 5))
            
            self._scroll_to_load_more() # اسکرول برای بارگذاری بیشتر

            # سلکتورهای رایج برای پیدا کردن لینک صفحه ویدیوها در صفحه اصلی
            # این سلکتورها باید بر اساس ساختار سایت شما تنظیم بشن
            homepage_selectors = [
                "a[href*='/watch']",  # لینک‌هایی که "/watch" دارن
                "a[href*='/video/']", # لینک‌هایی که "/video/" دارن
                "div.video-card a",    # لینک داخل div با کلاس video-card
                "a.thumbnail-link",   # لینک با کلاس thumbnail-link
                ".video-item a"        # لینک داخل div با کلاس video-item
            ]
            
            elements = self._find_elements(homepage_selectors)

            for el in elements:
                href = el.get_attribute("href")
                if href:
                    # اگر لینک نسبی بود، به لینک کامل تبدیل کن
                    if not href.startswith(('http', 'https')):
                        href = WEBSITE_URL.rstrip('/') + href
                    
                    # جلوگیری از تکرار و لینک‌های نامرتبط
                    if href not in video_page_links and ("/watch" in href or "/video/" in href):
                        video_page_links.append(href)

            if not video_page_links:
                logger.warning("⚠️ هیچ لینک صفحه‌ی ویدیویی در صفحه اصلی پیدا نشد!")
                # لاگ کردن بخشی از کد صفحه برای دیباگ
                # logger.info(f"ساختار صفحه اصلی: {self.driver.page_source[:500]}...") 
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
        """گرفتن لینک نهایی دانلود ویدیو از صفحه اختصاصی هر ویدیو"""
        final_url = None
        try:
            logger.info(f"🔄 در حال ورود به صفحه ویدیو: {video_page_url}")
            self.driver.get(video_page_url)
            time.sleep(SCRAPER_CONFIG.get("wait_time", 4))

            # اینجا سلکتورهایی که گفتی رو وارد می‌کنیم:
            # <p class="text-center download-ready">Download : <a href="...mp4"><strong>STANDARD</strong></a> file size.</p>
            
            # اول تگ <p> با کلاس download-ready رو پیدا می‌کنیم
            download_paragraph = self._find_elements(["p.text-center.download-ready"])
            
            if download_paragraph:
                # بعد توی اون پاراگراف، تگ <a> رو پیدا می‌کنیم
                link_element = download_paragraph[0].find_elements(By.TAG_NAME, "a")
                if link_element:
                    href = link_element[0].get_attribute("href")
                    if href and href.endswith('.mp4'):
                        final_url = href
                        logger.info(f"✅ لینک دانلود ویدیو از صفحه اختصاصی پیدا شد: {final_url}")
                        return final_url

            # اگر با روش بالا پیدا نشد، می‌تونیم یه بک‌آپ داشته باشیم
            # مثلاً دنبال لینک‌های mp4 در کل صفحه بگردیم (البته اولویت با روش بالا هست)
            if not final_url:
                logger.warning(f"⚠️ لینک دانلود مستقیم از صفحه {video_page_url} با روش اول پیدا نشد. در حال امتحان روش‌های عمومی‌تر...")
                fallback_selectors = [
                    "a[href$='.mp4']",
                    "video[src$='.mp4']",
                    "a[download]",
                    ".download-btn a"
                ]
                for selector in fallback_selectors:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in elements:
                        href = el.get_attribute("href")
                        if href and href.endswith('.mp4'):
                            final_url = href
                            logger.info(f"✅ لینک دانلود ویدیو از سلکتور fallback '{selector}' پیدا شد: {final_url}")
                            return final_url

            if not final_url:
                logger.warning(f"⚠️ لینک ویدیوی نهایی برای {video_page_url} پیدا نشد.")
                # لاگ کردن بخشی از کد صفحه برای دیباگ
                # logger.info(f"ساختار صفحه ویدیو: {self.driver.page_source[:500]}...")

            return final_url

        except TimeoutException:
            logger.error(f"❌ زمان بارگذاری صفحه ویدیو {video_page_url} به اتمام رسید")
            return None
        except ElementClickInterceptedException:
            logger.error(f"❌ امکان کلیک روی المان در {video_page_url} وجود ندارد (ممکن است پاپ‌آپ یا مانعی وجود داشته باشد).")
            return None
        except Exception as e:
            logger.error(f"❌ خطا در گرفتن لینک نهایی ویدیو از {video_page_url}: {e}")
            return None

    def scrape(self):
        """متد اصلی برای شروع اسکرپ دو مرحله‌ای"""
        all_final_video_urls = []
        homepage_links = self.get_video_page_links_from_homepage()

        if not homepage_links:
            logger.warning("هیچ لینک صفحه‌ی ویدیویی برای پردازش بیشتر یافت نشد.")
            return []

        processed_links = 0
        for link in homepage_links:
            # محدود کردن تعداد ویدیوها برای تست سریع
            if processed_links >= SCRAPER_CONFIG.get("max_videos_to_process", 10): # مثلاً حداکثر ۱۰ ویدیو رو پردازش کن
                logger.info(f"Reached max videos to process ({SCRAPER_CONFIG.get('max_videos_to_process', 10)}). Stopping.")
                break
                
            final_url = self.get_final_video_url(link)
            if final_url:
                all_final_video_urls.append(final_url)
            processed_links += 1
        
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

