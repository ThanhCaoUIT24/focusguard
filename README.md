# FocusGuard - Focus Management Application

![FocusGuard Logo](https://via.placeholder.com/200x80/2196F3/FFFFFF?text=FocusGuard)

## 📋 Description

FocusGuard is a powerful desktop application developed for Ubuntu/Linux that helps you manage focus and boost productivity. The application blocks distracting websites during focus sessions, features a secure password system, and provides detailed statistics about your work habits.

**🎯 Simple Version: Just one command to run!**

## ✨ Key Features

### 🔒 Security & Control
- **Password Protection**: bcrypt encryption, account lockout after 3 failed attempts
- **Simple Setup**: Only need to enter password once (no confirmation required)
- **Strict Mode**: Cannot stop session or exit application during focus time

### 🌐 Website Blocking
- **Automatic Blocking**: Modifies `/etc/hosts` file to block distracting websites
- **Safe Backup**: Automatically backs up and restores original hosts file
- **List Management**: Easily add/remove websites through the interface

### ⏱️ Timer & Sessions
- **Countdown Timer**: Clear display of remaining time
- **Progress Bar**: Track focus session progress
- **Flexible Settings**: Duration from 1-999 minutes

### 📊 Statistics & History
- **Daily Statistics**: Total time, completed sessions, success rate
- **7-Day Charts**: Visualize your focus habits
- **Session History**: Details of all completed sessions
- **SQLite Storage**: Safe data storage, no data loss

### 🎨 User-Friendly Interface
- **Modern UI**: Beautiful interface with PyQt5
- **System Tray**: Runs in background, doesn't occupy taskbar space
- **Responsive**: Auto-adjusts to window size

## 🔧 Yêu cầu hệ thống

### Hệ điều hành
- Ubuntu 20.04+ (hoặc các distro Linux tương tự)
- Python 3.8+

### Phần mềm phụ thuộc
- PyQt5
- bcrypt  
- matplotlib
- psutil
- sqlite3 (có sẵn trong Python)
## 🔧 System Requirements

### Operating System
- Ubuntu 20.04+ (or similar Linux distributions)
- Python 3.8+

### Software Dependencies
- PyQt5
- bcrypt  
- matplotlib
- psutil
- sqlite3 (included with Python)

### System Permissions
- Sudo access to modify `/etc/hosts` file

## 📦 Installation

### 🛠️ Install Dependencies
```bash
sudo apt update
sudo apt install python3 python3-pip python3-pyqt5 python3-bcrypt python3-matplotlib python3-psutil
```

### 📥 Download Project
```bash
# Clone repository or download ZIP
git clone https://github.com/your-username/focusguard.git
cd focusguard

# Or if you already have the folder
cd /path/to/focusguard
```

### 🔧 Install Python Packages (if needed)
```bash
pip3 install -r requirements.txt
```

## 🚀 Running the Application

### 🎯 Recommended Method (with sudo for website blocking)
```bash
cd /path/to/focusguard
sudo ./run_clean.sh
```

### 🔧 Alternative Method (with pkexec)
```bash
cd /path/to/focusguard
./run_pkexec.sh
```

### 🏃 Direct Method
```bash
cd /path/to/focusguard
python3 main.py
```

**Note**: To block websites, the application needs sudo access to modify the `/etc/hosts` file.

## � Cài đặt

### 🛠️ Cài đặt dependencies
```bash
sudo apt update
sudo apt install python3 python3-pip python3-pyqt5 python3-bcrypt python3-matplotlib python3-psutil
```

### 📥 Tải xuống dự án
```bash
# Clone repository hoặc download ZIP
git clone https://github.com/your-username/focusguard.git
cd focusguard

# Hoặc nếu đã có folder
cd /path/to/focusguard
```

### 🔧 Cài đặt Python packages (nếu cần)
```bash
pip3 install -r requirements.txt
```

## 🚀 Chạy ứng dụng

### 🎯 Cách khuyến khích (với sudo để chặn website)
```bash
cd /path/to/focusguard
sudo ./run_clean.sh
```

### � Cách thay thế (với pkexec)
```bash
cd /path/to/focusguard
./run_pkexec.sh
```

### 🏃 Chạy trực tiếp
```bash
cd /path/to/focusguard
python3 main.py
```

**Lưu ý**: Để chặn website được, ứng dụng cần quyền sudo để sửa đổi file `/etc/hosts`.
## 📖 User Guide

### First Launch
1. Run the application, system will prompt to create a password
2. Enter a strong password (minimum 6 characters) - **only need to enter once**
3. Application will start

### Starting a Focus Session
1. Select focus duration (minutes)
2. Check the list of websites to be blocked
3. Enable "Strict Mode" if desired
4. Click "🚀 Start"

### Managing Websites
1. Go to "🌐 Website" tab
2. Add new website in text box and click "➕ Add"
3. Select website from list and click "🗑️ Delete" to remove

### Viewing Statistics
1. "📈 Statistics" tab: View charts and overview
2. "📝 History" tab: View details of completed sessions

## 🔐 Security

### Password
- Encrypted with bcrypt using random salt
- Account locked for 5 minutes after 3 failed attempts
- Password file has 600 permissions (only owner can read)
- **Simple setup**: Only need to enter once, no confirmation required

### Configuration Files
All data is stored in `~/.config/focusguard/`:
- `config.json`: Application settings
- `auth.hash`: Encrypted password
- `sessions.db`: SQLite database
- `hosts_backup`: Original hosts file backup

## 🛠️ Project Structure

```
focusguard/
├── main.py                 # Main entry point
├── run_clean.sh           # Launch script with sudo (recommended)
├── run_pkexec.sh          # Launch script with pkexec
├── requirements.txt       # Python dependencies
├── README.md              # This document
├── LICENSE                # MIT License
└── src/                   # Main source code
    ├── __init__.py
    ├── core/              # Core logic
    │   ├── __init__.py
    │   ├── config_manager.py    # Configuration management
    │   ├── password_manager.py  # Password management
    │   ├── session_manager.py   # Session management
    │   └── website_blocker.py   # Website blocking
    └── gui/               # User interface
        ├── __init__.py
        ├── main_window.py       # Main window
        ├── setup_dialog.py      # Setup dialog
        ├── password_dialog.py   # Password dialog
        └── statistics_widget.py # Statistics widget
```

## 🐛 Troubleshooting

### Installation Errors
**"qt.qpa.plugin: Could not load the Qt platform plugin 'xcb'"**
```bash
# Use system PyQt5 instead of pip
sudo apt install python3-pyqt5
./run_clean.sh
```

**"Permission denied" when blocking websites**
- Make sure to run with sudo: `sudo ./run_clean.sh`
- Or use pkexec: `./run_pkexec.sh`

**"ModuleNotFoundError" during import**
```bash
# Install dependencies
pip3 install -r requirements.txt
```

### Runtime Errors
**Application doesn't show icon in system tray**
- Ensure your DE supports system tray
- For GNOME: install TopIcons Plus extension

**Forgot password**
- Delete file `~/.config/focusguard/auth.hash`
- Restart application to create new password

**Websites still accessible despite being blocked**
- Check sudo permissions
- Some browsers cache DNS, restart browser
- Check if `/etc/hosts` file has FocusGuard entries

### Configure sudo without password (optional)
To avoid entering sudo password every time:
```bash
sudo visudo
```

Add this line (replace `username` with your username):
```
username ALL=(ALL) NOPASSWD: /bin/cp, /usr/bin/test
```

## 🤝 Contributing

We welcome all contributions! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)  
5. Create a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` file for more information.

## 📞 Contact


- Email: caolecongthanh@gmail.com

## 🙏 Acknowledgments

- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [matplotlib](https://matplotlib.org/) - Plotting library
- [bcrypt](https://github.com/pyca/bcrypt/) - Password hashing
- [psutil](https://github.com/giampaolo/psutil) - Process and system utilities

---

**🎯 Focus to succeed! Just one command: `sudo ./run_clean.sh`**
