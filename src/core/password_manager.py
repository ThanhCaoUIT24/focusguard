"""
Quản lý mật khẩu bảo mật cho FocusGuard
Mã hóa, xác thực và quản lý khóa tài khoản
"""

import os
import bcrypt
import time
from pathlib import Path
from typing import Optional

class PasswordManager:
    """Quản lý mật khẩu và bảo mật"""
    
    def __init__(self):
        # Đường dẫn file lưu mật khẩu
        self.config_dir = Path.home() / ".config" / "focusguard"
        self.password_file = self.config_dir / "auth.hash"
        self.lockout_file = self.config_dir / "lockout.txt"
        
        # Tạo thư mục nếu chưa tồn tại
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Cấu hình bảo mật
        self.max_attempts = 3
        self.lockout_duration = 300  # 5 phút = 300 giây
        
        # Trạng thái khóa
        self._failed_attempts = 0
        self._lockout_until = 0
    
    def has_password(self) -> bool:
        """Kiểm tra đã có mật khẩu chưa"""
        return self.password_file.exists()
    
    def set_password(self, password: str) -> bool:
        """Đặt mật khẩu mới"""
        try:
            # Mã hóa mật khẩu
            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password_bytes, salt)
            
            # Lưu vào file
            with open(self.password_file, 'wb') as f:
                f.write(hashed)
            
            # Đặt quyền chỉ owner đọc được
            os.chmod(self.password_file, 0o600)
            
            return True
        except Exception as e:
            print(f"Lỗi đặt mật khẩu: {e}")
            return False
    
    def verify_password(self, password: str) -> bool:
        """Xác thực mật khẩu"""
        # Kiểm tra có bị khóa không
        if self.is_locked_out():
            return False
        
        try:
            # Đọc mật khẩu đã mã hóa
            with open(self.password_file, 'rb') as f:
                stored_hash = f.read()
            
            # Kiểm tra mật khẩu
            password_bytes = password.encode('utf-8')
            is_correct = bcrypt.checkpw(password_bytes, stored_hash)
            
            if is_correct:
                # Reset số lần thử sai
                self._failed_attempts = 0
                self._clear_lockout()
                return True
            else:
                # Tăng số lần thử sai
                self._failed_attempts += 1
                
                # Nếu đã thử sai quá nhiều lần
                if self._failed_attempts >= self.max_attempts:
                    self._lockout()
                
                return False
                
        except Exception as e:
            print(f"Lỗi xác thực mật khẩu: {e}")
            return False
    
    def is_locked_out(self) -> bool:
        """Kiểm tra có bị khóa không"""
        current_time = time.time()
        
        # Đọc thời gian khóa từ file
        if self.lockout_file.exists():
            try:
                with open(self.lockout_file, 'r') as f:
                    lockout_until = float(f.read().strip())
                    if current_time < lockout_until:
                        self._lockout_until = lockout_until
                        return True
                    else:
                        # Hết thời gian khóa
                        self._clear_lockout()
            except:
                pass
        
        return False
    
    def get_lockout_remaining(self) -> int:
        """Lấy thời gian còn lại của việc khóa (giây)"""
        if self.is_locked_out():
            return max(0, int(self._lockout_until - time.time()))
        return 0
    
    def get_failed_attempts(self) -> int:
        """Lấy số lần thử sai hiện tại"""
        return self._failed_attempts
    
    def get_remaining_attempts(self) -> int:
        """Lấy số lần thử còn lại"""
        return max(0, self.max_attempts - self._failed_attempts)
    
    def _lockout(self):
        """Khóa tài khoản"""
        self._lockout_until = time.time() + self.lockout_duration
        
        try:
            with open(self.lockout_file, 'w') as f:
                f.write(str(self._lockout_until))
        except Exception as e:
            print(f"Lỗi tạo file khóa: {e}")
    
    def _clear_lockout(self):
        """Xóa trạng thái khóa"""
        self._failed_attempts = 0
        self._lockout_until = 0
        
        if self.lockout_file.exists():
            try:
                os.remove(self.lockout_file)
            except Exception as e:
                print(f"Lỗi xóa file khóa: {e}")
    
    def change_password(self, old_password: str, new_password: str) -> bool:
        """Đổi mật khẩu"""
        if not self.verify_password(old_password):
            return False
        
        return self.set_password(new_password)
    
    def reset_password(self) -> bool:
        """Reset mật khẩu (xóa file mật khẩu)"""
        try:
            if self.password_file.exists():
                os.remove(self.password_file)
            self._clear_lockout()
            return True
        except Exception as e:
            print(f"Lỗi reset mật khẩu: {e}")
            return False
