import time
import logging
import json
import subprocess
import requests
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import chromedriver_autoinstaller

from config import WEBSITE_URL, CHROME_OPTIONS, SCRAPER_CONFIG

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VideoScraper:
    def __init__(self):
        self.driver = None
        self.setup_driver()
        self.compression_config = SCRAPER_CONFIG.get("compression", {})

    def setup_driver(self):
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
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    return elements
            except Exception:
                continue
        return []

    def _scroll_to_load_more(self):
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
                    if href not in video_page_links:
                        video_page_links.append(href)

            if not video_page_links:
                logger.warning("⚠️ هیچ لینک ویدیویی در صفحه اصلی پیدا نشد!")
            else:
                logger.info(f"✅ {len(video_page_links)} لینک صفحه ویدیو پیدا شد.")

            return video_page_links

        except Exception as e:
            logger.error(f"❌ خطا: {e}")
            return []

    def get_final_video_url(self, video_page_url):
        """گرفتن لینک دانلود - فقط mp4-cdn یا gcore"""
        final_url = None
        all_mp4_links = []
        
        try:
            logger.info(f"🔄 در حال بررسی: {video_page_url}")
            self.driver.get(video_page_url)
            time.sleep(SCRAPER_CONFIG.get("wait_time", 8))

            # ۱. لینک‌های از تگ video
            try:
                video_tags = self.driver.find_elements(By.TAG_NAME, "video")
                for v in video_tags:
                    src = v.get_attribute("src")
                    if src and ".mp4" in src:
                        all_mp4_links.append(src)
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
                elif data.get("@type") == "VideoObject" and "contentUrl" in data:
                    all_mp4_links.append(data["contentUrl"])
            except Exception:
                pass

            # ۳. لینک‌های از سلکتور مستقیم
            try:
                download_paragraph = self.driver.find_element(By.CSS_SELECTOR, "p.text-center.download-ready")
                links = download_paragraph.find_elements(By.TAG_NAME, "a")
                for link in links:
                    href = link.get_attribute("href")
                    if href and ".mp4" in href:
                        all_mp4_links.append(href)
            except Exception:
                pass

            # ۴. لینک‌های از a[href$='.mp4']
            try:
                mp4_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href$='.mp4']")
                for link in mp4_links:
                    href = link.get_attribute("href")
                    if href:
                        all_mp4_links.append(href)
            except Exception:
                pass

            all_mp4_links = list(set(all_mp4_links))
            logger.info(f"🔍 {len(all_mp4_links)} لینک mp4 پیدا شد")

            # =====================================================
            # فقط لینک‌های mp4-cdn یا gcore رو قبول کن
            # =====================================================
            
            # اولویت ۱: mp4-cdn یا gcore
            for link in all_mp4_links:
                if "mp4-cdn" in link or "gcore" in link:
                    final_url = link
                    logger.info(f"✅ لینک (mp4-cdn/gcore) انتخاب شد")
                    return final_url

            # رد کردن bkcdn (تبلیغاتی)
            for link in all_mp4_links:
                if "bkcdn" in link:
                    logger.info(f"⏭️ لینک bkcdn رد شد (تبلیغاتی)")
                    continue

            # اگه هیچکدوم نبود
            if not final_url:
                logger.warning(f"⚠️ هیچ لینک mp4-cdn یا gcore پیدا نشد، ویدیو رد شد.")
                return None

            return final_url

        except Exception as e:
            logger.error(f"❌ خطا: {e}")
            return None

    def download_and_compress_video(self, video_url):
        """دانلود و فشرده‌سازی ویدیو با ffmpeg"""
        try:
            if not self.compression_config.get("enabled", True):
                logger.info("ℹ️ فشرده‌سازی غیرفعال است")
                return video_url

            logger.info(f"📥 دانلود ویدیو...")
            response = requests.get(video_url, stream=True, timeout=120)
            temp_file = "temp_video.mp4"
            
            with open(temp_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            original_size = os.path.getsize(temp_file) / (1024 * 1024)
            logger.info(f"📊 حجم اصلی: {original_size:.2f} MB")

            max_size = self.compression_config.get("max_size_mb", 48)
            
            if original_size <= max_size:
                logger.info(f"ℹ️ حجم ویدیو کمتر از {max_size} MB است، نیازی به فشرده‌سازی نیست")
                os.remove(temp_file)
                return video_url

            logger.info("🔄 در حال فشرده‌سازی ویدیو...")
            output_path = "compressed_video.mp4"
            
            scale = self.compression_config.get("scale", "480:320")
            crf = self.compression_config.get("crf", 35)
            audio_bitrate = self.compression_config.get("audio_bitrate", "48k")
            preset = self.compression_config.get("preset", "fast")
            
            cmd = [
                "ffmpeg",
                "-i", temp_file,
                "-vf", f"scale={scale}",
                "-c:v", "libx264",
                "-crf", str(crf),
                "-preset", preset,
                "-c:a", "aac",
                "-b:a", audio_bitrate,
                "-movflags", "+faststart",
                "-y",
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"❌ خطا در ffmpeg: {result.stderr}")
                os.remove(temp_file)
                return video_url

            os.remove(temp_file)
            
            final_size = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"✅ فشرده‌سازی مرحله اول: {final_size:.2f} MB")
            
            retry_count = 0
            while final_size > max_size and retry_count < 4:
                retry_count += 1
                logger.info(f"🔄 تلاش {retry_count}: فشرده‌سازی مجدد با کیفیت پایین‌تر...")
                
                new_crf = crf + (retry_count * 4)
                new_width = max(320, 480 - (retry_count * 60))
                new_height = max(240, 320 - (retry_count * 40))
                
                cmd[cmd.index("-crf") + 1] = str(new_crf)
                cmd[cmd.index("-vf") + 1] = f"scale={new_width}:{new_height}"
                
                if retry_count >= 2:
                    new_audio_bitrate = f"{max(24, 48 - (retry_count * 8))}k"
                    cmd[cmd.index("-b:a") + 1] = new_audio_bitrate
                
                subprocess.run(cmd, capture_output=True, text=True)
                final_size = os.path.getsize(output_path) / (1024 * 1024)
                logger.info(f"✅ حجم نهایی: {final_size:.2f} MB")
                
                if final_size <= max_size:
                    break

            if final_size > max_size:
                logger.warning(f"⚠️ حجم بازم بالاست ({final_size:.2f} MB)، ارسال به صورت لینک")
                os.remove(output_path)
                return video_url

            logger.info(f"✅ فشرده‌سازی موفق! حجم نهایی: {final_size:.2f} MB")
            return output_path

        except Exception as e:
            logger.error(f"❌ خطا در فشرده‌سازی: {e}")
            if os.path.exists("temp_video.mp4"):
                os.remove("temp_video.mp4")
            return video_url

    def scrape(self):
        """متد اصلی اسکرپ"""
        all_video_paths = []
        homepage_links = self.get_video_page_links_from_homepage()

        if not homepage_links:
            logger.warning("هیچ لینک ویدیویی پیدا نشد.")
            return []

        max_videos_to_process = 6
        links_to_process = homepage_links[:max_videos_to_process]
        logger.info(f"پردازش {len(links_to_process)} ویدیو...")

        for link in links_to_process:
            video_url = self.get_final_video_url(link)
            if video_url:
                result = self.download_and_compress_video(video_url)
                if result and result.endswith('.mp4') and os.path.exists(result):
                    all_video_paths.append(result)
                else:
                    all_video_paths.append(video_url)
            else:
                logger.info(f"⏭️ ویدیو رد شد (لینک مناسب پیدا نشد)")

        if not all_video_paths:
            logger.warning("⚠️ هیچ ویدیویی استخراج نشد.")
        else:
            logger.info(f"✅ {len(all_video_paths)} ویدیو آماده ارسال شد.")

        return all_video_paths

    def __del__(self):
        if self.driver:
            self.driver.quit()
            logger.info("🚪 درایور بسته شد")
