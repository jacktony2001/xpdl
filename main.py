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
        video_items = scraper.scrape()  # لیست مسیر فایل‌ها یا لینک‌ها
        
        if not video_items:
            logger.warning("⚠️ هیچ ویدیویی پیدا نشد.")
            return
        
        db = Database()
        sender = TelegramSender(BOT_TOKEN, CHAT_ID)
        
        for item in video_items:
            # چک کن قبلاً فرستاده شده یا نه
            if db.is_sent(item):
                logger.info(f"⏭️ ویدیو قبلاً ارسال شده: {item[:50]}...")
                continue
            
            # ارسال
            if item.startswith(('http://', 'https://')):
                # لینک
                result = sender.send_link(item, "🎬 ویدیو جدید")
            else:
                # فایل محلی
                result = sender.send_video_file(item, "🎬 ویدیو (فشرده‌شده)")
                # پاک کردن فایل بعد از ارسال
                if os.path.exists(item):
                    os.remove(item)
                    logger.info(f"🗑️ فایل پاک شد: {item}")
            
            if result and result.get('ok'):
                db.mark_as_sent(item)
                logger.info(f"✅ ارسال شد: {item[:50]}...")
            else:
                logger.error(f"❌ ارسال ناموفق: {item[:50]}...")
        
        logger.info("🏁 فرآیند به پایان رسید.")
        
    except Exception as e:
        logger.error(f"💥 خطا: {e}")

if __name__ == "__main__":
    main()
