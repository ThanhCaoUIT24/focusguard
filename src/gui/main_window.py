"""
Cửa sổ chính của FocusGuard
Giao diện timer, quản lý website, thống kê
"""

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QSpinBox, QListWidget, 
                            QLineEdit, QMessageBox, QTabWidget, QProgressBar,
                            QTextEdit, QCheckBox, QGroupBox, QGridLayout,
                            QSystemTrayIcon, QMenu, QAction, QSplitter)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QIcon, QPixmap
import subprocess

# Thêm thư mục src vào path
current_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(current_dir))

from src.core.config_manager import ConfigManager
from src.core.password_manager import PasswordManager
from src.core.website_blocker import WebsiteBlocker
from src.core.session_manager import SessionManager
from src.gui.password_dialog import PasswordDialog
from src.gui.statistics_widget import StatisticsWidget

class FocusTimer(QThread):
    """Thread timer cho phiên tập trung"""
    timeChanged = pyqtSignal(int)  # Thời gian còn lại (giây)
    finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.remaining_seconds = 0
        self.is_running = False
    
    def start_timer(self, duration_minutes):
        """Bắt đầu timer"""
        self.remaining_seconds = duration_minutes * 60
        self.is_running = True
        self.start()
    
    def stop_timer(self):
        """Dừng timer"""
        self.is_running = False
        self.quit()
        self.wait()
    
    def run(self):
        """Chạy timer"""
        while self.is_running and self.remaining_seconds > 0:
            self.timeChanged.emit(self.remaining_seconds)
            self.msleep(1000)  # Sleep 1 giây
            self.remaining_seconds -= 1
        
        if self.remaining_seconds <= 0:
            self.finished.emit()

