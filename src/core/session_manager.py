"""
Quản lý lịch sử và thống kê thời gian tập trung
Lưu trữ trong SQLite database
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple, Optional

class SessionManager:
    """Quản lý phiên làm việc và thống kê"""
    
    def __init__(self, data_dir: Path):
        self.db_path = data_dir / "sessions.db"
        self.init_database()
    
    def init_database(self):
        """Khởi tạo cơ sở dữ liệu"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Bảng phiên làm việc
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    planned_duration INTEGER NOT NULL,  -- phút
                    actual_duration INTEGER,           -- phút
                    completed BOOLEAN NOT NULL DEFAULT 0,
                    interrupted BOOLEAN NOT NULL DEFAULT 0,
                    websites_blocked TEXT,             -- JSON string
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                
                # Bảng thống kê hàng ngày
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    date DATE PRIMARY KEY,
                    total_focus_time INTEGER NOT NULL DEFAULT 0,  -- phút
                    sessions_completed INTEGER NOT NULL DEFAULT 0,
                    sessions_interrupted INTEGER NOT NULL DEFAULT 0,
                    websites_blocked TEXT,                        -- JSON string
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                
                conn.commit()
                print("Database initialized successfully")
                
        except sqlite3.Error as e:
            print(f"Lỗi khởi tạo database: {e}")
    
    def start_session(self, planned_duration: int, websites_to_block: List[str]) -> int:
        """Bắt đầu phiên tập trung mới"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO sessions (start_time, planned_duration, websites_blocked)
                VALUES (?, ?, ?)
                ''', (
                    datetime.now(),
                    planned_duration,
                    json.dumps(websites_to_block)
                ))
                
                session_id = cursor.lastrowid
                conn.commit()
                
                print(f"Bắt đầu phiên {session_id}, dự kiến {planned_duration} phút")
                return session_id
                
        except sqlite3.Error as e:
            print(f"Lỗi bắt đầu phiên: {e}")
            return -1
    
    def end_session(self, session_id: int, completed: bool = True, notes: str = ""):
        """Kết thúc phiên tập trung"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Lấy thông tin phiên
                cursor.execute('SELECT start_time FROM sessions WHERE id = ?', (session_id,))
                result = cursor.fetchone()
                
                if not result:
                    print(f"Không tìm thấy phiên {session_id}")
                    return
                
                start_time = datetime.fromisoformat(result[0])
                end_time = datetime.now()
                actual_duration = int((end_time - start_time).total_seconds() / 60)
                
                # Cập nhật phiên
                cursor.execute('''
                UPDATE sessions 
                SET end_time = ?, actual_duration = ?, completed = ?, 
                    interrupted = ?, notes = ?
                WHERE id = ?
                ''', (
                    end_time,
                    actual_duration,
                    completed,
                    not completed,
                    notes,
                    session_id
                ))
                
                # Cập nhật thống kê hàng ngày
                self._update_daily_stats(cursor, start_time.date(), actual_duration, completed)
                
                conn.commit()
                
                status = "hoàn thành" if completed else "bị gián đoạn"
                print(f"Kết thúc phiên {session_id} ({status}), thời gian thực: {actual_duration} phút")
                
        except sqlite3.Error as e:
            print(f"Lỗi kết thúc phiên: {e}")
    
    def _update_daily_stats(self, cursor, date, duration, completed):
        """Cập nhật thống kê hàng ngày"""
        try:
            # Kiểm tra đã có record cho ngày này chưa
            cursor.execute('SELECT * FROM daily_stats WHERE date = ?', (date,))
            existing = cursor.fetchone()
            
            if existing:
                # Cập nhật record có sẵn
                new_total_time = existing[1] + duration
                new_completed = existing[2] + (1 if completed else 0)
                new_interrupted = existing[3] + (0 if completed else 1)
                
                cursor.execute('''
                UPDATE daily_stats 
                SET total_focus_time = ?, sessions_completed = ?, 
                    sessions_interrupted = ?, updated_at = ?
                WHERE date = ?
                ''', (
                    new_total_time,
                    new_completed,
                    new_interrupted,
                    datetime.now(),
                    date
                ))
            else:
                # Tạo record mới
                cursor.execute('''
                INSERT INTO daily_stats (date, total_focus_time, sessions_completed, sessions_interrupted)
                VALUES (?, ?, ?, ?)
                ''', (
                    date,
                    duration,
                    1 if completed else 0,
                    0 if completed else 1
                ))
                
        except sqlite3.Error as e:
            print(f"Lỗi cập nhật thống kê hàng ngày: {e}")
    
    def get_current_session(self) -> Optional[Dict]:
        """Lấy thông tin phiên hiện tại (chưa kết thúc)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT id, start_time, planned_duration, websites_blocked
                FROM sessions 
                WHERE end_time IS NULL 
                ORDER BY start_time DESC 
                LIMIT 1
                ''')
                
                result = cursor.fetchone()
                if result:
                    return {
                        'id': result[0],
                        'start_time': datetime.fromisoformat(result[1]),
                        'planned_duration': result[2],
                        'websites_blocked': json.loads(result[3] or '[]')
                    }
                
        except sqlite3.Error as e:
            print(f"Lỗi lấy phiên hiện tại: {e}")
        
        return None
    
    def get_today_stats(self) -> Dict:
        """Lấy thống kê hôm nay"""
        today = datetime.now().date()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Thống kê từ bảng daily_stats
                cursor.execute('SELECT * FROM daily_stats WHERE date = ?', (today,))
                daily_result = cursor.fetchone()
                
                if daily_result:
                    return {
                        'total_focus_time': daily_result[1],
                        'sessions_completed': daily_result[2],
                        'sessions_interrupted': daily_result[3],
                        'success_rate': (daily_result[2] / (daily_result[2] + daily_result[3]) * 100) 
                                       if (daily_result[2] + daily_result[3]) > 0 else 0
                    }
                else:
                    return {
                        'total_focus_time': 0,
                        'sessions_completed': 0,
                        'sessions_interrupted': 0,
                        'success_rate': 0
                    }
                    
        except sqlite3.Error as e:
            print(f"Lỗi lấy thống kê hôm nay: {e}")
            return {
                'total_focus_time': 0,
                'sessions_completed': 0,
                'sessions_interrupted': 0,
                'success_rate': 0
            }
    
    def get_week_stats(self) -> List[Dict]:
        """Lấy thống kê 7 ngày gần nhất"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=6)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT date, total_focus_time, sessions_completed, sessions_interrupted
                FROM daily_stats 
                WHERE date BETWEEN ? AND ?
                ORDER BY date
                ''', (start_date, end_date))
                
                results = cursor.fetchall()
                
                # Tạo dict để dễ lookup
                stats_dict = {
                    datetime.fromisoformat(str(row[0])).date(): {
                        'date': row[0],
                        'total_focus_time': row[1],
                        'sessions_completed': row[2],
                        'sessions_interrupted': row[3]
                    }
                    for row in results
                }
                
                # Đảm bảo có đủ 7 ngày (điền 0 cho ngày không có dữ liệu)
                week_stats = []
                for i in range(7):
                    date = start_date + timedelta(days=i)
                    if date in stats_dict:
                        week_stats.append(stats_dict[date])
                    else:
                        week_stats.append({
                            'date': date.isoformat(),
                            'total_focus_time': 0,
                            'sessions_completed': 0,
                            'sessions_interrupted': 0
                        })
                
                return week_stats
                
        except sqlite3.Error as e:
            print(f"Lỗi lấy thống kê tuần: {e}")
            return []
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """Lấy danh sách phiên gần nhất"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT id, start_time, end_time, planned_duration, actual_duration,
                       completed, interrupted, notes
                FROM sessions
                WHERE end_time IS NOT NULL
                ORDER BY start_time DESC
                LIMIT ?
                ''', (limit,))
                
                results = cursor.fetchall()
                
                sessions = []
                for row in results:
                    sessions.append({
                        'id': row[0],
                        'start_time': row[1],
                        'end_time': row[2],
                        'planned_duration': row[3],
                        'actual_duration': row[4] or 0,
                        'completed': bool(row[5]),
                        'interrupted': bool(row[6]),
                        'notes': row[7] or ""
                    })
                
                return sessions
                
        except sqlite3.Error as e:
            print(f"Lỗi lấy lịch sử phiên: {e}")
            return []
