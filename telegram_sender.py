import requests

class TelegramSender:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_video(self, video_url, caption="", thumb=None):
        url = f"{self.base_url}/sendVideo"
        payload = {
            'chat_id': self.chat_id,
            'video': video_url,
            'caption': caption[:1024],
            'parse_mode': 'HTML',
            'supports_streaming': True
        }
        if thumb:
            payload['thumbnail'] = thumb
        
        try:
            r = requests.post(url, json=payload, timeout=60)
            result = r.json()
            if result.get('ok'):
                return result
            if 'too big' in str(result).lower():
                return self.send_link(video_url, caption)
            return result
        except Exception as e:
            print(f"Send error: {e}")
            return self.send_link(video_url, caption)
    
    def send_link(self, video_url, caption):
        message = f"{caption}\n\n🎥 <b>Link:</b>\n{video_url}"
        url = f"{self.base_url}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': False
        }
        return requests.post(url, json=payload, timeout=30).json()
    
    def send_content(self, data):
        title = data.get('title', 'No title')
        video_url = data.get('video_src', '')
        thumb = data.get('thumbnail', '')
        duration = data.get('duration', '')
        page_url = data.get('url', '')
        size = data.get('file_size', 0)
        
        caption = f"🎬 <b>{title}</b>"
        if duration:
            caption += f"\n⏱ {duration}"
        if size:
            caption += f"\n📦 {size:.1f} MB"
        caption += f"\n\n🔗 <a href='{page_url}'>View on site</a>"
        
        if video_url and 0 < size <= 50:
            print(f"Sending video: {title[:50]}...")
            return self.send_video(video_url, caption, thumb)
        else:
            print(f"Sending link (size: {size:.1f}MB): {title[:50]}...")
            if thumb:
                # Send photo with link
                photo_url = f"{self.base_url}/sendPhoto"
                requests.post(photo_url, json={
                    'chat_id': self.chat_id,
                    'photo': thumb,
                    'caption': caption,
                    'parse_mode': 'HTML'
                }, timeout=30)
                return {'ok': True}
            return self.send_link(page_url, caption)
