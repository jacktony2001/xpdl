import requests
import logging
import os

logger = logging.getLogger(__name__)

class TelegramSender:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_video_file(self, file_path, caption=""):
        """ارسال فایل ویدیویی محلی (فشرده‌شده)"""
        try:
            if file_path.startswith(('http://', 'https://')):
                return self.send_link(file_path, caption)
            
            if not os.path.exists(file_path):
                logger.error(f"❌ فایل وجود ندارد: {file_path}")
                return None
            
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            if file_size > 50:
                logger.warning(f"⚠️ حجم فایل {file_size:.2f} MB بیشتر از 50 مگ است، ارسال به صورت لینک")
                return self.send_link(file_path, caption)
            
            url = f"{self.base_url}/sendVideo"
            with open(file_path, "rb") as f:
                files = {"video": f}
                data = {"chat_id": self.chat_id, "caption": caption[:1024], "supports_streaming": True}
                response = requests.post(url, data=data, files=files, timeout=300)
                result = response.json()
                
                if result.get('ok'):
                    logger.info(f"✅ ویدیو ارسال شد: {file_path}")
                    return result
                else:
                    logger.error(f"❌ خطا: {result}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ خطا: {e}")
            return None
    
    def send_link(self, video_url, caption=""):
        """ارسال لینک ویدیو (بدون parse_mode)"""
        try:
            message = f"🎬 ویدیو جدید\n\n{video_url}"
            if caption and caption != "🎬 ویدیو جدید":
                clean_caption = caption.replace('_', ' ').replace('*', '').replace('`', '').replace('[', '').replace(']', '')
                message = f"{clean_caption}\n\n{video_url}"
            
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'disable_web_page_preview': False
                # parse_mode رو کامل حذف کردیم
            }
            
            response = requests.post(url, json=payload, timeout=30)
            result = response.json()
            
            if result.get('ok'):
                logger.info(f"✅ لینک ویدیو ارسال شد")
                return result
            else:
                logger.error(f"❌ خطا: {result}")
                return None
                
        except Exception as e:
            logger.error(f"❌ خطا: {e}")
            return None
    
    def send_content(self, data):
        title = data.get('title', 'بدون عنوان')
        video_url = data.get('video_src', '')
        page_url = data.get('url', '')
        
        caption = f"🎬 {title}"
        if page_url:
            caption += f"\n📄 مشاهده در سایت: {page_url}"
        
        return self.send_link(video_url, caption)
