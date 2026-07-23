import time
import logging
import json # For JSON processing
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import chromedriver_autoinstaller
import os # For file operations

from config import WEBSITE_URL, CHROME_OPTIONS, SCRAPER_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VideoScraper:
    def __init__(self):
        self.driver = None
        self.setup_driver()

    def setup_driver(self):
        """Sets up the Chrome driver with specific configurations."""
        try:
            chromedriver_autoinstaller.install()
            options = Options()
            for arg in CHROME_OPTIONS:
                options.add_argument(arg)
            self.driver = webdriver.Chrome(options=options)
            logger.info("✅ Chrome driver successfully initialized.")
        except Exception as e:
            logger.error(f"❌ Error initializing Chrome driver: {e}")
            raise

    def _find_elements(self, selectors):
        """Finds elements using a list of CSS selectors."""
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    return elements
            except Exception as e:
                logger.debug(f"Selector {selector} did not work: {e}")
        return []

    def _scroll_to_load_more(self):
        """Scrolls the page to load more content."""
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
        """Retrieves links to individual video pages from the homepage."""
        video_page_links = []
        try:
            logger.info(f"🔄 Connecting to homepage: {WEBSITE_URL}")
            self.driver.get(WEBSITE_URL)
            time.sleep(SCRAPER_CONFIG.get("wait_time", 7)) # Increased wait time for homepage
            
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
                logger.warning("⚠️ No video page links found on the homepage!")
            else:
                logger.info(f"✅ Found {len(video_page_links)} video page links from the homepage.")
            
            return video_page_links

        except TimeoutException:
            logger.error("❌ Homepage load timed out.")
            return []
        except Exception as e:
            logger.error(f"❌ Error getting homepage video links: {e}")
            return []

    def get_final_video_url(self, video_page_url):
        """Retrieves the final video download URL from a specific video page."""
        final_url = None
        try:
            logger.info(f"🔄 Visiting video page: {video_page_url}")
            self.driver.get(video_page_url)
            # Increased wait time for video page to load
            time.sleep(SCRAPER_CONFIG.get("wait_time", 8)) 

            # --- Section to save page code for debugging ---
            try:
                page_source = self.driver.page_source
                # Create a filename by removing invalid characters from the URL
                safe_url_part = "".join(c for c in video_page_url if c.isalnum() or c in ('-', '_')).rstrip()
                filename = f"page_dump_{safe_url_part[:50]}.html" # Limit filename length
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(page_source)
                logger.info(f"✅ Full page source saved to file '{filename}'.")
            except Exception as e:
                logger.error(f"Error saving page source: {e}")
            # --- End of page saving section ---

            # --- Primary attempt: Find download link using your specific selector ---
            primary_download_selector = "p.text-center.download-ready a"
            download_elements = self._find_elements([primary_download_selector])
            
            if download_elements:
                href = download_elements[0].get_attribute("href")
                # Check if the link is an mp4 and starts with "mp4-cdn"
                if href and href.endswith('.mp4') and "mp4-cdn" in href:
                    final_url = href
                    logger.info(f"✅ Download link found using primary selector '{primary_download_selector}': {final_url}")
                    return final_url
            
            if not final_url:
                logger.warning(f"⚠️ Download link not found with primary selector '{primary_download_selector}' (or format was incorrect).")

            # --- Secondary attempt: Find download link from JSON-LD (contentUrl) ---
            logger.info("Attempting to find download link from JSON-LD (contentUrl)...")
            try:
                # Find the JSON-LD script tag
                script_tag = self.driver.find_element(By.XPATH, "//script[@type='application/ld+json']")
                script_content = script_tag.get_attribute("innerHTML")
                
                data = json.loads(script_content)
                
                # Check for VideoObject structure and contentUrl
                if data.get("@type") == "VideoObject" and "contentUrl" in data:
                    json_ld_url = data["contentUrl"]
                    if json_ld_url and json_ld_url.endswith('.mp4') and "mp4-cdn" in json_ld_url:
                        final_url = json_ld_url
                        logger.info(f"✅ Download link found from JSON-LD (contentUrl): {final_url}")
                        return final_url
                else:
                    logger.warning("Expected JSON-LD structure not found or contentUrl missing.")

            except NoSuchElementException:
                logger.warning("JSON-LD script tag not found on the page.")
            except json.JSONDecodeError:
                logger.warning("Error decoding JSON-LD content.")
            except Exception as e:
                logger.warning(f"Error processing JSON-LD: {e}")

            # --- Tertiary attempt: Use general fallback selectors ---
            if not final_url:
                logger.info("Trying general fallback methods to find download link...")
                fallback_selectors = [
                    "a[href$='.mp4']",       # Links ending with .mp4
                    "video[src$='.mp4']",     # Video tags with src ending in .mp4
                    "a[download]",            # Links with a download attribute
                    ".download-btn a",        # Links within elements having class 'download-btn'
                    "a[href*='mp4-cdn']"      # Links containing 'mp4-cdn' directly
                ]
                for selector in fallback_selectors:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in elements:
                        href = el.get_attribute("href")
                        if href and href.endswith('.mp4') and "mp4-cdn" in href:
                            final_url = href
                            logger.info(f"✅ Download link found using fallback selector '{selector}': {final_url}")
                            return final_url

            if not final_url:
                logger.warning(f"⚠️ No final video link found for {video_page_url} using any method.")

            return final_url

        except TimeoutException:
            logger.error(f"❌ Video page load timed out for {video_page_url}")
            return None
        except ElementClickInterceptedException:
            logger.error(f"❌ Element click intercepted on {video_page_url} (possible popup or overlay).")
            return None
        except Exception as e:
            logger.error(f"❌ Error getting final video link from {video_page_url}: {e}")
            return None

    def scrape(self):
        """Main method to initiate the two-stage scraping process with a video limit."""
        all_final_video_urls = []
        homepage_links = self.get_video_page_links_from_homepage()

        if not homepage_links:
            logger.warning("No video page links found for further processing.")
            return []

        max_videos_to_process = 10 
        
        # Process up to the maximum number of videos found on the homepage
        links_to_process = homepage_links[:max_videos_to_process]
        
        logger.info(f"Starting to process {len(links_to_process)} video links from the homepage...")

        processed_count = 0
        for link in links_to_process:
            final_url = self.get_final_video_url(link)
            if final_url:
                all_final_video_urls.append(final_url)
            processed_count += 1
            # Break if we have processed all the links we intended to process (up to max_videos_to_process)
            if processed_count >= len(links_to_process): 
                break
        
        if not all_final_video_urls:
            logger.warning("⚠️ No final video links were extracted.")
        else:
            logger.info(f"✅ Extracted a total of {len(all_final_video_urls)} final video links.")
            
        return list(set(all_final_video_urls)) # Remove duplicates

    def __del__(self):
        """Cleans up the driver when the scraper object is deleted."""
        if self.driver:
            self.driver.quit()
            logger.info("🚪 Driver closed.")