class MainWindow(QMainWindow):
    """Cửa sổ chính của ứng dụng"""
    
    def __init__(self, config_manager: ConfigManager, password_manager: PasswordManager):
        super().__init__()
        
        self.config_manager = config_manager
        self.password_manager = password_manager
        self.website_blocker = WebsiteBlocker(config_manager.get_backup_hosts_path())
        self.session_manager = SessionManager(config_manager.get_data_dir())
        
        # Trạng thái phiên
        self.current_session_id = None
        self.is_focus_session_active = False
        self.focus_timer = FocusTimer()
        
        # Thiết lập UI
        self.setup_ui()
        self.setup_system_tray()
        self.setup_connections()
        
        # Khôi phục vị trí cửa sổ
        self.restore_window_position()
        
        # Kiểm tra phiên đang chạy
        self.check_existing_session()
    
    def setup_ui(self):
        """Thiết lập giao diện người dùng"""
        self.setWindowTitle("FocusGuard - Quản lý sự tập trung")
        self.setMinimumSize(900, 700)
        
        # Widget chính
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout chính
        main_layout = QHBoxLayout(central_widget)
        
        # Splitter để chia cửa sổ
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Panel bên trái - Timer và controls
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Panel bên phải - Tabs
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Đặt tỷ lệ split
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
    
    def create_left_panel(self):
        """Tạo panel bên trái với timer và controls"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(20)
        
        # === TIMER SECTION ===
        timer_group = QGroupBox("⏱️ Timer Tập Trung")
        timer_layout = QVBoxLayout(timer_group)
        
        # Hiển thị thời gian
        self.time_display = QLabel("25:00")
        time_font = QFont()
        time_font.setPointSize(48)
        time_font.setBold(True)
        self.time_display.setFont(time_font)
        self.time_display.setAlignment(Qt.AlignCenter)
        self.time_display.setStyleSheet("color: #2196F3; background: #f0f0f0; border-radius: 10px; padding: 20px;")
        timer_layout.addWidget(self.time_display)
        
        # Thanh tiến trình
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        timer_layout.addWidget(self.progress_bar)
        
        # Cài đặt thời gian
        time_setting_layout = QHBoxLayout()
        time_setting_layout.addWidget(QLabel("Thời lượng (phút):"))
        
        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setRange(1, 999)
        self.duration_spinbox.setValue(self.config_manager.get_focus_duration())
        time_setting_layout.addWidget(self.duration_spinbox)
        
        timer_layout.addLayout(time_setting_layout)
        
        # Nút điều khiển
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("🚀 Bắt đầu")
        self.start_btn.clicked.connect(self.start_focus_session)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹️ Dừng")
        self.stop_btn.clicked.connect(self.stop_focus_session)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        timer_layout.addLayout(control_layout)
        
        layout.addWidget(timer_group)
        
        # === STRICT MODE ===
        strict_group = QGroupBox("🔒 Chế độ nghiêm khắc")
        strict_layout = QVBoxLayout(strict_group)
        
        self.strict_mode_cb = QCheckBox("Bật chế độ nghiêm khắc")
        self.strict_mode_cb.setChecked(self.config_manager.is_strict_mode())
        self.strict_mode_cb.toggled.connect(self.toggle_strict_mode)
        strict_layout.addWidget(self.strict_mode_cb)
        
        strict_info = QLabel(
            "• Không thể dừng phiên sớm\n"
            "• Không thể thoát ứng dụng\n"  
            "• Tự khởi động lại nếu bị kill"
        )
        strict_info.setStyleSheet("color: gray; font-size: 11px;")
        strict_layout.addWidget(strict_info)
        
        layout.addWidget(strict_group)
        
        # === QUICK STATS ===
        stats_group = QGroupBox("📊 Thống kê hôm nay")
        stats_layout = QGridLayout(stats_group)
        
        today_stats = self.session_manager.get_today_stats()
        
        self.total_time_label = QLabel(f"{today_stats['total_focus_time']} phút")
        stats_layout.addWidget(QLabel("Tổng thời gian:"), 0, 0)
        stats_layout.addWidget(self.total_time_label, 0, 1)
        
        self.sessions_count_label = QLabel(str(today_stats['sessions_completed']))
        stats_layout.addWidget(QLabel("Phiên hoàn thành:"), 1, 0)
        stats_layout.addWidget(self.sessions_count_label, 1, 1)
        
        self.success_rate_label = QLabel(f"{today_stats['success_rate']:.1f}%")
        stats_layout.addWidget(QLabel("Tỷ lệ thành công:"), 2, 0)
        stats_layout.addWidget(self.success_rate_label, 2, 1)
        
        layout.addWidget(stats_group)
        
        # Spacer để đẩy tất cả lên trên
        layout.addStretch()
        
        return panel
    
    def create_right_panel(self):
        """Tạo panel bên phải với tabs"""
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Tab 1: Quản lý website
        website_tab = self.create_website_tab()
        self.tab_widget.addTab(website_tab, "🌐 Website")
        
        # Tab 2: Thống kê
        self.stats_widget = StatisticsWidget(self.session_manager)
        self.tab_widget.addTab(self.stats_widget, "📈 Thống kê")
        
        # Tab 3: Lịch sử
        history_tab = self.create_history_tab()
        self.tab_widget.addTab(history_tab, "📝 Lịch sử")
        
        # Tab 4: Cài đặt
        settings_tab = self.create_settings_tab()
        self.tab_widget.addTab(settings_tab, "⚙️ Cài đặt")
        
        return self.tab_widget
    
    def create_website_tab(self):
        """Tạo tab quản lý website"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Danh sách website bị chặn
        layout.addWidget(QLabel("📛 Danh sách website sẽ bị chặn:"))
        
        self.website_list = QListWidget()
        self.update_website_list()
        layout.addWidget(self.website_list)
        
        # Thêm website mới
        add_layout = QHBoxLayout()
        self.website_input = QLineEdit()
        self.website_input.setPlaceholderText("Nhập tên website (vd: facebook.com)")
        add_layout.addWidget(self.website_input)
        
        add_btn = QPushButton("➕ Thêm")
        add_btn.clicked.connect(self.add_website)
        add_layout.addWidget(add_btn)
        
        layout.addLayout(add_layout)
        
        # Nút xóa
        remove_btn = QPushButton("🗑️ Xóa website đã chọn")
        remove_btn.clicked.connect(self.remove_website)
        layout.addWidget(remove_btn)
        
        # Kết nối Enter key
        self.website_input.returnPressed.connect(self.add_website)
        
        return widget
    
    def create_history_tab(self):
        """Tạo tab lịch sử phiên"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel("📚 Lịch sử các phiên tập trung:"))
        
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.update_history_display()
        layout.addWidget(self.history_text)
        
        # Nút refresh
        refresh_btn = QPushButton("🔄 Cập nhật")
        refresh_btn.clicked.connect(self.update_history_display)
        layout.addWidget(refresh_btn)
        
        return widget
    
    def create_settings_tab(self):
        """Tạo tab cài đặt"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Đổi mật khẩu
        password_group = QGroupBox("🔐 Bảo mật")
        password_layout = QVBoxLayout(password_group)
        
        change_password_btn = QPushButton("Đổi mật khẩu")
        change_password_btn.clicked.connect(self.change_password)
        password_layout.addWidget(change_password_btn)
        
        layout.addWidget(password_group)
        
        # Kiểm tra quyền sudo
        sudo_group = QGroupBox("⚙️ Hệ thống")
        sudo_layout = QVBoxLayout(sudo_group)
        
        check_sudo_btn = QPushButton("Kiểm tra quyền sudo")
        check_sudo_btn.clicked.connect(self.check_sudo_permissions)
        sudo_layout.addWidget(check_sudo_btn)
        
        layout.addWidget(sudo_group)
        
        # Thông tin ứng dụng
        about_group = QGroupBox("ℹ️ Thông tin")
        about_layout = QVBoxLayout(about_group)
        
        about_text = QLabel(
            "FocusGuard v1.0.0\n"
            "Ứng dụng quản lý sự tập trung\n"
            "Phát triển cho Ubuntu/Linux\n\n"
            "© 2025 FocusGuard Team"
        )
        about_text.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(about_text)
        
        layout.addWidget(about_group)
        
        layout.addStretch()
        
        return widget
    
    def setup_system_tray(self):
        """Thiết lập system tray"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            
            # Menu tray
            tray_menu = QMenu()
            
            show_action = QAction("Hiển thị", self)
            show_action.triggered.connect(self.show)
            tray_menu.addAction(show_action)
            
            tray_menu.addSeparator()
            
            quit_action = QAction("Thoát", self)
            quit_action.triggered.connect(self.quit_application)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self.tray_icon_activated)
            
            # Icon (sử dụng icon mặc định tạm thời)
            self.tray_icon.setToolTip("FocusGuard")
            self.tray_icon.show()
    
    def setup_connections(self):
        """Thiết lập các kết nối signal/slot"""
        self.focus_timer.timeChanged.connect(self.update_timer_display)
        self.focus_timer.finished.connect(self.on_timer_finished)
    
    def restore_window_position(self):
        """Khôi phục vị trí cửa sổ"""
        pos = self.config_manager.get("window_position", {"x": 100, "y": 100})
        size = self.config_manager.get("window_size", {"width": 900, "height": 700})
        
        self.move(pos["x"], pos["y"])
        self.resize(size["width"], size["height"])
    
    def check_existing_session(self):
        """Kiểm tra phiên đang chạy"""
        current_session = self.session_manager.get_current_session()
        if current_session:
            # Có phiên đang chạy
            reply = QMessageBox.question(
                self,
                "Phiên đang chạy",
                "Có phiên tập trung đang chạy từ trước.\n"
                "Bạn có muốn tiếp tục phiên này không?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.resume_session(current_session)
            else:
                # Kết thúc phiên cũ
                self.session_manager.end_session(current_session['id'], completed=False, notes="Bị gián đoạn do khởi động lại app")
    
    def resume_session(self, session_info):
        """Tiếp tục phiên đang chạy"""
        self.current_session_id = session_info['id']
        self.is_focus_session_active = True
        
        # Tính thời gian còn lại
        from datetime import datetime
        elapsed = (datetime.now() - session_info['start_time']).total_seconds()
        planned_seconds = session_info['planned_duration'] * 60
        remaining_seconds = max(0, planned_seconds - elapsed)
        
        if remaining_seconds > 0:
            # Bắt đầu timer với thời gian còn lại
            self.focus_timer.remaining_seconds = int(remaining_seconds)
            self.focus_timer.is_running = True
            self.focus_timer.start()
            
            # Cập nhật UI
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(planned_seconds)
            
            # Bật chặn website
            if not self.website_blocker.add_block_entries(session_info['websites_blocked']):
                QMessageBox.warning(self, "Lỗi", "Không thể chặn website. Kiểm tra quyền sudo!")
        else:
            # Phiên đã hết thời gian
            self.on_timer_finished()
    
    # === TIMER METHODS ===
    
    def start_focus_session(self):
        """Bắt đầu phiên tập trung"""
        # Kiểm tra quyền sudo
        if not self.website_blocker.has_sudo_access():
            reply = QMessageBox.question(
                self,
                "Không có quyền sudo",
                "Ứng dụng cần quyền sudo để chặn website.\n"
                "Bạn có muốn tiếp tục mà không chặn website không?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
        
        duration = self.duration_spinbox.value()
        websites = self.config_manager.get_blocked_websites()
        
        # Tạo phiên mới
        self.current_session_id = self.session_manager.start_session(duration, websites)
        if self.current_session_id == -1:
            QMessageBox.critical(self, "Lỗi", "Không thể bắt đầu phiên tập trung!")
            return
        
        # Chặn website
        if self.website_blocker.has_sudo_access():
            if not self.website_blocker.add_block_entries(websites):
                QMessageBox.warning(self, "Lỗi", "Không thể chặn website!")
        
        # Bắt đầu timer
        self.focus_timer.start_timer(duration)
        self.is_focus_session_active = True
        
        # Cập nhật UI
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(duration * 60)
        
        # Lưu thời lượng mặc định
        self.config_manager.set_focus_duration(duration)
        
        QMessageBox.information(
            self,
            "Bắt đầu tập trung",
            f"Phiên tập trung {duration} phút đã bắt đầu!\n"
            "Website xao nhãng đã được chặn."
        )
    
    def stop_focus_session(self):
        """Dừng phiên tập trung"""
        if not self.is_focus_session_active:
            return
        
        # Kiểm tra chế độ nghiêm khắc
        if self.config_manager.is_strict_mode():
            # Yêu cầu mật khẩu
            dialog = PasswordDialog(self.password_manager, "Dừng phiên tập trung", self)
            if dialog.exec_() != dialog.Accepted:
                return
        
        # Dừng timer
        self.focus_timer.stop_timer()
        
        # Kết thúc phiên
        if self.current_session_id:
            self.session_manager.end_session(
                self.current_session_id, 
                completed=False, 
                notes="Dừng sớm bởi người dùng"
            )
        
        # Tắt chặn website
        self.website_blocker.remove_block_entries()
        
        # Cập nhật UI
        self.reset_ui_after_session()
        
        QMessageBox.information(self, "Dừng phiên", "Phiên tập trung đã được dừng.")
    
    def on_timer_finished(self):
        """Xử lý khi timer kết thúc"""
        # Kết thúc phiên
        if self.current_session_id:
            self.session_manager.end_session(
                self.current_session_id,
                completed=True,
                notes="Hoàn thành đầy đủ"
            )
        
        # Tắt chặn website
        self.website_blocker.remove_block_entries()
        
        # Cập nhật UI
        self.reset_ui_after_session()
        
        # Cập nhật thống kê
        self.update_today_stats()
        
        # Thông báo hoàn thành
        QMessageBox.information(
            self,
            "🎉 Hoàn thành!",
            "Chúc mừng! Bạn đã hoàn thành phiên tập trung.\n"
            "Các trang web đã được mở khóa."
        )
    
    def reset_ui_after_session(self):
        """Reset UI sau khi kết thúc phiên"""
        self.is_focus_session_active = False
        self.current_session_id = None
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        # Reset hiển thị thời gian
        duration = self.duration_spinbox.value()
        self.time_display.setText(f"{duration:02d}:00")
    
    def update_timer_display(self, remaining_seconds):
        """Cập nhật hiển thị timer"""
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        self.time_display.setText(f"{minutes:02d}:{seconds:02d}")
        
        # Cập nhật thanh tiến trình
        if self.progress_bar.isVisible():
            total_seconds = self.progress_bar.maximum()
            progress = total_seconds - remaining_seconds
            self.progress_bar.setValue(progress)
    
    # === WEBSITE MANAGEMENT ===
    
    def update_website_list(self):
        """Cập nhật danh sách website"""
        self.website_list.clear()
        websites = self.config_manager.get_blocked_websites()
        self.website_list.addItems(websites)
    
    def add_website(self):
        """Thêm website vào danh sách chặn"""
        website = self.website_input.text().strip().lower()
        
        if not website:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên website!")
            return
        
        # Xóa http:// https:// nếu có
        website = website.replace("http://", "").replace("https://", "")
        website = website.replace("www.", "")  # Cũng xóa www. để chuẩn hóa
        
        if website in self.config_manager.get_blocked_websites():
            QMessageBox.information(self, "Thông báo", "Website này đã có trong danh sách!")
            return
        
        self.config_manager.add_blocked_website(website)
        self.update_website_list()
        self.website_input.clear()
    
    def remove_website(self):
        """Xóa website khỏi danh sách"""
        current_item = self.website_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn website cần xóa!")
            return
        
        website = current_item.text()
        reply = QMessageBox.question(
            self,
            "Xác nhận",
            f"Bạn có chắc muốn xóa '{website}' khỏi danh sách chặn?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.config_manager.remove_blocked_website(website)
            self.update_website_list()
    
    # === SETTINGS ===
    
    def toggle_strict_mode(self, checked):
        """Bật/tắt chế độ nghiêm khắc"""
        self.config_manager.set_strict_mode(checked)
        
        if checked:
            QMessageBox.information(
                self,
                "Chế độ nghiêm khắc",
                "Đã bật chế độ nghiêm khắc!\n"
                "Trong phiên tập trung, bạn sẽ không thể:\n"
                "• Dừng phiên sớm mà không nhập mật khẩu\n"
                "• Thoát ứng dụng\n"
                "• Kill ứng dụng từ terminal"
            )
    
    def change_password(self):
        """Đổi mật khẩu"""
        # Xác thực mật khẩu cũ
        dialog = PasswordDialog(self.password_manager, "Xác thực mật khẩu cũ", self)
        if dialog.exec_() != dialog.Accepted:
            return
        
        # Nhập mật khẩu mới (tương tự setup dialog)
        from src.gui.setup_dialog import SetupDialog
        setup_dialog = SetupDialog(self)
        setup_dialog.setWindowTitle("Đổi mật khẩu")
        
        if setup_dialog.exec_() == setup_dialog.Accepted:
            QMessageBox.information(self, "Thành công", "Mật khẩu đã được thay đổi!")
    
    def check_sudo_permissions(self):
        """Kiểm tra quyền sudo"""
        if self.website_blocker.has_sudo_access():
            QMessageBox.information(
                self,
                "Quyền sudo",
                "✅ Ứng dụng có quyền sudo.\n"
                "Có thể chặn website thành công."
            )
        else:
            QMessageBox.warning(
                self,
                "Quyền sudo",
                "❌ Ứng dụng không có quyền sudo.\n"
                "Cần chạy lệnh sau trong terminal:\n\n"
                "sudo visudo\n\n"
                "Và thêm dòng:\n"
                f"{os.getenv('USER')} ALL=(ALL) NOPASSWD: /bin/cp, /usr/bin/test"
            )
    
    # === HISTORY & STATS ===
    
    def update_history_display(self):
        """Cập nhật hiển thị lịch sử"""
        sessions = self.session_manager.get_recent_sessions(20)
        
        html = "<html><body>"
        html += "<h3>📚 Lịch sử phiên tập trung</h3>"
        
        if not sessions:
            html += "<p>Chưa có phiên nào được hoàn thành.</p>"
        else:
            for session in sessions:
                start_time = session['start_time']
                duration = session['actual_duration']
                status = "✅ Hoàn thành" if session['completed'] else "❌ Gián đoạn"
                
                html += f"""
                <div style='border: 1px solid #ddd; margin: 5px; padding: 10px; border-radius: 5px;'>
                    <strong>Phiên #{session['id']}</strong><br>
                    <strong>Thời gian:</strong> {start_time}<br>
                    <strong>Thời lượng:</strong> {duration} phút<br>
                    <strong>Trạng thái:</strong> {status}<br>
                    <strong>Ghi chú:</strong> {session['notes'] or 'Không có'}
                </div>
                """
        
        html += "</body></html>"
        self.history_text.setHtml(html)
    
    def update_today_stats(self):
        """Cập nhật thống kê hôm nay"""
        today_stats = self.session_manager.get_today_stats()
        
        self.total_time_label.setText(f"{today_stats['total_focus_time']} phút")
        self.sessions_count_label.setText(str(today_stats['sessions_completed']))
        self.success_rate_label.setText(f"{today_stats['success_rate']:.1f}%")
        
        # Cập nhật stats widget
        if hasattr(self, 'stats_widget'):
            self.stats_widget.refresh_stats()
    
    # === WINDOW EVENTS ===
    
    def tray_icon_activated(self, reason):
        """Xử lý click vào system tray"""
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()
    
    def closeEvent(self, event):
        """Xử lý đóng cửa sổ"""
        if self.is_focus_session_active and self.config_manager.is_strict_mode():
            # Chế độ nghiêm khắc - yêu cầu mật khẩu
            dialog = PasswordDialog(self.password_manager, "Thoát ứng dụng", self)
            if dialog.exec_() != dialog.Accepted:
                event.ignore()
                return
        
        # Ẩn vào system tray thay vì thoát
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            self.quit_application()
    
    def quit_application(self):
        """Thoát ứng dụng hoàn toàn"""
        # Lưu vị trí cửa sổ
        pos = self.pos()
        size = self.size()
        self.config_manager.set("window_position", {"x": pos.x(), "y": pos.y()})
        self.config_manager.set("window_size", {"width": size.width(), "height": size.height()})
        
        # Dừng phiên nếu đang chạy
        if self.is_focus_session_active:
            self.focus_timer.stop_timer()
            if self.current_session_id:
                self.session_manager.end_session(
                    self.current_session_id,
                    completed=False,
                    notes="Thoát ứng dụng"
                )
            self.website_blocker.remove_block_entries()
        
        # Thoát ứng dụng
        from PyQt5.QtWidgets import QApplication
        QApplication.quit()
