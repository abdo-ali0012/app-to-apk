"""
التطبيق الرئيسي - SnapTube Pro
تطبيق لتنزيل مقاطع الفيديو والصوت من منصات مختلفة
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
from pathlib import Path
import webbrowser
import threading
from PIL import Image, ImageTk

from config import *
from utils import *
from downloader import video_downloader, video_converter
from media_player import create_media_player

# إعداد المظهر
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class SnapTubeApp:
    """التطبيق الرئيسي"""
    
    def __init__(self):
        self.setup_window()
        self.setup_variables()
        self.setup_ui()
        self.setup_callbacks()
        
        # كائنات التطبيق
        self.media_player = None
        self.current_video_info = None
        
        # إشعارات
        notification_manager.add_callback(self.show_notification)
        
        logger.info("تم تشغيل SnapTube Pro")
    
    def setup_window(self):
        """إعداد النافذة الرئيسية"""
        self.root = ctk.CTk()
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry(WINDOW_SIZE)
        self.root.minsize(900, 600)
        
        # أيقونة التطبيق (إذا وجدت)
        try:
            icon_path = ASSETS_DIR / "icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(icon_path)
        except:
            pass
    
    def setup_variables(self):
        """إعداد المتغيرات"""
        self.url_var = tk.StringVar()
        self.quality_var = tk.StringVar(value=DEFAULT_QUALITY)
        self.download_type_var = tk.StringVar(value="video")
        self.audio_quality_var = tk.StringVar(value="192")
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="جاهز")
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        # الشريط العلوي
        self.create_header()
        
        # المحتوى الرئيسي
        self.create_main_content()
        
        # الشريط السفلي
        self.create_footer()
        
        # إعداد التخطيط
        self.setup_layout()
    
    def create_header(self):
        """إنشاء الشريط العلوي"""
        self.header_frame = ctk.CTkFrame(self.root, height=80)
        
        # شعار التطبيق
        title_label = ctk.CTkLabel(
            self.header_frame,
            text=APP_NAME,
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=20)
        
        # أزرار الشريط العلوي
        header_buttons_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        header_buttons_frame.pack(side=tk.RIGHT, padx=20, pady=20)
        
        # زر المشغل
        self.player_btn = ctk.CTkButton(
            header_buttons_frame,
            text="🎵 المشغل",
            width=100,
            command=self.open_media_player
        )
        self.player_btn.pack(side=tk.LEFT, padx=5)
        
        # زر الإعدادات
        self.settings_btn = ctk.CTkButton(
            header_buttons_frame,
            text="⚙ الإعدادات",
            width=100,
            command=self.open_settings
        )
        self.settings_btn.pack(side=tk.LEFT, padx=5)
        
        # زر المساعدة
        self.help_btn = ctk.CTkButton(
            header_buttons_frame,
            text="❓ مساعدة",
            width=100,
            command=self.show_help
        )
        self.help_btn.pack(side=tk.LEFT, padx=5)
    
    def create_main_content(self):
        """إنشاء المحتوى الرئيسي"""
        # إطار المحتوى
        self.content_frame = ctk.CTkFrame(self.root)
        
        # إنشاء تبويبات
        self.tabview = ctk.CTkTabview(self.content_frame, width=1000, height=500)
        
        # تبويب التنزيل
        self.download_tab = self.tabview.add("📥 تنزيل")
        self.create_download_tab()
        
        # تبويب التحويل
        self.convert_tab = self.tabview.add("🔄 تحويل")
        self.create_convert_tab()
        
        # تبويب التنزيلات
        self.downloads_tab = self.tabview.add("📋 التنزيلات")
        self.create_downloads_tab()
        
        # تبويب المكتبة
        self.library_tab = self.tabview.add("📚 المكتبة")
        self.create_library_tab()
        
        self.tabview.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def create_download_tab(self):
        """إنشاء تبويب التنزيل"""
        # قسم إدخال الرابط
        url_frame = ctk.CTkFrame(self.download_tab)
        url_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ctk.CTkLabel(url_frame, text="رابط الفيديو:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor=tk.W, padx=10, pady=5)
        
        url_input_frame = ctk.CTkFrame(url_frame, fg_color="transparent")
        url_input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.url_entry = ctk.CTkEntry(
            url_input_frame,
            textvariable=self.url_var,
            placeholder_text="الصق رابط الفيديو هنا...",
            height=40,
            font=ctk.CTkFont(size=12)
        )
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # زر لصق
        paste_btn = ctk.CTkButton(
            url_input_frame,
            text="📋 لصق",
            width=80,
            command=self.paste_url
        )
        paste_btn.pack(side=tk.RIGHT, padx=5)
        
        # زر تحليل الرابط
        analyze_btn = ctk.CTkButton(
            url_input_frame,
            text="🔍 تحليل",
            width=80,
            command=self.analyze_url
        )
        analyze_btn.pack(side=tk.RIGHT, padx=5)
        
        # معلومات الفيديو
        self.info_frame = ctk.CTkFrame(self.download_tab)
        self.info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.info_label = ctk.CTkLabel(
            self.info_frame,
            text="أدخل رابط فيديو لعرض المعلومات",
            font=ctk.CTkFont(size=14),
            justify=tk.CENTER
        )
        self.info_label.pack(expand=True)
        
        # خيارات التنزيل
        options_frame = ctk.CTkFrame(self.download_tab)
        options_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # نوع التنزيل
        type_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        type_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ctk.CTkLabel(type_frame, text="نوع التنزيل:", font=ctk.CTkFont(weight="bold")).pack(side=tk.LEFT, padx=5)
        
        video_radio = ctk.CTkRadioButton(type_frame, text="فيديو", variable=self.download_type_var, value="video")
        video_radio.pack(side=tk.LEFT, padx=10)
        
        audio_radio = ctk.CTkRadioButton(type_frame, text="صوت فقط", variable=self.download_type_var, value="audio")
        audio_radio.pack(side=tk.LEFT, padx=10)
        
        # جودة الفيديو
        quality_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        quality_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ctk.CTkLabel(quality_frame, text="جودة الفيديو:", font=ctk.CTkFont(weight="bold")).pack(side=tk.LEFT, padx=5)
        
        self.quality_menu = ctk.CTkOptionMenu(
            quality_frame,
            variable=self.quality_var,
            values=list(SUPPORTED_QUALITIES.keys())
        )
        self.quality_menu.pack(side=tk.LEFT, padx=10)
        
        # جودة الصوت
        audio_quality_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        audio_quality_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ctk.CTkLabel(audio_quality_frame, text="جودة الصوت:", font=ctk.CTkFont(weight="bold")).pack(side=tk.LEFT, padx=5)
        
        self.audio_quality_menu = ctk.CTkOptionMenu(
            audio_quality_frame,
            variable=self.audio_quality_var,
            values=list(AUDIO_QUALITIES.keys())
        )
        self.audio_quality_menu.pack(side=tk.LEFT, padx=10)
        
        # زر التنزيل
        download_btn = ctk.CTkButton(
            options_frame,
            text="📥 تنزيل",
            height=40,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.start_download
        )
        download_btn.pack(pady=10)
    
    def create_convert_tab(self):
        """إنشاء تبويب التحويل"""
        # اختيار الملف
        file_frame = ctk.CTkFrame(self.convert_tab)
        file_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ctk.CTkLabel(file_frame, text="تحويل الفيديو إلى صوت", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        file_select_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        file_select_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.selected_file_var = tk.StringVar(value="لم يتم اختيار ملف")
        selected_file_label = ctk.CTkLabel(file_select_frame, textvariable=self.selected_file_var)
        selected_file_label.pack(side=tk.LEFT, padx=10)
        
        select_file_btn = ctk.CTkButton(
            file_select_frame,
            text="📁 اختيار ملف",
            command=self.select_video_file
        )
        select_file_btn.pack(side=tk.RIGHT, padx=10)
        
        # خيارات التحويل
        convert_options_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        convert_options_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ctk.CTkLabel(convert_options_frame, text="جودة الصوت:", font=ctk.CTkFont(weight="bold")).pack(side=tk.LEFT, padx=5)
        
        self.convert_quality_var = tk.StringVar(value="192")
        convert_quality_menu = ctk.CTkOptionMenu(
            convert_options_frame,
            variable=self.convert_quality_var,
            values=list(AUDIO_QUALITIES.keys())
        )
        convert_quality_menu.pack(side=tk.LEFT, padx=10)
        
        # زر التحويل
        convert_btn = ctk.CTkButton(
            file_frame,
            text="🔄 تحويل",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.start_conversion
        )
        convert_btn.pack(pady=10)
        
        # شريط تقدم التحويل
        self.convert_progress = ctk.CTkProgressBar(file_frame)
        self.convert_progress.pack(fill=tk.X, padx=10, pady=10)
        self.convert_progress.set(0)
    
    def create_downloads_tab(self):
        """إنشاء تبويب التنزيلات"""
        # قائمة التنزيلات النشطة
        active_frame = ctk.CTkFrame(self.downloads_tab)
        active_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(active_frame, text="التنزيلات النشطة", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # جدول التنزيلات
        self.downloads_tree = ttk.Treeview(
            active_frame,
            columns=("name", "progress", "speed", "status"),
            show="headings",
            height=10
        )
        
        self.downloads_tree.heading("name", text="اسم الملف")
        self.downloads_tree.heading("progress", text="التقدم")
        self.downloads_tree.heading("speed", text="السرعة")
        self.downloads_tree.heading("status", text="الحالة")
        
        self.downloads_tree.column("name", width=300)
        self.downloads_tree.column("progress", width=100)
        self.downloads_tree.column("speed", width=100)
        self.downloads_tree.column("status", width=100)
        
        self.downloads_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # أزرار التحكم
        control_frame = ctk.CTkFrame(active_frame, fg_color="transparent")
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        pause_btn = ctk.CTkButton(control_frame, text="⏸ إيقاف مؤقت", width=100)
        pause_btn.pack(side=tk.LEFT, padx=5)
        
        resume_btn = ctk.CTkButton(control_frame, text="▶ استئناف", width=100)
        resume_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = ctk.CTkButton(control_frame, text="❌ إلغاء", width=100)
        cancel_btn.pack(side=tk.LEFT, padx=5)
    
    def create_library_tab(self):
        """إنشاء تبويب المكتبة"""
        # مجلدات المكتبة
        folders_frame = ctk.CTkFrame(self.library_tab)
        folders_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ctk.CTkLabel(folders_frame, text="المكتبة", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # أزرار المجلدات
        buttons_frame = ctk.CTkFrame(folders_frame, fg_color="transparent")
        buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        videos_btn = ctk.CTkButton(buttons_frame, text="📹 الفيديوهات", command=lambda: self.open_folder("videos"))
        videos_btn.pack(side=tk.LEFT, padx=5)
        
        audio_btn = ctk.CTkButton(buttons_frame, text="🎵 الصوتيات", command=lambda: self.open_folder("audio"))
        audio_btn.pack(side=tk.LEFT, padx=5)
        
        downloads_btn = ctk.CTkButton(buttons_frame, text="📁 التنزيلات", command=lambda: self.open_folder("downloads"))
        downloads_btn.pack(side=tk.LEFT, padx=5)
        
        # قائمة الملفات
        files_frame = ctk.CTkFrame(self.library_tab)
        files_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.files_listbox = tk.Listbox(
            files_frame,
            font=("Arial", 11),
            bg="#212121",
            fg="#ffffff",
            selectbackground="#1f538d"
        )
        self.files_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.files_listbox.bind("<Double-Button-1>", self.play_selected_file)
        
        # تحديث قائمة الملفات
        self.refresh_file_list()
    
    def create_footer(self):
        """إنشاء الشريط السفلي"""
        self.footer_frame = ctk.CTkFrame(self.root, height=60)
        
        # شريط التقدم العام
        self.progress_bar = ctk.CTkProgressBar(self.footer_frame, width=300)
        self.progress_bar.pack(side=tk.LEFT, padx=20, pady=15)
        self.progress_bar.set(0)
        
        # حالة التطبيق
        self.status_label = ctk.CTkLabel(self.footer_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT, padx=10, pady=15)
        
        # معلومات إضافية
        info_frame = ctk.CTkFrame(self.footer_frame, fg_color="transparent")
        info_frame.pack(side=tk.RIGHT, padx=20, pady=15)
        
        version_label = ctk.CTkLabel(info_frame, text=f"الإصدار {APP_VERSION}")
        version_label.pack(side=tk.RIGHT)
    
    def setup_layout(self):
        """إعداد التخطيط"""
        self.header_frame.pack(fill=tk.X, padx=10, pady=5)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.footer_frame.pack(fill=tk.X, padx=10, pady=5)
    
    def setup_callbacks(self):
        """إعداد callbacks الأحداث"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # تحديث دوري للتنزيلات
        self.update_downloads_display()
    
    def paste_url(self):
        """لصق رابط من الحافظة"""
        try:
            clipboard_content = self.root.clipboard_get()
            if validate_url(clipboard_content):
                self.url_var.set(clipboard_content)
                self.analyze_url()
            else:
                self.show_notification("محتوى الحافظة ليس رابطاً صحيحاً", "warning")
        except:
            self.show_notification("لا يوجد محتوى في الحافظة", "warning")
    
    def analyze_url(self):
        """تحليل الرابط والحصول على معلومات الفيديو"""
        url = self.url_var.get().strip()
        
        if not validate_url(url):
            self.show_notification("الرابط غير صحيح", "error")
            return
        
        self.status_var.set("جاري تحليل الرابط...")
        self.info_label.configure(text="جاري الحصول على معلومات الفيديو...")
        
        def analyze_callback(video_info, error):
            if video_info:
                self.current_video_info = video_info
                self.display_video_info(video_info)
                self.status_var.set("جاهز للتنزيل")
            else:
                self.info_label.configure(text=f"خطأ: {error}")
                self.status_var.set("خطأ في التحليل")
        
        # تشغيل التحليل في thread منفصل
        threading.Thread(
            target=video_downloader.get_video_info,
            args=(url, analyze_callback),
            daemon=True
        ).start()
    
    def display_video_info(self, video_info):
        """عرض معلومات الفيديو"""
        info_text = f"""
📹 العنوان: {video_info['title']}
👤 القناة: {video_info['uploader']}
⏱ المدة: {format_duration(video_info['duration'])}
👁 المشاهدات: {video_info.get('view_count', 0):,}
🌐 المنصة: {video_info['platform']}

📋 الوصف:
{video_info['description'][:200]}{'...' if len(video_info['description']) > 200 else ''}
        """
        
        self.info_label.configure(
            text=info_text,
            justify=tk.LEFT,
            anchor="nw"
        )
    
    def start_download(self):
        """بدء التنزيل"""
        if not self.current_video_info:
            self.show_notification("يجب تحليل الرابط أولاً", "warning")
            return
        
        url = self.current_video_info['url']
        download_type = self.download_type_var.get()
        
        def progress_callback(download_id, progress, downloaded, total):
            self.progress_bar.set(progress / 100)
            size_info = f"{format_file_size(downloaded)} / {format_file_size(total)}"
            self.status_var.set(f"تنزيل: {progress}% - {size_info}")
        
        def completion_callback(download_id, success, result):
            if success:
                self.progress_bar.set(1)
                self.status_var.set("تم التنزيل بنجاح")
                self.show_notification(f"تم تنزيل: {result['title']}", "success")
                self.refresh_file_list()
            else:
                self.progress_bar.set(0)
                self.status_var.set("فشل التنزيل")
                self.show_notification(f"خطأ: {result}", "error")
        
        if download_type == "video":
            quality = self.quality_var.get()
            download_id = video_downloader.download_video(
                url, quality, 
                progress_callback=progress_callback,
                completion_callback=completion_callback
            )
        else:
            quality = AUDIO_QUALITIES[self.audio_quality_var.get()]
            download_id = video_downloader.download_audio(
                url, quality,
                progress_callback=progress_callback, 
                completion_callback=completion_callback
            )
        
        self.status_var.set("بدء التنزيل...")
    
    def select_video_file(self):
        """اختيار ملف فيديو للتحويل"""
        filetypes = [
            ("ملفات الفيديو", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm"),
            ("جميع الملفات", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="اختيار ملف فيديو للتحويل",
            filetypes=filetypes
        )
        
        if filename:
            self.selected_file_var.set(Path(filename).name)
            self.selected_video_path = filename
    
    def start_conversion(self):
        """بدء تحويل الفيديو إلى صوت"""
        if not hasattr(self, 'selected_video_path'):
            self.show_notification("يجب اختيار ملف فيديو أولاً", "warning")
            return
        
        quality = AUDIO_QUALITIES[self.convert_quality_var.get()]
        
        def progress_callback(conversion_id, progress):
            self.convert_progress.set(progress / 100)
        
        def completion_callback(conversion_id, success, result):
            if success:
                self.convert_progress.set(1)
                self.show_notification("تم التحويل بنجاح", "success")
                self.refresh_file_list()
            else:
                self.convert_progress.set(0)
                self.show_notification(f"خطأ في التحويل: {result}", "error")
        
        conversion_id = video_converter.video_to_audio(
            self.selected_video_path,
            quality=quality,
            progress_callback=progress_callback,
            completion_callback=completion_callback
        )
    
    def refresh_file_list(self):
        """تحديث قائمة الملفات"""
        self.files_listbox.delete(0, tk.END)
        
        # إضافة الملفات من مجلد التنزيلات
        try:
            for file_path in DOWNLOADS_DIR.rglob("*"):
                if file_path.is_file():
                    self.files_listbox.insert(tk.END, file_path.name)
        except Exception as e:
            logger.error(f"خطأ في تحديث قائمة الملفات: {e}")
    
    def open_folder(self, folder_type):
        """فتح مجلد"""
        if folder_type == "videos":
            folder_path = DOWNLOADS_DIR
        elif folder_type == "audio":
            folder_path = DOWNLOADS_DIR / "audio"
        else:
            folder_path = DOWNLOADS_DIR
        
        try:
            if folder_path.exists():
                os.startfile(folder_path)  # Windows
            else:
                folder_path.mkdir(parents=True, exist_ok=True)
                os.startfile(folder_path)
        except:
            try:
                webbrowser.open(f"file://{folder_path}")  # متعدد المنصات
            except:
                self.show_notification("لا يمكن فتح المجلد", "error")
    
    def play_selected_file(self, event):
        """تشغيل الملف المحدد"""
        selection = self.files_listbox.curselection()
        if selection:
            filename = self.files_listbox.get(selection[0])
            file_path = DOWNLOADS_DIR / filename
            
            if file_path.exists():
                if not self.media_player:
                    self.open_media_player()
                self.media_player.load_file(str(file_path))
    
    def open_media_player(self):
        """فتح مشغل الوسائط"""
        if not self.media_player:
            self.media_player = create_media_player(self.root)
        else:
            try:
                self.media_player.player_window.lift()
                self.media_player.player_window.focus()
            except:
                self.media_player = create_media_player(self.root)
    
    def open_settings(self):
        """فتح نافذة الإعدادات"""
        settings_window = SettingsWindow(self.root)
    
    def show_help(self):
        """عرض نافذة المساعدة"""
        help_window = HelpWindow(self.root)
    
    def update_downloads_display(self):
        """تحديث عرض التنزيلات"""
        # مسح العناصر الحالية
        for item in self.downloads_tree.get_children():
            self.downloads_tree.delete(item)
        
        # إضافة التنزيلات النشطة
        active_downloads = video_downloader.get_all_downloads()
        for download_id, download_info in active_downloads.items():
            self.downloads_tree.insert("", tk.END, values=(
                download_info.get('url', '')[:50],
                f"{download_info.get('progress', 0)}%",
                "تحديد...",  # السرعة
                download_info.get('status', 'غير معروف')
            ))
        
        # جدولة التحديث التالي
        self.root.after(2000, self.update_downloads_display)
    
    def show_notification(self, message, type="info"):
        """عرض إشعار"""
        colors = {
            "info": "#2196F3",
            "success": "#4CAF50", 
            "warning": "#FF9800",
            "error": "#F44336"
        }
        
        # إشعار مؤقت
        notification = ctk.CTkToplevel(self.root)
        notification.title("إشعار")
        notification.geometry("400x120")
        notification.configure(fg_color=colors.get(type, "#2196F3"))
        
        # جعل النافذة تظهر أعلى البقية
        notification.attributes("-topmost", True)
        
        # محتوى الإشعار
        ctk.CTkLabel(
            notification,
            text=message,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white",
            wraplength=350
        ).pack(expand=True)
        
        # إغلاق تلقائي بعد 3 ثواني
        notification.after(3000, notification.destroy)
        
        # تسجيل الرسالة
        logger.info(f"إشعار ({type}): {message}")
    
    def on_closing(self):
        """عند إغلاق التطبيق"""
        try:
            if self.media_player:
                self.media_player.close()
        except:
            pass
        
        logger.info("إغلاق SnapTube Pro")
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """تشغيل التطبيق"""
        self.root.mainloop()

class SettingsWindow:
    """نافذة الإعدادات"""
    
    def __init__(self, parent):
        self.parent = parent
        self.window = ctk.CTkToplevel(parent)
        self.window.title("الإعدادات")
        self.window.geometry("500x400")
        self.window.resizable(False, False)
        
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد واجهة الإعدادات"""
        # عنوان
        title = ctk.CTkLabel(self.window, text="إعدادات التطبيق", font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=20)
        
        # إعدادات التنزيل
        download_frame = ctk.CTkFrame(self.window)
        download_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ctk.CTkLabel(download_frame, text="إعدادات التنزيل", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        
        # مسار التنزيل
        path_frame = ctk.CTkFrame(download_frame, fg_color="transparent")
        path_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ctk.CTkLabel(path_frame, text="مجلد التنزيل:").pack(side=tk.LEFT)
        
        self.path_var = tk.StringVar(value=str(DOWNLOADS_DIR))
        path_entry = ctk.CTkEntry(path_frame, textvariable=self.path_var, width=250)
        path_entry.pack(side=tk.LEFT, padx=10)
        
        browse_btn = ctk.CTkButton(path_frame, text="تصفح", width=80, command=self.browse_folder)
        browse_btn.pack(side=tk.RIGHT)
        
        # عدد التنزيلات المتزامنة
        concurrent_frame = ctk.CTkFrame(download_frame, fg_color="transparent")
        concurrent_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ctk.CTkLabel(concurrent_frame, text="التنزيلات المتزامنة:").pack(side=tk.LEFT)
        
        self.concurrent_var = tk.StringVar(value="3")
        concurrent_entry = ctk.CTkEntry(concurrent_frame, textvariable=self.concurrent_var, width=60)
        concurrent_entry.pack(side=tk.LEFT, padx=10)
        
        # إعدادات المظهر
        theme_frame = ctk.CTkFrame(self.window)
        theme_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ctk.CTkLabel(theme_frame, text="إعدادات المظهر", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        
        # وضع المظهر
        appearance_frame = ctk.CTkFrame(theme_frame, fg_color="transparent")
        appearance_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ctk.CTkLabel(appearance_frame, text="وضع المظهر:").pack(side=tk.LEFT)
        
        self.appearance_var = tk.StringVar(value="dark")
        appearance_menu = ctk.CTkOptionMenu(
            appearance_frame,
            variable=self.appearance_var,
            values=["light", "dark", "system"],
            command=self.change_appearance
        )
        appearance_menu.pack(side=tk.LEFT, padx=10)
        
        # أزرار الحفظ والإلغاء
        buttons_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        buttons_frame.pack(fill=tk.X, padx=20, pady=20)
        
        save_btn = ctk.CTkButton(buttons_frame, text="حفظ", command=self.save_settings)
        save_btn.pack(side=tk.RIGHT, padx=5)
        
        cancel_btn = ctk.CTkButton(buttons_frame, text="إلغاء", command=self.window.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=5)
    
    def browse_folder(self):
        """تصفح مجلد التنزيل"""
        folder = filedialog.askdirectory(initialdir=str(DOWNLOADS_DIR))
        if folder:
            self.path_var.set(folder)
    
    def change_appearance(self, value):
        """تغيير مظهر التطبيق"""
        ctk.set_appearance_mode(value)
    
    def save_settings(self):
        """حفظ الإعدادات"""
        # حفظ الإعدادات باستخدام SettingsManager
        settings_manager.set("download_path", self.path_var.get())
        settings_manager.set("concurrent_downloads", int(self.concurrent_var.get()))
        settings_manager.set("theme", self.appearance_var.get())
        
        self.window.destroy()

class HelpWindow:
    """نافذة المساعدة"""
    
    def __init__(self, parent):
        self.parent = parent
        self.window = ctk.CTkToplevel(parent)
        self.window.title("مساعدة")
        self.window.geometry("600x500")
        
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد واجهة المساعدة"""
        # عنوان
        title = ctk.CTkLabel(self.window, text=f"مساعدة {APP_NAME}", font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=20)
        
        # محتوى المساعدة
        help_text = """
🎯 مرحباً بك في SnapTube Pro

📥 كيفية تنزيل الفيديوهات:
1. الصق رابط الفيديو في الحقل المخصص
2. اضغط "تحليل" للحصول على معلومات الفيديو
3. اختر جودة الفيديو أو الصوت المطلوبة
4. اضغط "تنزيل" لبدء العملية

🔄 تحويل الفيديو إلى صوت:
1. انتقل إلى تبويب "تحويل"
2. اختر ملف الفيديو من جهازك
3. حدد جودة الصوت المطلوبة
4. اضغط "تحويل"

🎵 تشغيل الملفات:
- استخدم المشغل المدمج لتشغيل الملفات المحملة
- انقر نقراً مزدوجاً على أي ملف في المكتبة

⚙️ الإعدادات:
- يمكنك تخصيص مجلد التنزيل
- تغيير عدد التنزيلات المتزامنة
- تبديل بين الوضع الليلي والنهاري

🌐 المنصات المدعومة:
YouTube, Facebook, Instagram, TikTok, Twitter, 
Vimeo, Dailymotion وأكثر من 50 موقع آخر

💡 نصائح:
- استخدم جودة أقل للتنزيل السريع
- تحقق من مساحة القرص الصلب قبل التنزيل
- يمكنك إيقاف واستئناف التنزيلات في أي وقت

📞 الدعم الفني:
إذا واجهت أي مشكلة، تحقق من ملف السجل في مجلد الإعدادات
        """
        
        help_label = ctk.CTkLabel(
            self.window,
            text=help_text,
            font=ctk.CTkFont(size=12),
            justify=tk.LEFT,
            anchor="nw"
        )
        help_label.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # زر الإغلاق
        close_btn = ctk.CTkButton(self.window, text="إغلاق", command=self.window.destroy)
        close_btn.pack(pady=20)

if __name__ == "__main__":
    # التحقق من المتطلبات
    try:
        import yt_dlp
        import moviepy
        import pygame
    except ImportError as e:
        print(f"خطأ: مكتبة مفقودة - {e}")
        print("يرجى تثبيت المتطلبات باستخدام: pip install -r requirements.txt")
        exit(1)
    
    # تشغيل التطبيق
    app = SnapTubeApp()
    app.run()