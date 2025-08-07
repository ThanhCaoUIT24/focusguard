#!/usr/bin/env python3
"""
FocusGuard - Ứng dụng quản lý sự tập trung cho Ubuntu/Linux
Chặn trang web xao nhãng trong thời gian tập trung
"""

import sys
import os
import signal
import psutil
from PyQt5.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon
from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtGui import QIcon

# Thêm thư mục src vào path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.gui.main_window import MainWindow
from src.core.config_manager import ConfigManager
from src.core.password_manager import PasswordManager

class FocusGuardApp(QApplication):
    """Ứng dụng chính FocusGuard"""
    
    def __init__(self, argv):
        super().__init__(argv)
        
        # Thiết lập ứng dụng
        self.setQuitOnLastWindowClosed(False)
        self.setApplicationName("FocusGuard")
        self.setApplicationVersion("1.0.0")
        
        # Khởi tạo các thành phần
        self.config_manager = ConfigManager()
        self.password_manager = PasswordManager()
        self.main_window = None
        
        # Kiểm tra instance duy nhất
        self.check_single_instance()
        
        # Thiết lập signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def check_single_instance(self):
        """Đảm bảo chỉ có một instance của app đang chạy"""
        app_name = "focusguard"
        current_pid = os.getpid()
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if (proc.info['name'] == 'python3' and 
                    proc.info['pid'] != current_pid and
                    any(app_name in str(cmd) for cmd in proc.info['cmdline'] or [])):
                    print("FocusGuard đã đang chạy!")
                    sys.exit(1)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    
    def signal_handler(self, signum, frame):
        """Xử lý signal để thoát ứng dụng một cách an toàn"""
        print(f"Nhận signal {signum}, đang thoát...")
        self.quit()
    
    def initialize(self):
        """Khởi tạo ứng dụng"""
        print("Initializing FocusGuard...")
        
        # Kiểm tra xem có cần setup không
        if not self.password_manager.has_password():
            print("Password not set, showing setup dialog...")
            from src.gui.setup_dialog import SetupDialog
            setup_dialog = SetupDialog()
            setup_dialog.show()
            setup_dialog.raise_()
            setup_dialog.activateWindow()
            if setup_dialog.exec_() != setup_dialog.Accepted:
                print("Setup dialog cancelled")
                return False
            print("Setup completed successfully")
        
        # Tạo cửa sổ chính
        print("Creating main window...")
        self.main_window = MainWindow(self.config_manager, self.password_manager)
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()
        print("Main window created and shown")
        
        return True

def main():
    """Hàm main của ứng dụng"""
    print("Starting FocusGuard application...")
    print(f"Display: {os.environ.get('DISPLAY', 'Not set')}")
    print(f"QT Platform: {os.environ.get('QT_QPA_PLATFORM', 'Not set')}")
    
    app = FocusGuardApp(sys.argv)
    print("Application created successfully")

    # Always clean up leftover blocks at startup
    try:
        from src.core.website_blocker import WebsiteBlocker
        blocker = WebsiteBlocker(app.config_manager.get_backup_hosts_path())
        if blocker.is_blocking_active():
            print("Cleaning up leftover website blocks from previous session...")
            blocker.remove_block_entries()
    except Exception as e:
        print(f"Error cleaning up hosts file: {e}")

    if not app.initialize():
        print("Failed to initialize application")
        return 1

    print("Application initialized, starting event loop...")
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
