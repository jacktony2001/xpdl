from config import *
from scraper import ContentScraper
from telegram_sender import TelegramSender
from database import Database

def main():
    print("🚀 Starting scraper...")
    
    if TELEGRAM_BOT_TOKEN == 'YOUR_BOT_TOKEN':
        print("❌ Set TELEGRAM_BOT_TOKEN in Secrets!")
        return
    
    db = Database()
    scraper = ContentScraper(headless=HEADLESS)
    sender = TelegramSender(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    
    try:
        links = scraper.get_video_links(BASE_URL, SELECTORS)
        if not links:
            print("⚠️ No links found")
            return
        
        new_links = [l for l in links if not db.is_sent(l)]
        print(f"🆕 New videos: {len(new_links)}")
        
        if not new_links:
            print("✅ Nothing new")
            return
        
        new_links = new_links[:MAX_VIDEOS_PER_RUN]
        sent = 0
        
        for link in new_links:
            try:
                print(f"\n📥 {link}")
                details = scraper.get_video_details(link, SELECTORS)
                
                if not details or not details.get('title'):
                    print("⚠️ No details")
                    continue
                
                if any(p in details['title'].lower() for p in EXCLUDE_PATTERNS):
                    print("🚫 Excluded")
                    continue
                
                print(f"📝 {details['title'][:60]}")
                print(f"🎬 Video: {details['video_src'][:80] if details['video_src'] else 'Not found'}")
                
                result = sender.send_content(details)
                
                if result and result.get('ok'):
                    db.mark_as_sent(link, details['title'])
                    sent += 1
                    print("✅ Sent")
                else:
                    print(f"❌ Failed: {result}")
                
                import time
                time.sleep(3)
                
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
        
        print(f"\n🎉 Done! Sent {sent}/{len(new_links)}")
        print(f"📊 Total: {db.get_stats()}")
        
    except Exception as e:
        print(f"❌ Fatal: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
