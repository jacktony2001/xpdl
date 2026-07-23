# scraper.py
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import re
import json
from bs4 import BeautifulSoup

class ContentScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """تنظیمات Chrome Driver با undetected-chromedriver"""
        options = uc.ChromeOptions()
        
        if self.headless:
            options.add_argument("--headless=new")
        
        # تنظیمات ضروری
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # User-Agent واقعی
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # ایجاد driver
        self.driver = uc.Chrome(options=options, version_main=None)
        self.driver.set_page_load_timeout(30)
        
        # پنهان کردن webdriver
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def get_video_links(self, url, selectors):
        """دریافت لینک‌های ویدیو از صفحه لیست"""
        try:
            print(f"Loading page: {url}")
            self.driver.get(url)
            
            # منتظر لود شدن تامبنیل‌ها
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.thumb, div.video-item, a[href*='/video-']"))
            )
            
            time.sleep(3)  # زمان اضافی برای لود کامل
            
            # اسکرول برای لود محتوای lazy
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # پیدا کردن لینک‌ها
            video_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.thumb a, a[href*='/video-']")
            
            links = []
            for elem in video_elements:
                try:
                    href = elem.get_attribute('href')
                    if href and '/video-' in href and 'xnxx.com' in href:
                        # حذف پارامترهای اضافی
                        clean_url = href.split('?')[0]
                        if clean_url not in links:
                            links.append(clean_url)
                except:
                    continue
            
            print(f"Found {len(links)} unique video links")
            return links
            
        except Exception as e:
            print(f"Error getting links: {e}")
            return []
    
    def extract_video_from_html(self, page_source):
        """استخراج URL ویدیو از سورس HTML با روش‌های مختلف"""
        video_url = None
        
        # روش ۱: جستجو در JSON داخل script tags
        try:
            # XNXX معمولاً ویدیو را در متغیرهای جاوااسکریپت ذخیره می‌کند
            patterns = [
                r'"url":"(https?://[^"]+\.mp4[^"]*)"',
                r'"videoUrl":"(https?://[^"]+\.mp4[^"]*)"',
                r'"contentUrl":"(https?://[^"]+\.mp4[^"]*)"',
                r'"src":"(https?://[^"]+\.mp4[^"]*)"',
                r'html5player\.setVideoUrlHigh\([\'"]([^\'"]+)[\'"]\)',
                r'html5player\.setVideoUrlLow\([\'"]([^\'"]+)[\'"]\)',
                r'setVideoUrlHigh\([\'"]([^\'"]+)[\'"]\)',
                r'setVideoUrlLow\([\'"]([^\'"]+)[\'"]\)',
                r'"video":\s*{\s*"url":\s*"([^"]+)"',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_source)
                if matches:
                    video_url = matches[0].replace('\\/', '/')
                    print(f"Found video URL (regex): {video_url[:80]}...")
                    return video_url
        except Exception as e:
            print(f"Regex extraction error: {e}")
        
        # روش ۲: پیدا کردن در تگ video
        try:
            soup = BeautifulSoup(page_source, 'lxml')
            video_tag = soup.find('video')
            if video_tag:
                src = video_tag.get('src')
                if src:
                    return src
                # بررسی source tags
                source_tag = video_tag.find('source')
                if source_tag:
                    return source_tag.get('src')
        except Exception as e:
            print(f"BeautifulSoup extraction error: {e}")
        
        return None
    
    def get_video_details(self, url, selectors):
        """استخراج جزئیات ویدیو با روش‌های پیشرفته"""
        try:
            print(f"Loading video page: {url}")
            self.driver.get(url)
            
            # منتظر لود شدن پلیر
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "video"))
            )
            
            time.sleep(4)  # زمان برای لود ویدیو
            
            details = {
                'url': url,
                'title': '',
                'video_src': '',
                'thumbnail': '',
                'duration': '',
                'description': '',
                'file_size': 0
            }
            
            # گرفتن سورس کامل صفحه
            page_source = self.driver.page_source
            
            # استخراج عنوان
            try:
                title_elem = self.driver.find_element(By.CSS_SELECTOR, "h1.page-title, h1.title, h1")
                details['title'] = title_elem.text.strip()
            except:
                # Fallback به title صفحه
                details['title'] = self.driver.title.replace(' - XNXX.COM', '').replace(' - XNXX', '').strip()
            
            # استخراج لینک ویدیو با روش‌های مختلف
            print("Extracting video source...")
            
            # روش ۱: تلاش برای گرفتن از element video
            try:
                video_elem = self.driver.find_element(By.CSS_SELECTOR, "video")
                video_src = video_elem.get_attribute('currentSrc')
                if not video_src:
                    video_src = video_elem.get_attribute('src')
                if video_src:
                    details['video_src'] = video_src
                    print(f"Found via element: {video_src[:80]}...")
            except Exception as e:
                print(f"Element extraction failed: {e}")
            
            # روش ۲: استخراج از HTML source
            if not details['video_src']:
                details['video_src'] = self.extract_video_from_html(page_source)
            
            # روش ۳: اجرای JavaScript برای گرفتن از پلیر
            if not details['video_src']:
                try:
                    js_sources = [
                        "return document.querySelector('video')?.currentSrc;",
                        "return document.querySelector('video')?.src;",
                        "return document.querySelector('video source')?.src;",
                        "return window.html5player?.videoUrl || window.html5player?.videoUrlHigh;",
                        "return window.videoUrl || window.videoUrlHigh || window.video_url;",
                    ]
                    for js in js_sources:
                        try:
                            result = self.driver.execute_script(js)
                            if result and isinstance(result, str) and result.startswith('http'):
                                details['video_src'] = result
                                print(f"Found via JS: {result[:80]}...")
                                break
                        except:
                            continue
                except Exception as e:
                    print(f"JS extraction failed: {e}")
            
            # استخراج thumbnail
            try:
                # از meta tag
                soup = BeautifulSoup(page_source, 'lxml')
                meta_thumb = soup.find('meta', property='og:image')
                if meta_thumb:
                    details['thumbnail'] = meta_thumb.get('content', '')
                
                # یا از video poster
                if not details['thumbnail']:
                    video_elem = self.driver.find_element(By.CSS_SELECTOR, "video")
                    details['thumbnail'] = video_elem.get_attribute('poster')
            except:
                pass
            
            # استخراج مدت زمان
            try:
                duration_elem = self.driver.find_element(By.CSS_SELECTOR, "span.duration, .video-duration, [class*='duration']")
                details['duration'] = duration_elem.text.strip()
            except:
                # از JSON در صفحه
                try:
                    match = re.search(r'"duration":\s*"([^"]+)"', page_source)
                    if match:
                        details['duration'] = match.group(1)
                except:
                    pass
            
            # بررسی حجم فایل
            if details['video_src']:
                details['file_size'] = self.get_file_size(details['video_src'])
                print(f"Video size: {details['file_size']:.1f} MB")
            
            return details
            
        except Exception as e:
            print(f"Error getting video details: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_file_size(self, url):
        """دریافت حجم فایل با HEAD request"""
        import requests
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.xnxx.com/'
            }
            response = requests.head(url, headers=headers, timeout=15, allow_redirects=True)
            size = response.headers.get('content-length')
            if size:
                return int(size) / (1024 * 1024)  # MB
        except Exception as e:
            print(f"Error getting file size: {e}")
        return 0
    
    def close(self):
        """بستن مرورگر"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
