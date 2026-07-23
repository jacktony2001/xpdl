def download_and_compress_video(self, video_url):
    """دانلود و فشرده‌سازی ویدیو با ffmpeg - نسخه اصلاح شده"""
    try:
        if not self.compression_config.get("enabled", True):
            logger.info("ℹ️ فشرده‌سازی غیرفعال است")
            return video_url

        logger.info(f"📥 دانلود ویدیو...")
        response = requests.get(video_url, stream=True, timeout=120)
        temp_file = "temp_video.mp4"
        
        with open(temp_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        original_size = os.path.getsize(temp_file) / (1024 * 1024)
        logger.info(f"📊 حجم اصلی: {original_size:.2f} MB")

        # اگه حجم کمتر از حد مجازه، بدون فشرده‌سازی برگردون
        max_size = self.compression_config.get("max_size_mb", 45)
        if original_size <= max_size:
            logger.info(f"ℹ️ حجم ویدیو کمتر از {max_size} MB است، نیازی به فشرده‌سازی نیست")
            os.remove(temp_file)
            return video_url

        # فشرده‌سازی با تنظیمات جدید
        logger.info("🔄 در حال فشرده‌سازی ویدیو...")
        output_path = "compressed_video.mp4"
        
        scale = self.compression_config.get("scale", "640:360")
        crf = self.compression_config.get("crf", 32)
        audio_bitrate = self.compression_config.get("audio_bitrate", "64k")
        preset = self.compression_config.get("preset", "fast")
        
        # استفاده از 2-pass برای فشرده‌سازی بهتر
        cmd = [
            "ffmpeg",
            "-i", temp_file,
            "-vf", f"scale={scale}",
            "-c:v", "libx264",
            "-crf", str(crf),
            "-preset", preset,
            "-c:a", "aac",
            "-b:a", audio_bitrate,
            "-movflags", "+faststart",
            "-y",
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"❌ خطا در ffmpeg: {result.stderr}")
            os.remove(temp_file)
            return video_url

        # پاک کردن فایل موقت
        os.remove(temp_file)
        
        final_size = os.path.getsize(output_path) / (1024 * 1024)
        logger.info(f"✅ فشرده‌سازی کامل شد! حجم نهایی: {final_size:.2f} MB")
        
        # اگه حجم بازم بالاست، با کیفیت پایین‌تر دوباره امتحان کن
        if final_size > max_size:
            logger.info("🔄 حجم بازم بالاست، فشرده‌سازی مجدد با کیفیت پایین‌تر...")
            cmd[cmd.index("-crf") + 1] = str(crf + 5)
            cmd[cmd.index("-vf") + 1] = "scale=480:320"  # رزولوشن پایین‌تر
            subprocess.run(cmd, capture_output=True, text=True)
            final_size = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"✅ حجم نهایی بعد از فشرده‌سازی مجدد: {final_size:.2f} MB")

        # اگه بازم بالاست، به عنوان لینک برگردون
        if final_size > max_size:
            logger.warning(f"⚠️ حجم بازم بالاست ({final_size:.2f} MB)، ارسال به صورت لینک")
            os.remove(output_path)
            return video_url

        return output_path

    except Exception as e:
        logger.error(f"❌ خطا در فشرده‌سازی: {e}")
        if os.path.exists("temp_video.mp4"):
            os.remove("temp_video.mp4")
        return video_url
