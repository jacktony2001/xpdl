import time
import logging
import json # برای پردازش JSON
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import chromedriver_autoinstaller
import os # برای کار با فایل‌ها

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
            time.sleep(SCRAPER_CONFIG.get("wait_time", 7)) 
            
            self._scroll_to_load_more() 

            homepage_selectors = [
                "a.video-link",
                "a[href*='/video-']",
                "div.mozaique.cust-nb-cols a",
                "a.thumbnail"
            ]
            
            elements = self._find_elements(homepage_selectors)

            for el in elements:
                href = el.get_attribute("href")
                if href:
                    if not href.startswith(('http', 'https')):
                        href = WEBSITE_URL.rstrip('/') + href
                    if href not in video_page_links and ("/video-" in href or "/watch" in href):
                        video_page_links.append(href)

            if not video_page_links:
                logger.warning("⚠️ هیچ لینک صفحه‌ی ویدیویی در صفحه اصلی پیدا نشد!")
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
            time.sleep(SCRAPER_CONFIG.get("wait_time", 8)) # کمی بیشتر منتظر میمونیم

            # --- بخش ذخیره کد صفحه برای دیباگ ---
            try:
                page_source = self.driver.page_source
                # ایجاد نام فایل با حذف کاراکترهای نامعتبر از URL
                safe_url_part = "".join(c for c in video_page_url if c.isalnum() or c in ('-', '_')).rstrip()
                filename = f"page_dump_{safe_url_part[:50]}.html" # محدود کردن طول نام فایل
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(page_source)
                logger.info(f"✅ کد کامل صفحه در فایل '{filename}' ذخیره شد.")
            except Exception as e:
                logger.error(f"خطا در ذخیره کد صفحه: {e}")
            # --- پایان بخش ذخیره کد صفحه ---

            # --- بخش اول: تلاش برای پیدا کردن لینک دانلود با سلکتور دقیق شما ---
            primary_download_selector = "p.text-center.download-ready a"
            download_elements = self._find_elements([primary_download_selector])
            
            if download_elements:
                href = download_elements[0].get_attribute("href")
                # چک می‌کنیم که لینک mp4 باشه و واقعاً شروع میشه با mp4-cdn
                if href and href.endswith('.mp4') and "mp4-cdn" in href:
                    final_url = href
                    logger.info(f"✅ لینک دانلود ویدیو با سلکتور دقیق '{primary_download_selector}' پیدا شد: {final_url}")
                    return final_url
            
            if not final_url:
                logger.warning(f"⚠️ لینک دانلود با سلکتور دقیق '{primary_download_selector}' پیدا نشد (یا فرمت مناسب نداشت).")

            # --- بخش دوم: تلاش برای پیدا کردن لینک دانلود از JSON-LD (contentUrl) ---
            logger.info("در حال تلاش برای پیدا کردن لینک دانلود از JSON-LD (contentUrl)...")
            try:
                script_tag = self.driver.find_element(By.XPATH, "//script[@type='application/ld+json']")
                script_content = script_tag.get_attribute("innerHTML")
                
                data = json.loads(script_content)
                
                if data.get("@type") == "VideoObject" and "contentUrl" in data:
                    json_ld_url = data["contentUrl"]
                    if json_ld_url and json_ld_url.endswith('.mp4') and "mp4-cdn" in json_ld_url:
                        final_url = json_ld_url
                        logger.info(f"✅ لینک دانلود ویدیو از JSON-LD (contentUrl) پیدا شد: {final_url}")
                        return final_url
                else:
                    logger.warning("ساختار JSON-LD مورد انتظار نبود یا contentUrl پیدا نشد.")

            except NoSuchElementException:
                logger.warning("اسکریپت JSON-LD در صفحه پیدا نشد.")
            except json.JSONDecodeError:
                logger.warning("خطا در تجزیه محتوای JSON-LD.")
            except Exception as e:
                logger.warning(f"خطا در پردازش JSON-LD: {e}")

            # --- بخش سوم: اگر با روش‌های بالا پیدا نشد، از بک‌آپ عمومی استفاده کن ---
            if not final_url:
                logger.info("در حال امتحان روش‌های عمومی‌تر برای پیدا کردن لینک دانلود...")
                fallback_selectors = [
                    "a[href$='.mp4']",       
                    "video[src$='.mp4']",     
                    "a[download]",            
                    ".download-btn a",
                    "a[href*='mp4-cdn']" # اضافه کردن سلکتوری که مستقیم mp4-cdn رو چک کنه
                ]
                for selector in fallback_selectors:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in elements:
                        href = el.get_attribute("href")
                        if href and href.endswith('.mp4') and "mp4-cdn" in href:
                            final_url = href
                            logger.info(f"✅ لینک دانلود ویدیو از سلکتور fallback '{selector}' پیدا شد: {final_url}")
                            return final_url

            if not final_url:
                logger.warning(f"⚠️ هیچ لینک ویدیوی نهایی برای {video_page_url} با هیچ روشی پیدا نشد.")

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
        """متد اصلی برای شروع اسکرپ دو مرحله‌ای با محدودیت تعداد ویدیو"""
        all_final_video_urls = []
        homepage_links = self.get_video_page_links_from_homepage()

        if not homepage_links:
            logger.warning("هیچ لینک صفحه‌ی ویدیویی برای پردازش بیشتر یافت نشد.")
            return []

        max_videos_to_process = 10 
        
        links_to_process = homepage_links[:max_videos_to_process]
        
        logger.info(f"شروع پردازش {len(links_to_process)} لینک ویدیو از صفحه اصلی...")

        processed_count = 0
        for link in links_to_process:
            final_url = self.get_final_video_url(link)
            if final_url:
                all_final_video_urls.append(final_url)
            processed_count += 1
            if processed_count >= len(links_to_process): 
                break
        
        if not all_final_video_urls:
            logger.warning("⚠️ هیچ لینک ویدیوی نهایی استخراج نشد.")
        else:
            logger.info(f"✅ در مجموع {len(all_final_video_urls)} لینک ویدیوی نهایی استخراج شد.")
            
        return list(set(all_final_video_urls))

    def __del__(self):
        """پاکسازی درایور هنگام اتمام کار"""
        if self.driver:
            self.driver.quit()
            logger.info("🚪 درایور بسته شد")
