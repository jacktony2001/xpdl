import logging
from scraper import VideoScraper
from telegram_sender import TelegramSender
from database import Database
from config import BOT_TOKEN, CHAT_ID

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("🚀 شروع فرآیند اسکرپ و ارسال ویدیو")
    
    if not BOT_TOKEN or not CHAT_ID:
        logger.error("❌ توکن یا چت‌آیدی تنظیم نشده! لطفاً Secrets رو چک کن.")
        logger.error(f"BOT_TOKEN: {'OK' if BOT_TOKEN else 'MISSING'}")
        logger.error(f"CHAT_ID: {'OK' if CHAT_ID else 'MISSING'}")
        return
    
    try:
        scraper = VideoScraper()
        video_links = scraper.scrape()
        
        if not video_links:
            logger.warning("⚠️ هیچ ویدیویی برای ارسال وجود ندارد.")
            return
        
        db = Database()
        
        # فیلتر کردن لینک‌های جدید (ارسال نشده)
        new_videos = []
        for link in video_links:
            if not db.is_sent(link):  # این متد توی دیتابیس هست
                new_videos.append(link)
        
        if not new_videos:
            logger.info("ℹ️ همه ویدیوها قبلاً ارسال شده‌اند.")
            return
        
        sender = TelegramSender(BOT_TOKEN, CHAT_ID)
        for video in new_videos:
            success = sender.send_video(video, f"🎬 ویدیو جدید:\n{video}")
            if success and success.get('ok'):
                db.mark_as_sent(video)
                logger.info(f"✅ ویدیو ارسال شد: {video}")
            else:
                logger.error(f"❌ ارسال ویدیو ناموفق: {video}")
        
        logger.info("🏁 فرآیند با موفقیت به پایان رسید.")
        
    except Exception as e:
        logger.error(f"💥 خطای کلی در برنامه: {e}")

if __name__ == "__main__":
    main()
