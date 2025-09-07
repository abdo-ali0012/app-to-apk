"""
وظائف مساعدة ومرافق التطبيق
"""
import os
import re
import json
import hashlib
import threading
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
import requests
from config import CONFIG_DIR, MESSAGES

class Logger:
    """نظام تسجيل الأحداث"""
    
    def __init__(self):
        self.log_file = CONFIG_DIR / "app.log"
        self.lock = threading.Lock()
    
    def log(self, level, message):
        """تسجيل رسالة"""
        with self.lock:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {level}: {message}\n"
            
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
    
    def info(self, message):
        self.log("INFO", message)
    
    def warning(self, message):
        self.log("WARNING", message)
    
    def error(self, message):
        self.log("ERROR", message)

class SettingsManager:
    """إدارة إعدادات التطبيق"""
    
    def __init__(self):
        self.settings_file = CONFIG_DIR / "settings.json"
        self.default_settings = {
            "theme": "dark",
            "language": "ar",
            "download_path": str(Path.home() / "Downloads"),
            "default_quality": "720p",
            "auto_convert_audio": False,
            "concurrent_downloads": 3,
            "notification_sound": True
        }
        self.load_settings()
    
    def load_settings(self):
        """تحميل الإعدادات من الملف"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    self.settings = json.load(f)
            else:
                self.settings = self.default_settings.copy()
                self.save_settings()
        except Exception as e:
            Logger().error(f"خطأ في تحميل الإعدادات: {e}")
            self.settings = self.default_settings.copy()
    
    def save_settings(self):
        """حفظ الإعدادات في الملف"""
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            Logger().error(f"خطأ في حفظ الإعدادات: {e}")
    
    def get(self, key, default=None):
        """الحصول على قيمة إعداد"""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """تعديل قيمة إعداد"""
        self.settings[key] = value
        self.save_settings()

def validate_url(url):
    """التحقق من صحة الرابط"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def sanitize_filename(filename):
    """تنظيف اسم الملف من الأحرف غير المسموحة"""
    # إزالة الأحرف غير المسموحة
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # تقليل الأحرف المتتالية
    filename = re.sub(r'\s+', ' ', filename).strip()
    # تحديد الطول الأقصى
    if len(filename) > 200:
        filename = filename[:200]
    return filename

def format_file_size(size_bytes):
    """تنسيق حجم الملف"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024.0 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_names[i]}"

def format_duration(seconds):
    """تنسيق مدة الفيديو"""
    if seconds < 0:
        return "00:00"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def calculate_md5(file_path):
    """حساب MD5 للملف"""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except:
        return None

def check_internet_connection():
    """التحقق من الاتصال بالإنترنت"""
    try:
        response = requests.get("https://www.google.com", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_video_info_from_url(url):
    """استخراج معلومات أولية من الرابط"""
    info = {
        "platform": "غير معروف",
        "url": url,
        "valid": validate_url(url)
    }
    
    if not info["valid"]:
        return info
    
    domain = urlparse(url).netloc.lower()
    
    # تحديد المنصة بناء على النطاق
    if "youtube.com" in domain or "youtu.be" in domain:
        info["platform"] = "YouTube"
    elif "facebook.com" in domain or "fb.watch" in domain:
        info["platform"] = "Facebook"
    elif "instagram.com" in domain:
        info["platform"] = "Instagram"
    elif "tiktok.com" in domain:
        info["platform"] = "TikTok"
    elif "twitter.com" in domain or "x.com" in domain:
        info["platform"] = "Twitter"
    elif "vimeo.com" in domain:
        info["platform"] = "Vimeo"
    elif "dailymotion.com" in domain:
        info["platform"] = "Dailymotion"
    
    return info

class NotificationManager:
    """إدارة الإشعارات"""
    
    def __init__(self):
        self.callbacks = []
    
    def add_callback(self, callback):
        """إضافة دالة استدعاء للإشعارات"""
        self.callbacks.append(callback)
    
    def notify(self, message, type="info"):
        """إرسال إشعار"""
        for callback in self.callbacks:
            try:
                callback(message, type)
            except:
                pass

# إنشاء كائنات عامة
logger = Logger()
settings_manager = SettingsManager()
notification_manager = NotificationManager()