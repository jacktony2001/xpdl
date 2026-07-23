import logging
from scraper import VideoScraper
from telegram_sender import TelegramSender
from database import Database
from config import BOT_TOKEN, CHAT_ID

# تنظیم لاگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("🚀 شروع فرآیند اسکرپ و ارسال ویدیو")
    
    # بررسی توکن و چت‌آیدی
    if not BOT_TOKEN or not CHAT_ID:
        logger.error("❌ توکن یا چت‌آیدی تنظیم نشده! لطفاً Secrets رو چک کن.")
        return
    
    try:
        # ۱. اسکرپ کردن
        scraper = VideoScraper()
        video_links = scraper.scrape()
        
        if not video_links:
            logger.warning("⚠️ هیچ ویدیویی برای ارسال وجود ندارد.")
            return
        
        # ۲. اتصال به دیتابیس
        db = Database()
        new_videos = db.get_new_videos(video_links)
        
        if not new_videos:
            logger.info("ℹ️ همه ویدیوها قبلاً ارسال شده‌اند.")
            return
        
        # ۳. ارسال به تلگرام
        sender = TelegramSender(BOT_TOKEN, CHAT_ID)
        for video in new_videos:
            success = sender.send_video(video)
            if success:
                db.mark_as_sent(video)
                logger.info(f"✅ ویدیو ارسال شد: {video}")
            else:
                logger.error(f"❌ ارسال ویدیو ناموفق: {video}")
        
        logger.info("🏁 فرآیند با موفقیت به پایان رسید.")
        
    except Exception as e:
        logger.error(f"💥 خطای کلی در برنامه: {e}")

if __name__ == "__main__":
    main()
