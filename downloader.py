"""
منطق تنزيل الفيديوهات والتحويل
"""
import os
import threading
import subprocess
from pathlib import Path
import yt_dlp
from moviepy.video.io.VideoFileClip import VideoFileClip
from utils import logger, sanitize_filename, format_file_size, notification_manager
from config import DOWNLOADS_DIR, TEMP_DIR, SUPPORTED_QUALITIES, AUDIO_QUALITIES

class VideoDownloader:
    """فئة تنزيل الفيديوهات"""
    
    def __init__(self):
        self.active_downloads = {}
        self.download_history = []
        self.lock = threading.Lock()
    
    def get_video_info(self, url, callback=None):
        """الحصول على معلومات الفيديو"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                video_info = {
                    'title': info.get('title', 'فيديو بدون عنوان'),
                    'uploader': info.get('uploader', 'غير معروف'),
                    'duration': info.get('duration', 0),
                    'view_count': info.get('view_count', 0),
                    'description': info.get('description', ''),
                    'thumbnail': info.get('thumbnail', ''),
                    'formats': self._extract_formats(info.get('formats', [])),
                    'url': url,
                    'platform': info.get('extractor', 'غير معروف')
                }
                
                if callback:
                    callback(video_info, None)
                return video_info
                
        except Exception as e:
            error_msg = f"خطأ في الحصول على معلومات الفيديو: {str(e)}"
            logger.error(error_msg)
            if callback:
                callback(None, error_msg)
            return None
    
    def _extract_formats(self, formats):
        """استخراج الصيغ المتاحة"""
        video_formats = []
        audio_formats = []
        
        for fmt in formats:
            if fmt.get('vcodec') != 'none' and fmt.get('acodec') != 'none':
                # فيديو مع صوت
                quality = f"{fmt.get('height', 'غير محدد')}p"
                size = fmt.get('filesize') or fmt.get('filesize_approx', 0)
                
                video_formats.append({
                    'format_id': fmt['format_id'],
                    'quality': quality,
                    'ext': fmt.get('ext', 'mp4'),
                    'filesize': format_file_size(size) if size else 'غير محدد',
                    'fps': fmt.get('fps'),
                    'vcodec': fmt.get('vcodec'),
                    'acodec': fmt.get('acodec')
                })
            elif fmt.get('acodec') != 'none' and fmt.get('vcodec') == 'none':
                # صوت فقط
                quality = f"{fmt.get('abr', 'غير محدد')} kbps"
                size = fmt.get('filesize') or fmt.get('filesize_approx', 0)
                
                audio_formats.append({
                    'format_id': fmt['format_id'],
                    'quality': quality,
                    'ext': fmt.get('ext', 'mp3'),
                    'filesize': format_file_size(size) if size else 'غير محدد',
                    'acodec': fmt.get('acodec')
                })
        
        return {
            'video': sorted(video_formats, key=lambda x: int(x['quality'].replace('p', '')) if x['quality'].replace('p', '').isdigit() else 0, reverse=True),
            'audio': sorted(audio_formats, key=lambda x: int(x['quality'].replace(' kbps', '')) if x['quality'].replace(' kbps', '').isdigit() else 0, reverse=True)
        }
    
    def download_video(self, url, quality="720p", output_path=None, progress_callback=None, completion_callback=None):
        """تنزيل فيديو"""
        download_id = str(hash(url + quality))
        
        if download_id in self.active_downloads:
            notification_manager.notify("التنزيل قيد التشغيل بالفعل", "warning")
            return download_id
        
        # إنشاء thread للتنزيل
        thread = threading.Thread(
            target=self._download_thread,
            args=(download_id, url, quality, output_path, progress_callback, completion_callback)
        )
        
        self.active_downloads[download_id] = {
            'thread': thread,
            'status': 'preparing',
            'progress': 0,
            'url': url,
            'quality': quality,
            'paused': False
        }
        
        thread.start()
        return download_id
    
    def _download_thread(self, download_id, url, quality, output_path, progress_callback, completion_callback):
        """Thread تنزيل الفيديو"""
        try:
            if not output_path:
                output_path = DOWNLOADS_DIR
            
            Path(output_path).mkdir(parents=True, exist_ok=True)
            
            def progress_hook(d):
                if download_id not in self.active_downloads:
                    return
                
                if d['status'] == 'downloading':
                    downloaded = d.get('downloaded_bytes', 0)
                    total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                    
                    if total > 0:
                        progress = int((downloaded / total) * 100)
                        self.active_downloads[download_id]['progress'] = progress
                        
                        if progress_callback:
                            progress_callback(download_id, progress, downloaded, total)
                
                elif d['status'] == 'finished':
                    self.active_downloads[download_id]['status'] = 'completed'
                    self.active_downloads[download_id]['progress'] = 100
                    self.active_downloads[download_id]['filename'] = d['filename']
            
            # إعداد خيارات التنزيل
            ydl_opts = {
                'format': SUPPORTED_QUALITIES.get(quality, 'best'),
                'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                'progress_hooks': [progress_hook],
                'noplaylist': True,
                'extractaudio': False,
            }
            
            # بدء التنزيل
            self.active_downloads[download_id]['status'] = 'downloading'
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # إضافة إلى السجل
                download_record = {
                    'title': info.get('title', 'فيديو بدون عنوان'),
                    'url': url,
                    'quality': quality,
                    'filename': self.active_downloads[download_id].get('filename', ''),
                    'download_date': str(Path().cwd()),
                    'status': 'completed'
                }
                
                self.download_history.append(download_record)
                
                if completion_callback:
                    completion_callback(download_id, True, download_record)
                
                notification_manager.notify(f"تم تنزيل: {download_record['title']}", "success")
                
        except Exception as e:
            error_msg = f"خطأ في التنزيل: {str(e)}"
            logger.error(error_msg)
            
            if download_id in self.active_downloads:
                self.active_downloads[download_id]['status'] = 'error'
                self.active_downloads[download_id]['error'] = error_msg
            
            if completion_callback:
                completion_callback(download_id, False, error_msg)
            
            notification_manager.notify(error_msg, "error")
        
        finally:
            # تنظيف
            if download_id in self.active_downloads:
                del self.active_downloads[download_id]
    
    def download_audio(self, url, quality="192", output_path=None, progress_callback=None, completion_callback=None):
        """تنزيل الصوت فقط"""
        download_id = str(hash(url + "audio" + quality))
        
        if download_id in self.active_downloads:
            return download_id
        
        thread = threading.Thread(
            target=self._download_audio_thread,
            args=(download_id, url, quality, output_path, progress_callback, completion_callback)
        )
        
        self.active_downloads[download_id] = {
            'thread': thread,
            'status': 'preparing',
            'progress': 0,
            'url': url,
            'quality': f"{quality} kbps",
            'type': 'audio'
        }
        
        thread.start()
        return download_id
    
    def _download_audio_thread(self, download_id, url, quality, output_path, progress_callback, completion_callback):
        """Thread تنزيل الصوت"""
        try:
            if not output_path:
                output_path = DOWNLOADS_DIR / "audio"
            
            Path(output_path).mkdir(parents=True, exist_ok=True)
            
            def progress_hook(d):
                if download_id not in self.active_downloads:
                    return
                
                if d['status'] == 'downloading':
                    downloaded = d.get('downloaded_bytes', 0)
                    total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                    
                    if total > 0:
                        progress = int((downloaded / total) * 100)
                        self.active_downloads[download_id]['progress'] = progress
                        
                        if progress_callback:
                            progress_callback(download_id, progress, downloaded, total)
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                'progress_hooks': [progress_hook],
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': quality,
                }],
                'noplaylist': True,
            }
            
            self.active_downloads[download_id]['status'] = 'downloading'
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                download_record = {
                    'title': info.get('title', 'صوت بدون عنوان'),
                    'url': url,
                    'quality': f"{quality} kbps",
                    'type': 'audio',
                    'status': 'completed'
                }
                
                self.download_history.append(download_record)
                
                if completion_callback:
                    completion_callback(download_id, True, download_record)
                
                notification_manager.notify(f"تم تنزيل الصوت: {download_record['title']}", "success")
                
        except Exception as e:
            error_msg = f"خطأ في تنزيل الصوت: {str(e)}"
            logger.error(error_msg)
            
            if completion_callback:
                completion_callback(download_id, False, error_msg)
            
            notification_manager.notify(error_msg, "error")
        
        finally:
            if download_id in self.active_downloads:
                del self.active_downloads[download_id]
    
    def pause_download(self, download_id):
        """إيقاف مؤقت للتنزيل"""
        if download_id in self.active_downloads:
            self.active_downloads[download_id]['paused'] = True
            return True
        return False
    
    def resume_download(self, download_id):
        """استئناف التنزيل"""
        if download_id in self.active_downloads:
            self.active_downloads[download_id]['paused'] = False
            return True
        return False
    
    def cancel_download(self, download_id):
        """إلغاء التنزيل"""
        if download_id in self.active_downloads:
            del self.active_downloads[download_id]
            return True
        return False
    
    def get_download_status(self, download_id):
        """الحصول على حالة التنزيل"""
        return self.active_downloads.get(download_id)
    
    def get_all_downloads(self):
        """الحصول على جميع التنزيلات النشطة"""
        return self.active_downloads.copy()

class VideoConverter:
    """فئة تحويل الفيديوهات"""
    
    def __init__(self):
        self.active_conversions = {}
    
    def video_to_audio(self, video_path, output_path=None, quality="192", progress_callback=None, completion_callback=None):
        """تحويل فيديو إلى صوت"""
        conversion_id = str(hash(video_path + str(quality)))
        
        if conversion_id in self.active_conversions:
            return conversion_id
        
        thread = threading.Thread(
            target=self._convert_thread,
            args=(conversion_id, video_path, output_path, quality, progress_callback, completion_callback)
        )
        
        self.active_conversions[conversion_id] = {
            'thread': thread,
            'status': 'preparing',
            'progress': 0,
            'input_file': video_path
        }
        
        thread.start()
        return conversion_id
    
    def _convert_thread(self, conversion_id, video_path, output_path, quality, progress_callback, completion_callback):
        """Thread تحويل الفيديو"""
        try:
            if not output_path:
                output_path = Path(video_path).parent / "audio" / f"{Path(video_path).stem}.mp3"
            
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            self.active_conversions[conversion_id]['status'] = 'converting'
            
            # تحويل باستخدام moviepy
            video = VideoFileClip(video_path)
            audio = video.audio
            
            def progress_callback_wrapper(get_progress):
                try:
                    if conversion_id in self.active_conversions:
                        progress = int(get_progress * 100)
                        self.active_conversions[conversion_id]['progress'] = progress
                        
                        if progress_callback:
                            progress_callback(conversion_id, progress)
                except:
                    pass
            
            # حفظ الصوت
            audio.write_audiofile(
                str(output_path),
                bitrate=f"{quality}k",
                verbose=False,
                logger=None
            )
            
            # تنظيف
            audio.close()
            video.close()
            
            self.active_conversions[conversion_id]['status'] = 'completed'
            self.active_conversions[conversion_id]['output_file'] = str(output_path)
            
            if completion_callback:
                completion_callback(conversion_id, True, str(output_path))
            
            notification_manager.notify("تم التحويل بنجاح", "success")
            
        except Exception as e:
            error_msg = f"خطأ في التحويل: {str(e)}"
            logger.error(error_msg)
            
            if completion_callback:
                completion_callback(conversion_id, False, error_msg)
            
            notification_manager.notify(error_msg, "error")
        
        finally:
            if conversion_id in self.active_conversions:
                del self.active_conversions[conversion_id]

# إنشاء كائنات عامة
video_downloader = VideoDownloader()
video_converter = VideoConverter()