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

            # اولویت ۱: bkcdn (پایدار)
            for link in all_mp4_links:
                if "bkcdn" in link:
                    final_url = link
                    logger.info(f"✅ لینک پایدار (bkcdn) انتخاب شد")
                    return final_url

            # اولویت ۲: mp4-cdn یا gcore
            for link in all_mp4_links:
                if "mp4-cdn" in link or "gcore" in link:
                    final_url = link
                    logger.info(f"✅ لینک (mp4-cdn) انتخاب شد")
                    return final_url

            # اولویت ۳: هر لینک دیگه
            if all_mp4_links:
                final_url = all_mp4_links[0]
                logger.info(f"✅ لینک (fallback) انتخاب شد")
                return final_url

            logger.warning(f"⚠️ هیچ لینک دانلودی پیدا نشد.")
            return None

        except Exception as e:
            logger.error(f"❌ خطا: {e}")
            return None

    def _run_ffmpeg(self, input_file, output_file, crf, scale, audio_bitrate):
        """ساخت و اجرای دستور ffmpeg. همیشه از فایل ورودی داده‌شده می‌خونه."""
        preset = self.compression_config.get("preset", "fast")
        cmd = [
            "ffmpeg",
            "-y",
            "-i", input_file,
            "-vf", f"scale={scale}",
            "-c:v", "libx264",
            "-crf", str(crf),
            "-preset", preset,
            "-c:a", "aac",
            "-b:a", audio_bitrate,
            "-movflags", "+faststart",
            output_file
        ]
        logger.info(f"🎞 ffmpeg: crf={crf} scale={scale} audio={audio_bitrate}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"❌ خطا در ffmpeg: {result.stderr[-500:]}")
            return False
        return True

    def download_and_compress_video(self, video_url):
        """دانلود و فشرده‌سازی ویدیو با ffmpeg - نسخه اصلاح‌شده.

        رفع باگ: در نسخه قبلی فایل موقت دانلود (temp_file) قبل از حلقه
        retry پاک می‌شد، ولی دستور ffmpeg هنوز همون فایل رو به عنوان ورودی
        می‌خوند → تلاش‌های بعدی با خطای «فایل پیدا نشد» شکست می‌خوردن و حجم
        تغییر نمی‌کرد. حالا ورودی همیشه فایل اصلی دانلود شده‌ست و تا آخر نگه
        داشته می‌شه.
        """
        temp_file = "temp_video.mp4"
        output_path = "compressed_video.mp4"
        try:
            if not self.compression_config.get("enabled", True):
                logger.info("ℹ️ فشرده‌سازی غیرفعال است")
                return video_url

            logger.info(f"📥 دانلود ویدیو...")
            response = requests.get(video_url, stream=True, timeout=120)
            response.raise_for_status()
            with open(temp_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            original_size = os.path.getsize(temp_file) / (1024 * 1024)
            logger.info(f"📊 حجم اصلی: {original_size:.2f} MB")

            max_size = self.compression_config.get("max_size_mb", 48)

            # اگه حجم کمتر از حد مجازه، بدون فشرده‌سازی برگردون
            if original_size <= max_size:
                logger.info(f"ℹ️ حجم ویدیو کمتر از {max_size} MB است، نیازی به فشرده‌سازی نیست")
                os.remove(temp_file)
                return video_url

            # پاک کردن خروجی‌های قدیمی (اگه از اجرای قبلی مونده باشن)
            for f in (output_path, "compressed_retry_tmp.mp4"):
                if os.path.exists(f):
                    os.remove(f)

            scale = self.compression_config.get("scale", "480:320")
            crf = self.compression_config.get("crf", 35)
            audio_bitrate = self.compression_config.get("audio_bitrate", "48k")

            # فشرده‌سازی مرحله اول (از روی فایل اصلی دانلود‌شده)
            logger.info("🔄 در حال فشرده‌سازی ویدیو...")
            if not self._run_ffmpeg(temp_file, output_path, crf, scale, audio_bitrate):
                os.remove(temp_file)
                return video_url

            final_size = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"✅ فشرده‌سازی مرحله اول: {final_size:.2f} MB")

            # تلاش‌های بعدی: همیشه از فایل اصلی (temp_file) دوباره encode می‌کنیم
            # تا کیفیت تجمعی خراب نشه و ورودی همیشه وجود داشته باشه.
            retry_count = 0
            while final_size > max_size and retry_count < 4:
                retry_count += 1
                logger.info(f"🔄 تلاش {retry_count}: فشرده‌سازی مجدد با کیفیت پایین‌تر...")

                new_crf = crf + (retry_count * 4)
                new_width = max(320, 480 - (retry_count * 60))
                new_height = max(240, 320 - (retry_count * 40))
                new_audio = audio_bitrate
                if retry_count >= 2:
                    new_audio = f"{max(24, 48 - (retry_count * 8))}k"

                if not self._run_ffmpeg(
                    temp_file, output_path,
                    new_crf, f"{new_width}:{new_height}", new_audio
                ):
                    logger.error(f"❌ فشرده‌سازی تلاش {retry_count} شکست خورد.")
                    break

                final_size = os.path.getsize(output_path) / (1024 * 1024)
                logger.info(f"✅ حجم نهایی: {final_size:.2f} MB")

                if final_size <= max_size:
                    break

            # پاک کردن فایل دانلود‌شده اصلی
            if os.path.exists(temp_file):
                os.remove(temp_file)

            # اگه بازم بالاست، به عنوان لینک برگردون
            if final_size > max_size:
                logger.warning(f"⚠️ حجم بازم بالاست ({final_size:.2f} MB)، ارسال به صورت لینک")
                if os.path.exists(output_path):
                    os.remove(output_path)
                return video_url

            logger.info(f"✅ فشرده‌سازی موفق! حجم نهایی: {final_size:.2f} MB")
            return output_path

        except Exception as e:
            logger.error(f"❌ خطا در فشرده‌سازی: {e}")
            for f in (temp_file, output_path, "compressed_retry_tmp.mp4"):
                if os.path.exists(f):
                    os.remove(f)
            return video_url

    def scrape(self):
        """متد اصلی اسکرپ با فشرده‌سازی.

        خروجی: لیستی از دیکشنری‌ها با کلیدهای
        page_url, result, is_file, title
        (برای dedup درست در main.py از page_url استفاده می‌شه).
        """
        all_items = []
        homepage_links = self.get_video_page_links_from_homepage()

        if not homepage_links:
            logger.warning("هیچ لینک ویدیویی پیدا نشد.")
            return []

        max_videos_to_process = 3
        links_to_process = homepage_links[:max_videos_to_process]
        logger.info(f"پردازش {len(links_to_process)} ویدیو...")

        for link in links_to_process:
            try:
                video_url = self.get_final_video_url(link)
                if not video_url:
                    continue

                result = self.download_and_compress_video(video_url)
                is_file = bool(result and result.endswith('.mp4') and os.path.exists(result))

                entry = {
                    "page_url": link,
                    "source_url": video_url,
                    "result": result,
                    "is_file": is_file,
                    "title": ""
                }
                all_items.append(entry)
            except Exception as e:
                logger.error(f"❌ خطا در پردازش {link}: {e}")
                continue

        if not all_items:
            logger.warning("⚠️ هیچ ویدیویی استخراج نشد.")
        else:
            logger.info(f"✅ {len(all_items)} ویدیو آماده ارسال شد.")

        return all_items

    def __del__(self):
        if self.driver:
            self.driver.quit()
            logger.info("🚪 درایور بسته شد")
