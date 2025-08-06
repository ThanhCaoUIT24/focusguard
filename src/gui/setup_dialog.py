"""
Dialog thiết lập ban đầu cho FocusGuard
Tạo mật khẩu lần đầu tiên
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QMessageBox, QCheckBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
from pathlib import Path
import sys
import os

# Thêm thư mục src vào path
current_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(current_dir))

from src.core.password_manager import PasswordManager

class SetupDialog(QDialog):
    """Dialog thiết lập lần đầu"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.password_manager = PasswordManager()
        self.setup_ui()
        
    def setup_ui(self):
        """Thiết lập giao diện"""
        self.setWindowTitle("FocusGuard - Thiết lập ban đầu")
        self.setFixedSize(450, 400)  # Tăng kích thước dialog
        self.setModal(True)
        
        # Layout chính
        layout = QVBoxLayout()
        layout.setSpacing(15)  # Giảm spacing
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Tiêu đề
        title_label = QLabel("🔒 Chào mừng đến với FocusGuard!")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Mô tả
        desc_label = QLabel(
            "Để bảo vệ ứng dụng, bạn cần tạo một mật khẩu.\n"
            "Mật khẩu này sẽ được yêu cầu khi:\n"
            "• Dừng phiên tập trung sớm\n"
            "• Thoát ứng dụng trong khi đang tập trung\n"
            "• Thay đổi cài đặt quan trọng"
        )
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc_label)
        
        # Form nhập mật khẩu
        form_layout = QVBoxLayout()
        
        # Mật khẩu
        self.password_label = QLabel("Mật khẩu:")
        form_layout.addWidget(self.password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Nhập mật khẩu (tối thiểu 6 ký tự)")
        form_layout.addWidget(self.password_input)
        
        # Removed password confirmation field - user only needs to type password once
        
        layout.addLayout(form_layout)
        
        # Checkbox hiển thị mật khẩu
        self.show_password_cb = QCheckBox("Hiển thị mật khẩu")
        self.show_password_cb.toggled.connect(self.toggle_password_visibility)
        layout.addWidget(self.show_password_cb)
        
        # Nút bấm
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Hủy")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.create_btn = QPushButton("Tạo mật khẩu")
        self.create_btn.clicked.connect(self.create_password)
        self.create_btn.setDefault(True)
        button_layout.addWidget(self.create_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Focus vào ô nhập mật khẩu
        self.password_input.setFocus()
        
        # Kết nối Enter key
        self.password_input.returnPressed.connect(self.create_password)
    
    def toggle_password_visibility(self, checked):
        """Bật/tắt hiển thị mật khẩu"""
        if checked:
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
    
    def create_password(self):
        """Tạo mật khẩu mới"""
        password = self.password_input.text()
        
        # Kiểm tra độ dài
        if len(password) < 6:
            QMessageBox.warning(
                self,
                "Lỗi",
                "Mật khẩu phải có ít nhất 6 ký tự!"
            )
            self.password_input.setFocus()
            return
        
        # Tạo mật khẩu
        if self.password_manager.set_password(password):
            QMessageBox.information(
                self,
                "Thành công",
                "Mật khẩu đã được tạo thành công!\n"
                "Hãy ghi nhớ mật khẩu này để sử dụng ứng dụng."
            )
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Lỗi",
                "Không thể tạo mật khẩu. Vui lòng thử lại!"
            )
    
    def keyPressEvent(self, event):
        """Xử lý phím bấm"""
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
