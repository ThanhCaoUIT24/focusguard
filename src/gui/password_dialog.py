"""
Dialog xác thực mật khẩu
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QMessageBox, QCheckBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from pathlib import Path
import sys

# Thêm thư mục src vào path
current_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(current_dir))

from src.core.password_manager import PasswordManager

class PasswordDialog(QDialog):
    """Dialog xác thực mật khẩu"""
    
    def __init__(self, password_manager: PasswordManager, title="Xác thực mật khẩu", parent=None):
        super().__init__(parent)
        self.password_manager = password_manager
        self.title = title
        self.setup_ui()
        self.update_lockout_status()
        
        # Timer để cập nhật trạng thái khóa
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_lockout_status)
        self.timer.start(1000)  # Cập nhật mỗi giây
        
    def setup_ui(self):
        """Thiết lập giao diện"""
        self.setWindowTitle(self.title)
        self.setFixedSize(350, 200)
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Tiêu đề
        title_label = QLabel("🔐 " + self.title)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Thông tin trạng thái
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Nhập mật khẩu
        self.password_label = QLabel("Mật khẩu:")
        layout.addWidget(self.password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Nhập mật khẩu")
        layout.addWidget(self.password_input)
        
        # Checkbox hiển thị mật khẩu
        self.show_password_cb = QCheckBox("Hiển thị mật khẩu")
        self.show_password_cb.toggled.connect(self.toggle_password_visibility)
        layout.addWidget(self.show_password_cb)
        
        # Nút bấm
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Hủy")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.verify_btn = QPushButton("Xác thực")
        self.verify_btn.clicked.connect(self.verify_password)
        self.verify_btn.setDefault(True)
        button_layout.addWidget(self.verify_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Focus vào ô nhập mật khẩu
        self.password_input.setFocus()
        
        # Kết nối Enter key
        self.password_input.returnPressed.connect(self.verify_password)
    
    def toggle_password_visibility(self, checked):
        """Bật/tắt hiển thị mật khẩu"""
        if checked:
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
    
    def update_lockout_status(self):
        """Cập nhật trạng thái khóa"""
        if self.password_manager.is_locked_out():
            remaining = self.password_manager.get_lockout_remaining()
            minutes = remaining // 60
            seconds = remaining % 60
            
            self.status_label.setText(
                f"⚠️ Tài khoản bị khóa!\n"
                f"Thời gian còn lại: {minutes:02d}:{seconds:02d}"
            )
            self.status_label.setStyleSheet("color: red;")
            self.password_input.setEnabled(False)
            self.verify_btn.setEnabled(False)
            
            if remaining <= 0:
                # Hết thời gian khóa
                self.status_label.setText("")
                self.status_label.setStyleSheet("")
                self.password_input.setEnabled(True)
                self.verify_btn.setEnabled(True)
                self.password_input.setFocus()
        else:
            remaining_attempts = self.password_manager.get_remaining_attempts()
            if remaining_attempts < 3:
                self.status_label.setText(
                    f"⚠️ Còn {remaining_attempts} lần thử"
                )
                self.status_label.setStyleSheet("color: orange;")
            else:
                self.status_label.setText("")
                self.status_label.setStyleSheet("")
            
            self.password_input.setEnabled(True)
            self.verify_btn.setEnabled(True)
    
    def verify_password(self):
        """Xác thực mật khẩu"""
        if self.password_manager.is_locked_out():
            return
        
        password = self.password_input.text()
        
        if not password:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập mật khẩu!")
            return
        
        if self.password_manager.verify_password(password):
            self.accept()
        else:
            remaining = self.password_manager.get_remaining_attempts()
            
            if remaining > 0:
                QMessageBox.warning(
                    self,
                    "Mật khẩu sai",
                    f"Mật khẩu không đúng!\nCòn {remaining} lần thử."
                )
            else:
                QMessageBox.critical(
                    self,
                    "Tài khoản bị khóa",
                    "Bạn đã nhập sai mật khẩu quá nhiều lần.\n"
                    "Tài khoản sẽ bị khóa trong 5 phút."
                )
            
            self.password_input.clear()
            self.password_input.setFocus()
    
    def keyPressEvent(self, event):
        """Xử lý phím bấm"""
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Xử lý đóng dialog"""
        if hasattr(self, 'timer'):
            self.timer.stop()
        super().closeEvent(event)
