"""
Widget hiển thị thống kê và biểu đồ
"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QGroupBox, QGridLayout, QPushButton)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# Thêm thư mục src vào path
current_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(current_dir))

from src.core.session_manager import SessionManager

class StatisticsWidget(QWidget):
    """Widget hiển thị thống kê"""
    
    def __init__(self, session_manager: SessionManager):
        super().__init__()
        self.session_manager = session_manager
        self.setup_ui()
        self.refresh_stats()
    
    def setup_ui(self):
        """Thiết lập giao diện"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # === THỐNG KÊ TỔNG QUAN ===
        overview_group = QGroupBox("📈 Tổng quan")
        overview_layout = QGridLayout(overview_group)
        
        # Labels cho thống kê
        self.today_time_label = QLabel("0 phút")
        self.today_sessions_label = QLabel("0")
        self.today_success_label = QLabel("0%")
        self.week_time_label = QLabel("0 phút")
        
        # Thiết lập font cho các số liệu
        stat_font = QFont()
        stat_font.setPointSize(14)
        stat_font.setBold(True)
        
        for label in [self.today_time_label, self.today_sessions_label, 
                     self.today_success_label, self.week_time_label]:
            label.setFont(stat_font)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("color: #2196F3; background: #f0f0f0; padding: 10px; border-radius: 5px;")
        
        # Thêm vào layout
        overview_layout.addWidget(QLabel("Hôm nay:"), 0, 0)
        overview_layout.addWidget(self.today_time_label, 0, 1)
        overview_layout.addWidget(QLabel("phút"), 0, 2)
        
        overview_layout.addWidget(QLabel("Phiên hoàn thành:"), 1, 0)
        overview_layout.addWidget(self.today_sessions_label, 1, 1)
        overview_layout.addWidget(QLabel("phiên"), 1, 2)
        
        overview_layout.addWidget(QLabel("Tỷ lệ thành công:"), 2, 0)
        overview_layout.addWidget(self.today_success_label, 2, 1)
        overview_layout.addWidget(QLabel(""), 2, 2)
        
        overview_layout.addWidget(QLabel("Tuần này:"), 3, 0)
        overview_layout.addWidget(self.week_time_label, 3, 1)
        overview_layout.addWidget(QLabel("phút"), 3, 2)
        
        layout.addWidget(overview_group)
        
        # === BIỂU ĐỒ ===
        chart_group = QGroupBox("📊 Biểu đồ 7 ngày gần nhất")
        chart_layout = QVBoxLayout(chart_group)
        
        # Tạo matplotlib figure
        self.figure = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        chart_layout.addWidget(self.canvas)
        
        # Nút refresh
        refresh_btn = QPushButton("🔄 Cập nhật")
        refresh_btn.clicked.connect(self.refresh_stats)
        chart_layout.addWidget(refresh_btn)
        
        layout.addWidget(chart_group)
        
        # Spacer
        layout.addStretch()
    
    def refresh_stats(self):
        """Cập nhật thống kê"""
        # Cập nhật thống kê hôm nay
        today_stats = self.session_manager.get_today_stats()
        self.today_time_label.setText(f"{today_stats['total_focus_time']}")
        self.today_sessions_label.setText(str(today_stats['sessions_completed']))
        self.today_success_label.setText(f"{today_stats['success_rate']:.1f}")
        
        # Cập nhật thống kê tuần
        week_stats = self.session_manager.get_week_stats()
        week_total = sum(day['total_focus_time'] for day in week_stats)
        self.week_time_label.setText(str(week_total))
        
        # Cập nhật biểu đồ
        self.update_chart(week_stats)
    
    def update_chart(self, week_stats):
        """Cập nhật biểu đồ"""
        self.figure.clear()
        
        # Tạo subplot
        ax = self.figure.add_subplot(111)
        
        # Dữ liệu cho biểu đồ
        dates = []
        times = []
        sessions = []
        
        for day in week_stats:
            date = datetime.fromisoformat(day['date']).date()
            dates.append(date)
            times.append(day['total_focus_time'])
            sessions.append(day['sessions_completed'])
        
        # Biểu đồ cột cho thời gian tập trung
        bars = ax.bar(dates, times, alpha=0.7, color='#2196F3', label='Thời gian tập trung (phút)')
        
        # Tạo trục y thứ hai cho số phiên
        ax2 = ax.twinx()
        line = ax2.plot(dates, sessions, color='#FF9800', marker='o', linewidth=2, label='Số phiên hoàn thành')
        
        # Thiết lập labels và title
        ax.set_xlabel('Ngày')
        ax.set_ylabel('Thời gian (phút)', color='#2196F3')
        ax2.set_ylabel('Số phiên', color='#FF9800')
        ax.set_title('Thống kê tập trung 7 ngày gần nhất')
        
        # Format trục x
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator())
        
        # Xoay labels trục x
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Thiết lập màu cho các trục
        ax.tick_params(axis='y', labelcolor='#2196F3')
        ax2.tick_params(axis='y', labelcolor='#FF9800')
        
        # Grid
        ax.grid(True, alpha=0.3)
        
        # Legend
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        # Thêm giá trị lên các cột
        for bar, time_val in zip(bars, times):
            if time_val > 0:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                       f'{int(time_val)}', ha='center', va='bottom', fontsize=9)
        
        # Tight layout
        self.figure.tight_layout()
        
        # Refresh canvas
        self.canvas.draw()
