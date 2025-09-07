"""
مشغل الوسائط المدمج
"""
import os
import threading
import time
from pathlib import Path
import pygame
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from utils import logger, format_duration
from config import SUPPORTED_VIDEO_FORMATS, SUPPORTED_AUDIO_FORMATS

class MediaPlayer:
    """مشغل الوسائط المدمج"""
    
    def __init__(self, parent_window):
        self.parent = parent_window
        self.current_file = None
        self.is_playing = False
        self.is_paused = False
        self.position = 0
        self.duration = 0
        self.volume = 0.7
        
        # تهيئة pygame للصوت
        try:
            pygame.mixer.init()
            self.audio_available = True
        except:
            self.audio_available = False
            logger.warning("فشل تهيئة مشغل الصوت")
        
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد واجهة المشغل"""
        # النافذة الرئيسية للمشغل
        self.player_window = tk.Toplevel(self.parent)
        self.player_window.title("مشغل الوسائط - SnapTube Pro")
        self.player_window.geometry("800x600")
        self.player_window.configure(bg="#1e1e1e")
        
        # منطقة العرض
        self.video_frame = tk.Frame(self.player_window, bg="#000000", height=400)
        self.video_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # صورة العرض (للصوت أو عندما لا يوجد فيديو)
        self.display_label = tk.Label(
            self.video_frame,
            bg="#000000",
            fg="#ffffff",
            text="مشغل الوسائط\nاختر ملف للتشغيل",
            font=("Arial", 16),
            justify=tk.CENTER
        )
        self.display_label.pack(expand=True, fill=tk.BOTH)
        
        # شريط التحكم
        self.control_frame = tk.Frame(self.player_window, bg="#2d2d2d", height=80)
        self.control_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.control_frame.pack_propagate(False)
        
        # شريط التقدم
        self.progress_frame = tk.Frame(self.control_frame, bg="#2d2d2d")
        self.progress_frame.pack(fill=tk.X, pady=(10, 5))
        
        self.progress_var = tk.DoubleVar()
        self.progress_scale = ttk.Scale(
            self.progress_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.progress_var,
            command=self.on_seek
        )
        self.progress_scale.pack(fill=tk.X, padx=10)
        
        # معلومات الوقت
        self.time_frame = tk.Frame(self.control_frame, bg="#2d2d2d")
        self.time_frame.pack(fill=tk.X)
        
        self.time_label = tk.Label(
            self.time_frame,
            text="00:00 / 00:00",
            bg="#2d2d2d",
            fg="#ffffff",
            font=("Arial", 10)
        )
        self.time_label.pack(side=tk.LEFT, padx=10)
        
        # أزرار التحكم
        self.buttons_frame = tk.Frame(self.control_frame, bg="#2d2d2d")
        self.buttons_frame.pack(side=tk.RIGHT, padx=10)
        
        # زر التشغيل/الإيقاف
        self.play_button = tk.Button(
            self.buttons_frame,
            text="▶",
            font=("Arial", 14),
            bg="#4CAF50",
            fg="white",
            width=3,
            command=self.toggle_play_pause
        )
        self.play_button.pack(side=tk.LEFT, padx=2)
        
        # زر الإيقاف
        self.stop_button = tk.Button(
            self.buttons_frame,
            text="⏹",
            font=("Arial", 14),
            bg="#f44336",
            fg="white",
            width=3,
            command=self.stop
        )
        self.stop_button.pack(side=tk.LEFT, padx=2)
        
        # شريط الصوت
        self.volume_frame = tk.Frame(self.buttons_frame, bg="#2d2d2d")
        self.volume_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(self.volume_frame, text="🔊", bg="#2d2d2d", fg="white").pack(side=tk.LEFT)
        
        self.volume_var = tk.DoubleVar(value=self.volume * 100)
        self.volume_scale = ttk.Scale(
            self.volume_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            length=100,
            variable=self.volume_var,
            command=self.on_volume_change
        )
        self.volume_scale.pack(side=tk.LEFT, padx=5)
        
        # قائمة الملفات
        self.setup_file_list()
        
        # بدء thread المراقبة
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_playback, daemon=True)
        self.monitor_thread.start()
    
    def setup_file_list(self):
        """إعداد قائمة الملفات"""
        # نافذة قائمة التشغيل
        self.playlist_window = tk.Toplevel(self.player_window)
        self.playlist_window.title("قائمة التشغيل")
        self.playlist_window.geometry("300x400")
        self.playlist_window.configure(bg="#2d2d2d")
        
        # قائمة الملفات
        self.file_listbox = tk.Listbox(
            self.playlist_window,
            bg="#1e1e1e",
            fg="#ffffff",
            selectbackground="#4CAF50",
            font=("Arial", 10)
        )
        self.file_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.file_listbox.bind("<Double-Button-1>", self.on_file_select)
        
        # أزرار إدارة القائمة
        buttons_frame = tk.Frame(self.playlist_window, bg="#2d2d2d")
        buttons_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Button(
            buttons_frame,
            text="إضافة ملف",
            bg="#2196F3",
            fg="white",
            command=self.add_file
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            buttons_frame,
            text="حذف",
            bg="#f44336",
            fg="white",
            command=self.remove_file
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            buttons_frame,
            text="مسح الكل",
            bg="#FF9800",
            fg="white",
            command=self.clear_playlist
        ).pack(side=tk.LEFT, padx=5)
    
    def add_file(self):
        """إضافة ملف للقائمة"""
        from tkinter import filedialog
        
        filetypes = [
            ("جميع الملفات المدعومة", "*.mp4;*.avi;*.mov;*.mkv;*.mp3;*.wav;*.ogg"),
            ("ملفات الفيديو", "*.mp4;*.avi;*.mov;*.mkv;*.wmv;*.flv;*.webm"),
            ("ملفات الصوت", "*.mp3;*.wav;*.ogg;*.flac;*.aac;*.wma"),
            ("جميع الملفات", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="اختيار ملفات الوسائط",
            filetypes=filetypes
        )
        
        for file_path in files:
            filename = Path(file_path).name
            self.file_listbox.insert(tk.END, filename)
            # حفظ المسار الكامل كسمة
            self.file_listbox.insert(tk.END, file_path)
            self.file_listbox.delete(tk.END)  # حذف المسار المكرر
            
            # إضافة المسار كبيانات مخفية
            index = self.file_listbox.size() - 1
            self.file_listbox.insert(index, file_path)
            self.file_listbox.delete(index)
            self.file_listbox.insert(tk.END, filename)
    
    def remove_file(self):
        """حذف ملف من القائمة"""
        selection = self.file_listbox.curselection()
        if selection:
            self.file_listbox.delete(selection[0])
    
    def clear_playlist(self):
        """مسح قائمة التشغيل"""
        self.file_listbox.delete(0, tk.END)
    
    def on_file_select(self, event):
        """عند اختيار ملف من القائمة"""
        selection = self.file_listbox.curselection()
        if selection:
            filename = self.file_listbox.get(selection[0])
            # البحث عن المسار الكامل (يحتاج تحسين)
            # هذا مثال مبسط، في التطبيق الحقيقي نحتاج نظام أفضل
            from tkinter import messagebox
            messagebox.showinfo("تشغيل", f"سيتم تشغيل: {filename}")
    
    def load_file(self, file_path):
        """تحميل ملف وسائط"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError("الملف غير موجود")
            
            self.current_file = file_path
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext in SUPPORTED_AUDIO_FORMATS:
                self.load_audio(file_path)
            elif file_ext in SUPPORTED_VIDEO_FORMATS:
                self.load_video(file_path)
            else:
                raise ValueError("نوع الملف غير مدعوم")
            
            # تحديث واجهة المستخدم
            filename = Path(file_path).name
            self.display_label.config(text=f"جاري تحميل:\n{filename}")
            
        except Exception as e:
            logger.error(f"خطأ في تحميل الملف: {e}")
            self.display_label.config(text=f"خطأ في تحميل الملف:\n{str(e)}")
    
    def load_audio(self, audio_path):
        """تحميل ملف صوتي"""
        if not self.audio_available:
            raise Exception("مشغل الصوت غير متاح")
        
        try:
            pygame.mixer.music.load(audio_path)
            self.duration = self.get_audio_length(audio_path)
            self.is_playing = False
            self.position = 0
            
            # تحديث الواجهة للصوت
            filename = Path(audio_path).name
            self.display_label.config(
                text=f"🎵\n{filename}\n\nملف صوتي",
                font=("Arial", 14)
            )
            
        except Exception as e:
            raise Exception(f"فشل تحميل الملف الصوتي: {e}")
    
    def load_video(self, video_path):
        """تحميل ملف فيديو (مبسط)"""
        try:
            # للفيديو، نعرض فقط معلومات أساسية
            # في تطبيق حقيقي، نحتاج مكتبة تشغيل فيديو مثل opencv أو vlc
            filename = Path(video_path).name
            self.display_label.config(
                text=f"🎬\n{filename}\n\nملف فيديو\n(تشغيل الصوت فقط)",
                font=("Arial", 14)
            )
            
            # محاولة تشغيل الصوت من الفيديو
            # هذا مثال مبسط، في التطبيق الحقيقي نحتاج استخراج الصوت
            self.current_file = video_path
            
        except Exception as e:
            raise Exception(f"فشل تحميل الملف المرئي: {e}")
    
    def play(self):
        """تشغيل الوسائط"""
        if not self.current_file:
            return
        
        try:
            if self.audio_available:
                if self.is_paused:
                    pygame.mixer.music.unpause()
                else:
                    pygame.mixer.music.play(start=self.position)
                
                self.is_playing = True
                self.is_paused = False
                self.play_button.config(text="⏸", bg="#FF9800")
                
        except Exception as e:
            logger.error(f"خطأ في التشغيل: {e}")
    
    def pause(self):
        """إيقاف مؤقت"""
        if self.is_playing and self.audio_available:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.is_playing = False
            self.play_button.config(text="▶", bg="#4CAF50")
    
    def stop(self):
        """إيقاف التشغيل"""
        if self.audio_available:
            pygame.mixer.music.stop()
        
        self.is_playing = False
        self.is_paused = False
        self.position = 0
        self.progress_var.set(0)
        self.play_button.config(text="▶", bg="#4CAF50")
        self.time_label.config(text="00:00 / 00:00")
    
    def toggle_play_pause(self):
        """تبديل التشغيل/الإيقاف المؤقت"""
        if self.is_playing:
            self.pause()
        else:
            self.play()
    
    def on_seek(self, value):
        """عند تغيير موضع التشغيل"""
        if self.duration > 0:
            new_position = (float(value) / 100) * self.duration
            self.position = new_position
            # في تطبيق حقيقي، نحتاج تنفيذ seek للموضع الجديد
    
    def on_volume_change(self, value):
        """عند تغيير مستوى الصوت"""
        self.volume = float(value) / 100
        if self.audio_available:
            pygame.mixer.music.set_volume(self.volume)
    
    def get_audio_length(self, audio_path):
        """الحصول على مدة الملف الصوتي (مبسط)"""
        # في تطبيق حقيقي، نستخدم مكتبة مثل mutagen
        try:
            import wave
            with wave.open(audio_path, 'r') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration = frames / float(rate)
                return duration
        except:
            return 180  # قيمة افتراضية 3 دقائق
    
    def monitor_playback(self):
        """مراقبة حالة التشغيل"""
        while self.monitoring:
            try:
                if self.is_playing and not self.is_paused:
                    self.position += 1
                    
                    if self.duration > 0:
                        progress = (self.position / self.duration) * 100
                        self.progress_var.set(progress)
                        
                        current_time = format_duration(self.position)
                        total_time = format_duration(self.duration)
                        self.time_label.config(text=f"{current_time} / {total_time}")
                
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"خطأ في مراقبة التشغيل: {e}")
                time.sleep(1)
    
    def close(self):
        """إغلاق المشغل"""
        self.monitoring = False
        self.stop()
        
        try:
            self.playlist_window.destroy()
        except:
            pass
        
        try:
            self.player_window.destroy()
        except:
            pass

def create_media_player(parent):
    """إنشاء مشغل وسائط جديد"""
    return MediaPlayer(parent)