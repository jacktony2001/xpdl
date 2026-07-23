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

            # سلکتورهای صفحه اصلی
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
                    if href not in video_page_links:
                        video_page_links.append(href)

            if not video_page_links:
                logger.warning("⚠️ هیچ لینک ویدیویی در صفحه اصلی پیدا نشد!")
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
        """گرفتن لینک دانلود با اولویت لینک‌های پایدار (bkcdn)"""
        final_url = None
        all_mp4_links = []
        
        try:
            logger.info(f"🔄 در حال بررسی: {video_page_url}")
            self.driver.get(video_page_url)
            time.sleep(SCRAPER_CONFIG.get("wait_time", 8))

            # =======================================================
            # جمع‌آوری همه لینک‌های mp4 از روش‌های مختلف
            # =======================================================

            # ۱. لینک‌های از تگ video
            try:
                video_tags = self.driver.find_elements(By.TAG_NAME, "video")
                for v in video_tags:
                    src = v.get_attribute("src")
                    if src and ".mp4" in src:
                        all_mp4_links.append(src)
                        logger.debug(f"لینک از تگ video: {src}")
            except Exception:
                pass

            # ۲. لینک‌های از JSON-LD
            try:
                script_tag = self.driver.find_element(By.XPATH, "//script[@type='application/ld+json']")
                data = json.loads(script_tag.get_attribute("innerHTML"))
                
                if isinstance(data, list):
                    for item in data:
                        if item.get("@type") == "VideoObject" and "contentUrl" in item:
                            all_mp4_links.append(item["contentUrl"])
                            logger.debug(f"لینک از JSON-LD (list): {item['contentUrl']}")
                elif data.get("@type") == "VideoObject" and "contentUrl" in data:
                    all_mp4_links.append(data["contentUrl"])
                    logger.debug(f"لینک از JSON-LD: {data['contentUrl']}")
            except Exception:
                pass

            # ۳. لینک‌های از سلکتور مستقیم (p.text-center.download-ready a)
            try:
                download_paragraph = self.driver.find_element(By.CSS_SELECTOR, "p.text-center.download-ready")
                links = download_paragraph.find_elements(By.TAG_NAME, "a")
                for link in links:
                    href = link.get_attribute("href")
                    if href and ".mp4" in href:
                        all_mp4_links.append(href)
                        logger.debug(f"لینک از سلکتور مستقیم: {href}")
            except Exception:
                pass

            # ۴. لینک‌های از a[href$='.mp4']
            try:
                mp4_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href$='.mp4']")
                for link in mp4_links:
                    href = link.get_attribute("href")
                    if href:
                        all_mp4_links.append(href)
                        logger.debug(f"لینک از a[href$='.mp4']: {href}")
            except Exception:
                pass

            # =======================================================
            # اولویت‌بندی لینک‌ها
            # =======================================================

            # حذف موارد تکراری
            all_mp4_links = list(set(all_mp4_links))
            logger.info(f"🔍 {len(all_mp4_links)} لینک mp4 پیدا شد")

            # اولویت ۱: لینک‌های bkcdn (پایدارترین)
            for link in all_mp4_links:
                if "bkcdn" in link:
                    final_url = link
                    logger.info(f"✅ لینک پایدار (bkcdn) انتخاب شد: {final_url}")
                    return final_url

            # اولویت ۲: لینک‌های mp4-cdn یا gcore
            for link in all_mp4_links:
                if "mp4-cdn" in link or "gcore" in link:
                    final_url = link
                    logger.info(f"✅ لینک (mp4-cdn/gcore) انتخاب شد: {final_url}")
                    return final_url

            # اولویت ۳: هر لینک mp4 دیگه‌ای
            if all_mp4_links:
                final_url = all_mp4_links[0]
                logger.info(f"✅ لینک (fallback) انتخاب شد: {final_url}")
                return final_url

            logger.warning(f"⚠️ هیچ لینک دانلودی برای {video_page_url} پیدا نشد.")
            return None

        except Exception as e:
            logger.error(f"❌ خطا در پردازش {video_page_url}: {e}")
            return None

    def scrape(self):
        """متد اصلی اسکرپ"""
        all_final_video_urls = []
        homepage_links = self.get_video_page_links_from_homepage()

        if not homepage_links:
            logger.warning("هیچ لینک ویدیویی پیدا نشد.")
            return []

        max_videos_to_process = 10
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
