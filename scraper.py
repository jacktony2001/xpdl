import time
import logging
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
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
        """راه‌اندازی درایور کروم"""
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
        """پیدا کردن المان‌ها با لیست سلکتورها"""
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    return elements
            except Exception:
                continue
        return []

    def _scroll_to_load_more(self):
        """اسکرول صفحه برای بارگذاری بیشتر"""
        scroll_times = SCRAPER_CONFIG.get("scroll_pages", 0)
        if scroll_times > 0:
            logger.info(f"📜 اسکرول {scroll_times} بار برای بارگذاری بیشتر...")
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            for _ in range(scroll_times):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(SCRAPER_CONFIG.get("wait_time", 3))
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

    def get_video_page_links_from_homepage(self):
        """گرفتن لینک صفحه ویدیوها از صفحه اصلی"""
        video_page_links = []
        try:
            logger.info(f"🔄 در حال اتصال به صفحه اصلی: {WEBSITE_URL}")
            self.driver.get(WEBSITE_URL)
            time.sleep(SCRAPER_CONFIG.get("wait_time", 7))
            
            self._scroll_to_load_more()

            # ========== اینجا سلکتور صفحه اصلی رو عوض کن ==========
            homepage_selectors = [
                "a.video-link",
                "a[href*='/video-']",
                "div.mozaique.cust-nb-cols a",
                "a.thumbnail",
                # سلکتور جدید رو اینجا اضافه کن
            ]
            # =====================================================

            elements = self._find_elements(homepage_selectors)

            for el in elements:
                href = el.get_attribute("href")
                if href:
                    if not href.startswith(('http', 'https')):
                        href = WEBSITE_URL.rstrip('/') + href
                    if href not in video_page_links:
                        video_page_links.append(href)

            if not video_page_links:
                logger.warning("⚠️ هیچ لینک ویدیویی در صفحه اصلی پیدا نشد!")
                # نمایش چند لینک نمونه برای دیباگ
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                sample = [a.get_attribute("href") for a in all_links[:5] if a.get_attribute("href")]
                logger.info(f"📋 نمونه لینک‌های صفحه: {sample}")
            else:
                logger.info(f"✅ {len(video_page_links)} لینک صفحه ویدیو پیدا شد.")

            return video_page_links

        except Exception as e:
            logger.error(f"❌ خطا: {e}")
            return []

    def get_final_video_url(self, video_page_url):
        """گرفتن لینک دانلود از صفحه اختصاصی ویدیو"""
        final_url = None
        try:
            logger.info(f"🔄 در حال بررسی: {video_page_url}")
            self.driver.get(video_page_url)
            time.sleep(SCRAPER_CONFIG.get("wait_time", 8))

            # ========== سلکتور دانلود (همون چیزی که خودت دیدی) ==========
            # اگه سایتت تغییر کرد، اینجا رو عوض کن
            primary_download_selector = "p.text-center.download-ready a"
            # ===========================================================

            # روش اول: سلکتور دقیق
            try:
                download_paragraph = self.driver.find_element(By.CSS_SELECTOR, "p.text-center.download-ready")
                links = download_paragraph.find_elements(By.TAG_NAME, "a")
                for link in links:
                    href = link.get_attribute("href")
                    if href and ".mp4" in href:
                        final_url = href
                        logger.info(f"✅ لینک دانلود پیدا شد: {final_url}")
                        return final_url
            except NoSuchElementException:
                logger.info("سلکتور دقیق پیدا نشد، روش‌های دیگه رو امتحان می‌کنم...")

            # روش دوم: تگ video
            if not final_url:
                try:
                    video_tags = self.driver.find_elements(By.TAG_NAME, "video")
                    for v in video_tags:
                        src = v.get_attribute("src")
                        if src and ".mp4" in src:
                            final_url = src
                            logger.info(f"✅ لینک از تگ video پیدا شد: {final_url}")
                            return final_url
                except Exception:
                    pass

            # روش سوم: لینک‌های مستقیم mp4
            if not final_url:
                try:
                    mp4_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href$='.mp4']")
                    for link in mp4_links:
                        href = link.get_attribute("href")
                        if href:
                            final_url = href
                            logger.info(f"✅ لینک از a[href$='.mp4'] پیدا شد: {final_url}")
                            return final_url
                except Exception:
                    pass

            # روش چهارم: دکمه دانلود
            if not final_url:
                try:
                    download_btns = self.driver.find_elements(By.CSS_SELECTOR, ".download-btn, a[download], .download")
                    for btn in download_btns:
                        href = btn.get_attribute("href")
                        if href and ".mp4" in href:
                            final_url = href
                            logger.info(f"✅ لینک از دکمه دانلود پیدا شد: {final_url}")
                            return final_url
                except Exception:
                    pass

            # روش پنجم: JSON-LD
            if not final_url:
                try:
                    script_tag = self.driver.find_element(By.XPATH, "//script[@type='application/ld+json']")
                    data = json.loads(script_tag.get_attribute("innerHTML"))
                    if isinstance(data, list):
                        for item in data:
                            if item.get("@type") == "VideoObject" and "contentUrl" in item:
                                final_url = item["contentUrl"]
                                logger.info(f"✅ لینک از JSON-LD پیدا شد: {final_url}")
                                return final_url
                    elif data.get("@type") == "VideoObject" and "contentUrl" in data:
                        final_url = data["contentUrl"]
                        logger.info(f"✅ لینک از JSON-LD پیدا شد: {final_url}")
                        return final_url
                except Exception:
                    pass

            if not final_url:
                logger.warning(f"⚠️ هیچ لینک دانلودی برای {video_page_url} پیدا نشد.")

            return final_url

        except Exception as e:
            logger.error(f"❌ خطا: {e}")
            return None

    def scrape(self):
        """متد اصلی اسکرپ"""
        all_final_video_urls = []
        homepage_links = self.get_video_page_links_from_homepage()

        if not homepage_links:
            logger.warning("هیچ لینک ویدیویی پیدا نشد.")
            return []

        # ========== تعداد ویدیو (اگه میخوای همه رو بگیری بذار 999) ==========
        max_videos_to_process = 10
        # ==================================================================

        links_to_process = homepage_links[:max_videos_to_process]
        logger.info(f"پردازش {len(links_to_process)} ویدیو...")

        for link in links_to_process:
            final_url = self.get_final_video_url(link)
            if final_url:
                all_final_video_urls.append(final_url)

        if not all_final_video_urls:
            logger.warning("⚠️ هیچ لینک نهایی استخراج نشد.")
        else:
            logger.info(f"✅ {len(all_final_video_urls)} لینک نهایی استخراج شد.")

        return list(set(all_final_video_urls))

    def __del__(self):
        if self.driver:
            self.driver.quit()
            logger.info("🚪 درایور بسته شد")
