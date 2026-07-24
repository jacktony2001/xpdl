import logging
import os
from scraper import VideoScraper
from telegram_sender import TelegramSender
from database import Database
from config import BOT_TOKEN, CHAT_ID

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("🚀 شروع فرآیند اسکرپ و ارسال ویدیو")
    
    if not BOT_TOKEN or not CHAT_ID:
        logger.error("❌ توکن یا چت‌آیدی تنظیم نشده!")
        return
    
    try:
        scraper = VideoScraper()
        video_items = scraper.scrape()
        
        if not video_items:
            logger.warning("⚠️ هیچ ویدیویی پیدا نشد.")
            return
        
        db = Database()
        sender = TelegramSender(BOT_TOKEN, CHAT_ID)
        
        for entry in video_items:
            # کلید پایدار برای dedup: آدرس صفحه ویدیو (نه مسیر فایل محلی)
            key = entry.get("page_url") or entry.get("result", "")
            item = entry.get("result")
            is_file = entry.get("is_file", False)
            title = entry.get("title", "")

            if not item:
                continue

            # چک کن قبلاً فرستاده شده یا نه
            if db.is_sent(key):
                logger.info(f"⏭️ ویدیو قبلاً ارسال شده: {key}")
                # پاک کردن فایل محلی در صورت وجود
                if is_file and os.path.exists(item):
                    os.remove(item)
                    logger.info(f"🗑️ فایل پاک شد: {item}")
                continue
            
            if is_file:
                # فایل محلی (فشرده‌شده)
                result = sender.send_video_file(item, "🎬 ویدیو (فشرده)")
                # پاک کردن فایل بعد از ارسال (موفق یا ناموفق)
                if os.path.exists(item):
                    os.remove(item)
                    logger.info(f"🗑️ فایل پاک شد: {item}")
                
                if result and result.get('ok'):
                    db.mark_as_sent(key, title)
                    logger.info(f"✅ ویدیو ارسال شد")
                else:
                    logger.error(f"❌ ارسال ناموفق")
            else:
                # لینک
                result = sender.send_link(item, "🎬 ویدیو جدید")
                if result and result.get('ok'):
                    db.mark_as_sent(key, title)
                    logger.info(f"✅ لینک ارسال شد")
                else:
                    logger.error(f"❌ ارسال ناموفق")
        
        logger.info("🏁 فرآیند به پایان رسید.")
        
    except Exception as e:
        logger.error(f"💥 خطا: {e}")

if __name__ == "__main__":
    main()
