# ============================================================================
# Fahr - Xodim Vaqti Hisoblash Boti
# Ma'lumotlar Bazasi (Database) Moduli
# ============================================================================

import sqlite3
from datetime import datetime
from typing import List, Optional, Tuple
from config import DATABASE_FILE, ROLE_EMPLOYEE, ROLE_BOSS, STATUS_PENDING, STATUS_ACTIVE


class Database:
    """SQLite ma'lumotlar bazasi bilan ishlash uchun klass"""
    
    def __init__(self, db_file: str = DATABASE_FILE):
        """Database klassini initsializatsiya qilish"""
        self.db_file = db_file
        self.init_db()
    
    def get_connection(self) -> sqlite3.Connection:
        """Database ulanishini olish"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Database jadvallarini yaratish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users jadvali
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'employee',
                hourly_rate REAL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Work_hours jadvali
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS work_hours (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                work_date DATE NOT NULL,
                hours REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, work_date),
                FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # ===================== USERS OPERATSIYALARI =====================
    
    def user_exists(self, user_id: int) -> bool:
        """Foydalanuvchi bazada mavjudmi tekshirish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def add_user(self, user_id: int, full_name: str, role: str = ROLE_EMPLOYEE, status: str = STATUS_PENDING):
        """Yangi foydalanuvchini qo'shish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (user_id, full_name, role, status)
                VALUES (?, ?, ?, ?)
            ''', (user_id, full_name, role, status))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def get_user(self, user_id: int) -> Optional[dict]:
        """Foydalanuvchi ma'lumotini olish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def update_user_status(self, user_id: int, status: str):
        """Foydalanuvchi statusini o'zgartirish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (status, user_id))
        conn.commit()
        conn.close()
    
    def update_hourly_rate(self, user_id: int, hourly_rate: float):
        """Soatbay haqini o'zgartirish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET hourly_rate = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (hourly_rate, user_id))
        conn.commit()
        conn.close()
    
    def get_all_employees(self) -> List[dict]:
        """Barcha xodimlarni olish (Boss uchun)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM users 
            WHERE role = ? AND status = ?
            ORDER BY full_name ASC
        ''', (ROLE_EMPLOYEE, STATUS_ACTIVE))
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_pending_employees(self) -> List[dict]:
        """Tasdiqlash kutayotgan xodimlarni olish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM users 
            WHERE role = ? AND status = ?
            ORDER BY created_at ASC
        ''', (ROLE_EMPLOYEE, STATUS_PENDING))
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    # ===================== WORK_HOURS OPERATSIYALARI =====================
    
    def add_work_hours(self, user_id: int, work_date: str, hours: float) -> Tuple[bool, str]:
        """Ish soatlarini qo'shish (UNIQUE constraint bilan)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO work_hours (user_id, work_date, hours)
                VALUES (?, ?, ?)
            ''', (user_id, work_date, hours))
            conn.commit()
            return True, "Vaqt muvaffaqiyatli kiritildi!"
        except sqlite3.IntegrityError:
            return False, "Bu kun uchun vaqt kiritilgan! Tahrirlash uchun /edit buyrug'ini ishlating."
        finally:
            conn.close()
    
    def get_work_hours(self, user_id: int, work_date: Optional[str] = None) -> List[dict]:
        """Ish soatlarini olish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if work_date:
            cursor.execute('''
                SELECT * FROM work_hours 
                WHERE user_id = ? AND work_date = ?
                ORDER BY work_date ASC
            ''', (user_id, work_date))
        else:
            cursor.execute('''
                SELECT * FROM work_hours 
                WHERE user_id = ?
                ORDER BY work_date ASC
            ''', (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_work_hours_range(self, user_id: int, start_date: str, end_date: str) -> List[dict]:
        """Vaqt oraligi uchun ish soatlarini olish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM work_hours 
            WHERE user_id = ? AND work_date BETWEEN ? AND ?
            ORDER BY work_date ASC
        ''', (user_id, start_date, end_date))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_work_hours(self, user_id: int, work_date: str, hours: float) -> bool:
        """Ish soatlarini tahrirlash"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE work_hours 
            SET hours = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND work_date = ?
        ''', (hours, user_id, work_date))
        
        conn.commit()
        rows_affected = cursor.rowcount
        conn.close()
        
        return rows_affected > 0
    
    def delete_work_hours(self, user_id: int, work_date: str) -> bool:
        """Ish soatlarini o'chirish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM work_hours
            WHERE user_id = ? AND work_date = ?
        ''', (user_id, work_date))
        
        conn.commit()
        rows_affected = cursor.rowcount
        conn.close()
        
        return rows_affected > 0
    
    def get_all_work_hours_range(self, start_date: str, end_date: str) -> List[dict]:
        """Vaqt oraligi uchun BARCHA xodimlarning ish soatlarini olish (Boss uchun)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT wh.*, u.full_name, u.hourly_rate
            FROM work_hours wh
            JOIN users u ON wh.user_id = u.user_id
            WHERE u.role = ? AND u.status = ? AND wh.work_date BETWEEN ? AND ?
            ORDER BY u.full_name ASC, wh.work_date ASC
        ''', (ROLE_EMPLOYEE, STATUS_ACTIVE, start_date, end_date))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def employee_has_pending_approval(self, user_id: int) -> bool:
        """Xodim tasdiqlanishni kutayotganmi?"""
        user = self.get_user(user_id)
        return user and user['status'] == STATUS_PENDING


# Global database instansiyasi
db = Database()
