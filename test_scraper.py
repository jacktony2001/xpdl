# test_scraper.py - برای تست استخراج ویدیو
from scraper import ContentScraper
from config import *
import json

def test_single_video():
    """تست استخراج یک ویدیو خاص"""
    scraper = ContentScraper(headless=False)  # False برای دیدن مرورگر
    
    try:
        # لینک تست
        test_url = "https://www.xnxx.com/video-xxx"  # یک لینک واقعی قرار دهید
        
        print("Testing video extraction...")
        details = scraper.get_video_details(test_url, SELECTORS)
        
        if details:
            print("\n" + "="*50)
            print("✅ SUCCESS!")
            print(f"Title: {details['title']}")
            print(f"Video URL: {details['video_src'][:100]}..." if details['video_src'] else "❌ No video URL")
            print(f"Thumbnail: {details['thumbnail']}")
            print(f"Duration: {details['duration']}")
            print(f"File Size: {details['file_size']:.1f} MB")
            print("="*50)
        else:
            print("❌ Failed to extract details")
            
    finally:
        scraper.close()

def test_listing():
    """تست دریافت لیست لینک‌ها"""
    scraper = ContentScraper(headless=True)
    
    try:
        links = scraper.get_video_links(BASE_URL, SELECTORS)
        print(f"\nFound {len(links)} links:")
        for i, link in enumerate(links[:5], 1):
            print(f"{i}. {link}")
    finally:
        scraper.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "single":
        test_single_video()
    else:
        test_listing()
