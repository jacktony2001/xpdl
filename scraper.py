import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import requests
from bs4 import BeautifulSoup
import chromedriver_autoinstaller

class ContentScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        # نصب خودکار chromedriver مناسب
        chromedriver_autoinstaller.install()
        
        options = uc.ChromeOptions()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        self.driver = uc.Chrome(options=options)
        self.driver.set_page_load_timeout(30)
    
    def get_video_links(self, url, selectors):
        try:
            print(f"Loading: {url}")
            self.driver.get(url)
            time.sleep(5)
            
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            elements = self.driver.find_elements(By.CSS_SELECTOR, selectors['video_links'])
            links = []
            for elem in elements:
                href = elem.get_attribute('href')
                if href and '/video-' in href and 'xnxx.com' in href:
                    clean = href.split('?')[0]
                    if clean not in links:
                        links.append(clean)
            
            print(f"Found {len(links)} videos")
            return links
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def extract_video_from_page(self, page_source):
        patterns = [
            r'"url":"(https?://[^"]+\.mp4[^"]*)"',
            r'"videoUrl":"(https?://[^"]+\.mp4[^"]*)"',
            r'html5player\.setVideoUrlHigh\([\'"]([^\'"]+)[\'"]\)',
            r'html5player\.setVideoUrlLow\([\'"]([^\'"]+)[\'"]\)',
            r'"contentUrl":"(https?://[^"]+\.mp4[^"]*)"',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, page_source)
            if matches:
                return matches[0].replace('\\/', '/')
        return None
    
    def get_video_details(self, url, selectors):
        try:
            print(f"Loading video: {url}")
            self.driver.get(url)
            time.sleep(5)
            
            details = {
                'url': url,
                'title': '',
                'video_src': '',
                'thumbnail': '',
                'duration': '',
                'file_size': 0
            }
            
            page_source = self.driver.page_source
            
            # Title
            try:
                title_elem = self.driver.find_element(By.CSS_SELECTOR, selectors['title'])
                details['title'] = title_elem.text.strip()
            except:
                details['title'] = self.driver.title.replace(' - XNXX.COM', '').strip()
            
            # Video URL from page source
            details['video_src'] = self.extract_video_from_page(page_source)
            
            # Try JS methods if regex failed
            if not details['video_src']:
                try:
                    js_result = self.driver.execute_script("return window.html5player?.videoUrlHigh || window.html5player?.videoUrlLow;")
                    if js_result:
                        details['video_src'] = js_result
                except:
                    pass
            
            # Thumbnail
            try:
                soup = BeautifulSoup(page_source, 'lxml')
                meta = soup.find('meta', property='og:image')
                if meta:
                    details['thumbnail'] = meta.get('content', '')
            except:
                pass
            
            # Duration
            try:
                dur_elem = self.driver.find_element(By.CSS_SELECTOR, selectors['duration'])
                details['duration'] = dur_elem.text.strip()
            except:
                pass
            
            # File size
            if details['video_src']:
                details['file_size'] = self.get_file_size(details['video_src'])
            
            return details
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def get_file_size(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.xnxx.com/'}
            r = requests.head(url, headers=headers, timeout=15, allow_redirects=True)
            size = r.headers.get('content-length')
            if size:
                return int(size) / (1024 * 1024)
        except:
            pass
        return 0
    
    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
