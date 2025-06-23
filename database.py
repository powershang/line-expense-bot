import sqlite3
from datetime import datetime
from config import DATABASE_NAME

class ExpenseDatabase:
    def __init__(self):
        self.init_database()
    
    def init_database(self):
        """初始化資料庫，建立必要的資料表"""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        # 建立支出記錄表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                amount REAL NOT NULL,
                location TEXT,
                description TEXT,
                category TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_expense(self, user_id, amount, location=None, description=None, category=None):
        """新增支出記錄"""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO expenses (user_id, amount, location, description, category)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, amount, location, description, category))
        
        conn.commit()
        expense_id = cursor.lastrowid
        conn.close()
        
        return expense_id
    
    def get_user_expenses(self, user_id, limit=10):
        """取得用戶的支出記錄"""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, amount, location, description, category, timestamp
            FROM expenses
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (user_id, limit))
        
        expenses = cursor.fetchall()
        conn.close()
        
        return expenses
    
    def get_monthly_summary(self, user_id, year, month):
        """取得月度支出摘要"""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"
        
        cursor.execute('''
            SELECT SUM(amount), COUNT(*), category
            FROM expenses
            WHERE user_id = ? AND timestamp >= ? AND timestamp < ?
            GROUP BY category
        ''', (user_id, start_date, end_date))
        
        summary = cursor.fetchall()
        conn.close()
        
        return summary
    
    def delete_expense(self, expense_id, user_id):
        """刪除支出記錄"""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM expenses
            WHERE id = ? AND user_id = ?
        ''', (expense_id, user_id))
        
        conn.commit()
        affected_rows = cursor.rowcount
        conn.close()
        
        return affected_rows > 0 