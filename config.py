"""
إعدادات التطبيق والثوابت
"""
import os
from pathlib import Path

# إعدادات التطبيق
APP_NAME = "SnapTube Pro"
APP_VERSION = "2.0.0"
APP_AUTHOR = "SnapTube Team"

# مسارات التطبيق
BASE_DIR = Path(__file__).parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
TEMP_DIR = BASE_DIR / "temp"
CONFIG_DIR = BASE_DIR / "config"
ASSETS_DIR = BASE_DIR / "assets"

# إنشاء المجلدات إذا لم تكن موجودة
for directory in [DOWNLOADS_DIR, TEMP_DIR, CONFIG_DIR, ASSETS_DIR]:
    directory.mkdir(exist_ok=True)

# إعدادات التنزيل
DEFAULT_QUALITY = "720p"
SUPPORTED_QUALITIES = {
    "144p": "worst[height<=144]",
    "240p": "worst[height<=240]",
    "360p": "worst[height<=360]",
    "480p": "best[height<=480]",
    "720p": "best[height<=720]",
    "1080p": "best[height<=1080]",
    "1440p": "best[height<=1440]",
    "4K": "best[height<=2160]",
    "أفضل جودة": "best",
    "أقل جودة": "worst"
}

# إعدادات الصوت
AUDIO_QUALITIES = {
    "64 kbps": "64",
    "128 kbps": "128", 
    "192 kbps": "192",
    "256 kbps": "256",
    "320 kbps": "320"
}

# ألوان التطبيق
COLORS = {
    "primary": "#2196F3",
    "secondary": "#FF9800", 
    "success": "#4CAF50",
    "error": "#F44336",
    "warning": "#FF5722",
    "info": "#00BCD4",
    "light": "#FAFAFA",
    "dark": "#212121",
    "text_light": "#FFFFFF",
    "text_dark": "#000000"
}

# إعدادات الواجهة
THEME_MODES = ["light", "dark", "auto"]
DEFAULT_THEME = "dark"
WINDOW_SIZE = "1200x800"
MIN_WINDOW_SIZE = "900x600"

# إعدادات المشغل
SUPPORTED_VIDEO_FORMATS = [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"]
SUPPORTED_AUDIO_FORMATS = [".mp3", ".wav", ".ogg", ".flac", ".aac", ".wma"]

# رسائل التطبيق
MESSAGES = {
    "download_started": "بدأ التنزيل...",
    "download_completed": "تم التنزيل بنجاح",
    "download_failed": "فشل التنزيل",
    "invalid_url": "الرابط غير صحيح",
    "no_internet": "لا يوجد اتصال بالإنترنت",
    "conversion_started": "بدأ التحويل...",
    "conversion_completed": "تم التحويل بنجاح"
}

# منصات مدعومة
SUPPORTED_PLATFORMS = [
    "YouTube", "Facebook", "Instagram", "TikTok", "Twitter", "Dailymotion",
    "Vimeo", "SoundCloud", "Twitch", "Reddit", "Tumblr", "Pinterest"
]