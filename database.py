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
        
        # 建立用戶設定表（記錄統計重置日期）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id TEXT PRIMARY KEY,
                stats_reset_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
    
    def get_monthly_total(self, user_id, year, month):
        """取得指定月份的總支出金額"""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"
        
        cursor.execute('''
            SELECT SUM(amount), COUNT(*)
            FROM expenses
            WHERE user_id = ? AND timestamp >= ? AND timestamp < ?
        ''', (user_id, start_date, end_date))
        
        result = cursor.fetchone()
        conn.close()
        
        total_amount = result[0] or 0
        total_count = result[1] or 0
        
        return total_amount, total_count
    
    def get_all_time_stats(self, user_id):
        """取得用戶的總統計資料"""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        # 總金額和總筆數
        cursor.execute('''
            SELECT SUM(amount), COUNT(*), MIN(timestamp), MAX(timestamp)
            FROM expenses
            WHERE user_id = ?
        ''', (user_id,))
        
        total_result = cursor.fetchone()
        
        # 每月統計
        cursor.execute('''
            SELECT strftime('%Y-%m', timestamp) as month, SUM(amount), COUNT(*)
            FROM expenses
            WHERE user_id = ?
            GROUP BY strftime('%Y-%m', timestamp)
            ORDER BY month DESC
            LIMIT 12
        ''', (user_id,))
        
        monthly_stats = cursor.fetchall()
        conn.close()
        
        total_amount = total_result[0] or 0
        total_count = total_result[1] or 0
        first_record = total_result[2]
        last_record = total_result[3]
        
        return {
            'total_amount': total_amount,
            'total_count': total_count,
            'first_record': first_record,
            'last_record': last_record,
            'monthly_stats': monthly_stats
        }
    
    def clear_all_expenses(self, user_id):
        """清空用戶的所有支出記錄"""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        # 先取得記錄數量
        cursor.execute('''
            SELECT COUNT(*) FROM expenses WHERE user_id = ?
        ''', (user_id,))
        
        count_before = cursor.fetchone()[0]
        
        # 刪除所有記錄
        cursor.execute('''
            DELETE FROM expenses WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        affected_rows = cursor.rowcount
        conn.close()
        
        return count_before, affected_rows
    
    def get_current_stats(self, user_id):
        """取得當前統計金額（從重置日期開始計算）"""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        # 取得重置日期
        cursor.execute('''
            SELECT stats_reset_date FROM user_settings WHERE user_id = ?
        ''', (user_id,))
        
        reset_result = cursor.fetchone()
        
        if reset_result:
            reset_date = reset_result[0]
        else:
            # 如果沒有設定，創建設定並使用第一筆記錄的時間
            cursor.execute('''
                SELECT MIN(timestamp) FROM expenses WHERE user_id = ?
            ''', (user_id,))
            
            first_record = cursor.fetchone()[0]
            reset_date = first_record or datetime.now().isoformat()
            
            # 創建用戶設定
            cursor.execute('''
                INSERT OR REPLACE INTO user_settings (user_id, stats_reset_date)
                VALUES (?, ?)
            ''', (user_id, reset_date))
            conn.commit()
        
        # 計算重置日期之後的統計
        cursor.execute('''
            SELECT SUM(amount), COUNT(*), MIN(timestamp), MAX(timestamp)
            FROM expenses
            WHERE user_id = ? AND timestamp >= ?
        ''', (user_id, reset_date))
        
        result = cursor.fetchone()
        conn.close()
        
        total_amount = result[0] or 0
        total_count = result[1] or 0
        first_record = result[2]
        last_record = result[3]
        
        return {
            'total_amount': total_amount,
            'total_count': total_count,
            'first_record': first_record,
            'last_record': last_record,
            'reset_date': reset_date
        }
    
    def reset_current_stats(self, user_id):
        """重置當前統計（更新重置日期為現在）"""
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        # 取得重置前的統計
        current_stats = self.get_current_stats(user_id)
        
        # 更新重置日期為現在
        reset_date = datetime.now().isoformat()
        cursor.execute('''
            INSERT OR REPLACE INTO user_settings (user_id, stats_reset_date)
            VALUES (?, ?)
        ''', (user_id, reset_date))
        
        conn.commit()
        conn.close()
        
        return current_stats 