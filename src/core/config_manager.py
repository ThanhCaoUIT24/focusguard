"""
Quản lý cấu hình ứng dụng FocusGuard
Lưu trữ và đọc cài đặt từ file JSON
"""

import os
import json
from typing import Dict, List, Any
from pathlib import Path

class ConfigManager:
    """Quản lý cấu hình ứng dụng"""
    
    def __init__(self):
        # Đường dẫn thư mục cấu hình
        self.config_dir = Path.home() / ".config" / "focusguard"
        self.config_file = self.config_dir / "config.json"
        
        # Tạo thư mục nếu chưa tồn tại
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Cấu hình mặc định
        self.default_config = {
            "blocked_websites": [
                "facebook.com",
                "www.facebook.com",
                "twitter.com",
                "www.twitter.com",
                "instagram.com",
                "www.instagram.com",
                "youtube.com",
                "www.youtube.com",
                "tiktok.com",
                "www.tiktok.com",
                "reddit.com",
                "www.reddit.com"
            ],
            "default_focus_duration": 25,  # phút
            "strict_mode": False,
            "auto_start_break": True,
            "break_duration": 5,  # phút
            "notification_enabled": True,
            "sound_enabled": True,
            "theme": "light",
            "window_position": {"x": 100, "y": 100},
            "window_size": {"width": 800, "height": 600}
        }
        
        # Load cấu hình
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Đọc cấu hình từ file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Merge với default config để đảm bảo có đủ keys
                    merged_config = self.default_config.copy()
                    merged_config.update(config)
                    return merged_config
            else:
                # Tạo file config mới với cấu hình mặc định
                self.save_config(self.default_config)
                return self.default_config.copy()
        except (json.JSONDecodeError, IOError) as e:
            print(f"Lỗi đọc file cấu hình: {e}")
            return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any] = None):
        """Lưu cấu hình vào file"""
        try:
            config_to_save = config if config is not None else self.config
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Lỗi lưu file cấu hình: {e}")
    
    def get(self, key: str, default=None):
        """Lấy giá trị cấu hình"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Đặt giá trị cấu hình"""
        self.config[key] = value
        self.save_config()
    
    def get_blocked_websites(self) -> List[str]:
        """Lấy danh sách website bị chặn"""
        return self.config.get("blocked_websites", [])
    
    def add_blocked_website(self, website: str):
        """Thêm website vào danh sách chặn"""
        blocked_sites = self.get_blocked_websites()
        if website not in blocked_sites:
            blocked_sites.append(website)
            self.set("blocked_websites", blocked_sites)
    
    def remove_blocked_website(self, website: str):
        """Xóa website khỏi danh sách chặn"""
        blocked_sites = self.get_blocked_websites()
        if website in blocked_sites:
            blocked_sites.remove(website)
            self.set("blocked_websites", blocked_sites)
    
    def get_focus_duration(self) -> int:
        """Lấy thời gian tập trung mặc định (phút)"""
        return self.config.get("default_focus_duration", 25)
    
    def set_focus_duration(self, duration: int):
        """Đặt thời gian tập trung mặc định"""
        self.set("default_focus_duration", duration)
    
    def is_strict_mode(self) -> bool:
        """Kiểm tra có bật chế độ nghiêm khắc không"""
        return self.config.get("strict_mode", False)
    
    def set_strict_mode(self, enabled: bool):
        """Bật/tắt chế độ nghiêm khắc"""
        self.set("strict_mode", enabled)
    
    def get_backup_hosts_path(self) -> Path:
        """Lấy đường dẫn backup file hosts"""
        return self.config_dir / "hosts_backup"
    
    def get_data_dir(self) -> Path:
        """Lấy thư mục dữ liệu"""
        return self.config_dir
