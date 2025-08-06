"""
Quản lý chặn website thông qua file /etc/hosts
Backup và khôi phục file hosts gốc
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

class WebsiteBlocker:
    """Quản lý chặn website"""
    
    def __init__(self, backup_path: Path):
        self.hosts_file = Path("/etc/hosts")
        self.backup_path = backup_path
        self.block_marker_start = "# === FOCUSGUARD BLOCK START ==="
        self.block_marker_end = "# === FOCUSGUARD BLOCK END ==="
        
    def has_sudo_access(self) -> bool:
        """Kiểm tra có quyền sudo không"""
        try:
            # Kiểm tra bằng cách thử ghi vào /etc/hosts
            result = subprocess.run(
                ["sudo", "-n", "test", "-w", "/etc/hosts"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def backup_hosts_file(self) -> bool:
        """Backup file hosts gốc"""
        try:
            if not self.backup_path.exists():
                shutil.copy2(self.hosts_file, self.backup_path)
                print(f"Đã backup hosts file tới {self.backup_path}")
            return True
        except Exception as e:
            print(f"Lỗi backup hosts file: {e}")
            return False
    
    def restore_hosts_file(self) -> bool:
        """Khôi phục file hosts từ backup"""
        try:
            if self.backup_path.exists():
                # Sử dụng sudo để copy file backup
                result = subprocess.run(
                    ["sudo", "cp", str(self.backup_path), str(self.hosts_file)],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    print("Đã khôi phục hosts file từ backup")
                    return True
                else:
                    print(f"Lỗi khôi phục hosts file: {result.stderr}")
                    return False
            else:
                print("Không tìm thấy file backup")
                return self.remove_block_entries()
        except Exception as e:
            print(f"Lỗi khôi phục hosts file: {e}")
            return False
    
    def add_block_entries(self, websites: List[str]) -> bool:
        """Thêm các entry chặn website vào hosts file"""
        try:
            # Backup trước khi sửa đổi
            if not self.backup_hosts_file():
                return False
            
            # Đọc nội dung hosts file hiện tại
            with open(self.hosts_file, 'r') as f:
                content = f.read()
            
            # Xóa các entry cũ nếu có
            content = self._remove_existing_blocks(content)
            
            # Tạo các entry chặn mới
            block_entries = [self.block_marker_start]
            for website in websites:
                # Chặn cả domain chính và www subdomain
                block_entries.append(f"127.0.0.1 {website}")
                if not website.startswith("www."):
                    block_entries.append(f"127.0.0.1 www.{website}")
            block_entries.append(self.block_marker_end)
            
            # Thêm vào cuối file
            if not content.endswith('\n'):
                content += '\n'
            content += '\n'.join(block_entries) + '\n'
            
            # Ghi file với sudo
            temp_file = "/tmp/focusguard_hosts"
            with open(temp_file, 'w') as f:
                f.write(content)
            
            result = subprocess.run(
                ["sudo", "cp", temp_file, str(self.hosts_file)],
                capture_output=True,
                text=True
            )
            
            # Xóa file temp
            try:
                os.remove(temp_file)
            except:
                pass
            
            if result.returncode == 0:
                print(f"Đã chặn {len(websites)} website")
                return True
            else:
                print(f"Lỗi ghi hosts file: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Lỗi thêm entry chặn: {e}")
            return False
    
    def remove_block_entries(self) -> bool:
        """Xóa các entry chặn khỏi hosts file"""
        try:
            # Đọc nội dung hosts file
            with open(self.hosts_file, 'r') as f:
                content = f.read()
            
            # Xóa các entry chặn
            new_content = self._remove_existing_blocks(content)
            
            # Ghi lại file nếu có thay đổi
            if new_content != content:
                temp_file = "/tmp/focusguard_hosts_clean"
                with open(temp_file, 'w') as f:
                    f.write(new_content)
                
                result = subprocess.run(
                    ["sudo", "cp", temp_file, str(self.hosts_file)],
                    capture_output=True,
                    text=True
                )
                
                # Xóa file temp
                try:
                    os.remove(temp_file)
                except:
                    pass
                
                if result.returncode == 0:
                    print("Đã xóa các entry chặn website")
                    return True
                else:
                    print(f"Lỗi ghi hosts file: {result.stderr}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"Lỗi xóa entry chặn: {e}")
            return False
    
    def _remove_existing_blocks(self, content: str) -> str:
        """Xóa các block FocusGuard có từ trước"""
        lines = content.split('\n')
        new_lines = []
        inside_block = False
        
        for line in lines:
            if line.strip() == self.block_marker_start:
                inside_block = True
                continue
            elif line.strip() == self.block_marker_end:
                inside_block = False
                continue
            elif not inside_block:
                new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def is_blocking_active(self) -> bool:
        """Kiểm tra có đang chặn website không"""
        try:
            with open(self.hosts_file, 'r') as f:
                content = f.read()
                return self.block_marker_start in content
        except:
            return False
    
    def get_blocked_websites_from_hosts(self) -> List[str]:
        """Lấy danh sách website đang bị chặn từ hosts file"""
        blocked_sites = []
        try:
            with open(self.hosts_file, 'r') as f:
                lines = f.readlines()
            
            inside_block = False
            for line in lines:
                line = line.strip()
                if line == self.block_marker_start:
                    inside_block = True
                    continue
                elif line == self.block_marker_end:
                    inside_block = False
                    continue
                elif inside_block and line.startswith("127.0.0.1"):
                    parts = line.split()
                    if len(parts) >= 2:
                        website = parts[1]
                        if not website.startswith("www."):
                            blocked_sites.append(website)
            
        except Exception as e:
            print(f"Lỗi đọc hosts file: {e}")
        
        return blocked_sites
