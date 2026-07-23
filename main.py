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
        
        for item in video_items:
            # چک کن قبلاً فرستاده شده یا نه
            item_hash = item[:100]  # برای دیتابیس
            if db.is_sent(item_hash):
                logger.info(f"⏭️ ویدیو قبلاً ارسال شده")
                continue
            
            # ارسال
            if item.startswith(('http://', 'https://')):
                # لینک
                result = sender.send_link(item, "🎬 ویدیو جدید")
                if result and result.get('ok'):
                    db.mark_as_sent(item_hash)
                    logger.info(f"✅ لینک ارسال شد")
            else:
                # فایل محلی
                result = sender.send_video_file(item, "🎬 ویدیو (فشرده)")
                # پاک کردن فایل بعد از ارسال (موفق یا ناموفق)
                if os.path.exists(item):
                    os.remove(item)
                    logger.info(f"🗑️ فایل پاک شد: {item}")
                
                if result and result.get('ok'):
                    db.mark_as_sent(item_hash)
                    logger.info(f"✅ ویدیو ارسال شد")
                else:
                    logger.error(f"❌ ارسال ناموفق")
        
        logger.info("🏁 فرآیند به پایان رسید.")
        
    except Exception as e:
        logger.error(f"💥 خطا: {e}")

if __name__ == "__main__":
    main()
