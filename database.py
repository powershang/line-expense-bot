import sqlite3
import os
from datetime import datetime
from config import DATABASE_NAME, DATABASE_URL

# 檢查是否有 PostgreSQL 支援
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAS_POSTGRESQL = True
    print(f"🔧 DATABASE: psycopg2 導入成功 ✅")
except ImportError as e:
    HAS_POSTGRESQL = False
    print(f"🔧 DATABASE: psycopg2 導入失敗 ❌ - {e}")

class ExpenseDatabase:
    def __init__(self):
        print(f"🔧 DATABASE: 初始化資料庫...")
        print(f"🔧 DATABASE: DATABASE_URL 是否存在: {'✅' if DATABASE_URL else '❌'}")
        print(f"🔧 DATABASE: PostgreSQL 支援: {'✅' if HAS_POSTGRESQL else '❌'}")
        
        self.use_postgresql = DATABASE_URL and HAS_POSTGRESQL
        print(f"🔧 DATABASE: 使用資料庫類型: {'PostgreSQL' if self.use_postgresql else 'SQLite'}")
        
        if self.use_postgresql:
            print(f"🔧 DATABASE: PostgreSQL 連線字串長度: {len(DATABASE_URL)}")
        
        # 測試連線
        try:
            print(f"🔧 DATABASE: 測試資料庫連線...")
            conn = self.get_connection()
            print(f"🔧 DATABASE: 連線測試成功 ✅")
            conn.close()
        except Exception as e:
            print(f"🔧 DATABASE: 連線測試失敗 ❌ - {e}")
            raise e
        
        self.init_database()
        print(f"🔧 DATABASE: 資料庫初始化完成")
    
    def get_connection(self):
        """取得資料庫連線"""
        try:
            if self.use_postgresql:
                return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
            else:
                return sqlite3.connect(DATABASE_NAME)
        except Exception as e:
            print(f"❌ DATABASE: 連線失敗 - {e}")
            raise e
    
    def init_database(self):
        """初始化資料庫，建立必要的資料表"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            print(f"🔧 DATABASE: 建立資料表...")
            
            if self.use_postgresql:
                # PostgreSQL 語法
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS expenses (
                        id SERIAL PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        amount REAL NOT NULL,
                        location TEXT,
                        description TEXT,
                        category TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_settings (
                        user_id TEXT PRIMARY KEY,
                        stats_reset_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 新增用戶資料表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_profiles (
                        user_id TEXT PRIMARY KEY,
                        display_name TEXT,
                        picture_url TEXT,
                        status_message TEXT,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                print(f"🔧 DATABASE: PostgreSQL 資料表建立完成")
            else:
                # SQLite 語法
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
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_settings (
                        user_id TEXT PRIMARY KEY,
                        stats_reset_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 新增用戶資料表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_profiles (
                        user_id TEXT PRIMARY KEY,
                        display_name TEXT,
                        picture_url TEXT,
                        status_message TEXT,
                        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                print(f"🔧 DATABASE: SQLite 資料表建立完成")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ DATABASE: 初始化失敗 - {e}")
            raise e
    
    def add_expense(self, user_id, amount, location=None, description=None, category=None):
        """新增支出記錄"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if self.use_postgresql:
                sql = '''
                    INSERT INTO expenses (user_id, amount, location, description, category)
                    VALUES (%s, %s, %s, %s, %s) RETURNING id
                '''
                params = (user_id, amount, location, description, category)
                cursor.execute(sql, params)
                
                result = cursor.fetchone()
                if result:
                    # PostgreSQL psycopg2 返回的可能是 tuple 或 DictRow
                    if isinstance(result, (list, tuple)):
                        expense_id = result[0]
                    else:
                        # 如果是 DictRow 或其他類型，嘗試用 'id' 鍵
                        expense_id = result['id'] if hasattr(result, '__getitem__') and 'id' in result else result[0]
                else:
                    expense_id = None
            else:
                sql = '''
                    INSERT INTO expenses (user_id, amount, location, description, category)
                    VALUES (?, ?, ?, ?, ?)
                '''
                params = (user_id, amount, location, description, category)
                cursor.execute(sql, params)
                expense_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            return expense_id
            
        except Exception as e:
            print(f"❌ DATABASE: 新增支出記錄失敗 - {type(e).__name__}: {str(e)}")
            if conn:
                try:
                    conn.rollback()
                    conn.close()
                except Exception as close_e:
                    print(f"❌ DATABASE: 關閉連線時發生錯誤: {close_e}")
            raise e
    
    def get_user_expenses(self, user_id, limit=10):
        """取得用戶的支出記錄"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if self.use_postgresql:
                cursor.execute('''
                    SELECT id, amount, location, description, category, timestamp
                    FROM expenses
                    WHERE user_id = %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                ''', (user_id, limit))
            else:
                cursor.execute('''
                    SELECT id, amount, location, description, category, timestamp
                    FROM expenses
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (user_id, limit))
            
            expenses = cursor.fetchall()
            conn.close()
            
            # 轉換 PostgreSQL 結果為 list
            if self.use_postgresql:
                expenses = [tuple(expense.values()) for expense in expenses]
            
            return expenses
            
        except Exception as e:
            print(f"❌ DATABASE: 查詢用戶記錄失敗 - {type(e).__name__}: {str(e)}")
            if conn:
                try:
                    conn.close()
                except:
                    pass
            raise e
    
    def get_monthly_summary(self, user_id, year, month):
        """取得月度支出摘要"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"
        
        cursor.execute('''
            SELECT SUM(amount), COUNT(*), category
            FROM expenses
            WHERE user_id = %s AND timestamp >= %s AND timestamp < %s
            GROUP BY category
        ''' if self.use_postgresql else '''
            SELECT SUM(amount), COUNT(*), category
            FROM expenses
            WHERE user_id = ? AND timestamp >= ? AND timestamp < ?
            GROUP BY category
        ''', (user_id, start_date, end_date))
        
        summary = cursor.fetchall()
        conn.close()
        
        # 轉換 PostgreSQL 結果為 list
        if self.use_postgresql:
            summary = [tuple(row.values()) for row in summary]
        
        return summary
    
    def delete_expense(self, expense_id, user_id):
        """刪除支出記錄"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM expenses
            WHERE id = %s AND user_id = %s
        ''' if self.use_postgresql else '''
            DELETE FROM expenses
            WHERE id = ? AND user_id = ?
        ''', (expense_id, user_id))
        
        conn.commit()
        affected_rows = cursor.rowcount
        conn.close()
        
        return affected_rows > 0
    
    def get_monthly_total(self, user_id, year, month):
        """取得指定月份的總支出金額"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            start_date = f"{year}-{month:02d}-01"
            if month == 12:
                end_date = f"{year+1}-01-01"
            else:
                end_date = f"{year}-{month+1:02d}-01"
            
            if self.use_postgresql:
                cursor.execute('''
                    SELECT SUM(amount), COUNT(*)
                    FROM expenses
                    WHERE user_id = %s AND timestamp >= %s AND timestamp < %s
                ''', (user_id, start_date, end_date))
            else:
                cursor.execute('''
                    SELECT SUM(amount), COUNT(*)
                    FROM expenses
                    WHERE user_id = ? AND timestamp >= ? AND timestamp < ?
                ''', (user_id, start_date, end_date))
            
            result = cursor.fetchone()
            conn.close()
            
            if self.use_postgresql:
                total_amount = result[0] if result[0] is not None else 0
                total_count = result[1] if result[1] is not None else 0
            else:
                total_amount = result[0] if result[0] is not None else 0
                total_count = result[1] if result[1] is not None else 0
            
            return total_amount, total_count
            
        except Exception as e:
            print(f"❌ DATABASE: 查詢月度總計失敗 - {type(e).__name__}: {str(e)}")
            if conn:
                try:
                    conn.close()
                except:
                    pass
            raise e
    
    def get_all_time_stats(self, user_id):
        """取得用戶的總統計資料"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 總金額和總筆數
        cursor.execute('''
            SELECT SUM(amount), COUNT(*), MIN(timestamp), MAX(timestamp)
            FROM expenses
            WHERE user_id = %s
        ''' if self.use_postgresql else '''
            SELECT SUM(amount), COUNT(*), MIN(timestamp), MAX(timestamp)
            FROM expenses
            WHERE user_id = ?
        ''', (user_id,))
        
        total_result = cursor.fetchone()
        
        # 每月統計
        if self.use_postgresql:
            cursor.execute('''
                SELECT to_char(timestamp, 'YYYY-MM') as month, SUM(amount), COUNT(*)
                FROM expenses
                WHERE user_id = %s
                GROUP BY to_char(timestamp, 'YYYY-MM')
                ORDER BY month DESC
                LIMIT 12
            ''', (user_id,))
        else:
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
        
        if self.use_postgresql:
            total_amount = total_result[0] or 0
            total_count = total_result[1] or 0
            first_record = total_result[2]
            last_record = total_result[3]
            monthly_stats = [tuple(row.values()) for row in monthly_stats]
        else:
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
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 先取得記錄數量
        cursor.execute('''
            SELECT COUNT(*) FROM expenses WHERE user_id = %s
        ''' if self.use_postgresql else '''
            SELECT COUNT(*) FROM expenses WHERE user_id = ?
        ''', (user_id,))
        
        count_before = cursor.fetchone()[0]
        
        # 刪除所有記錄
        cursor.execute('''
            DELETE FROM expenses WHERE user_id = %s
        ''' if self.use_postgresql else '''
            DELETE FROM expenses WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        affected_rows = cursor.rowcount
        conn.close()
        
        return count_before, affected_rows
    
    def get_current_stats(self, user_id):
        """取得當前統計金額（從重置日期開始計算）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 取得重置日期
        cursor.execute('''
            SELECT stats_reset_date FROM user_settings WHERE user_id = %s
        ''' if self.use_postgresql else '''
            SELECT stats_reset_date FROM user_settings WHERE user_id = ?
        ''', (user_id,))
        
        reset_result = cursor.fetchone()
        
        if reset_result:
            # 處理 PostgreSQL DictRow 和 SQLite tuple 的差異
            if self.use_postgresql:
                reset_date = reset_result['stats_reset_date'] if hasattr(reset_result, '__getitem__') and 'stats_reset_date' in reset_result else reset_result[0]
            else:
                reset_date = reset_result[0]
        else:
            # 如果沒有設定，創建設定並使用第一筆記錄的時間
            cursor.execute('''
                SELECT MIN(timestamp) FROM expenses WHERE user_id = %s
            ''' if self.use_postgresql else '''
                SELECT MIN(timestamp) FROM expenses WHERE user_id = ?
            ''', (user_id,))
            
            first_record = cursor.fetchone()
            
            # 處理 first_record 的類型差異
            if first_record:
                if self.use_postgresql:
                    reset_date = first_record['min'] if hasattr(first_record, '__getitem__') and 'min' in first_record else first_record[0]
                else:
                    reset_date = first_record[0]
            else:
                reset_date = None
            
            if not reset_date:
                reset_date = datetime.now().isoformat()
            
            # 創建用戶設定
            if self.use_postgresql:
                cursor.execute('''
                    INSERT INTO user_settings (user_id, stats_reset_date)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET stats_reset_date = EXCLUDED.stats_reset_date
                ''', (user_id, reset_date))
            else:
                cursor.execute('''
                    INSERT OR REPLACE INTO user_settings (user_id, stats_reset_date)
                    VALUES (?, ?)
                ''', (user_id, reset_date))
            conn.commit()
        
        # 計算重置日期之後的統計
        cursor.execute('''
            SELECT SUM(amount), COUNT(*), MIN(timestamp), MAX(timestamp)
            FROM expenses
            WHERE user_id = %s AND timestamp >= %s
        ''' if self.use_postgresql else '''
            SELECT SUM(amount), COUNT(*), MIN(timestamp), MAX(timestamp)
            FROM expenses
            WHERE user_id = ? AND timestamp >= ?
        ''', (user_id, reset_date))
        
        result = cursor.fetchone()
        conn.close()
        
        if self.use_postgresql:
            # 處理 PostgreSQL DictRow
            if hasattr(result, 'keys'):
                # 如果是 DictRow，使用欄位名稱
                total_amount = result.get('sum', 0) or 0
                total_count = result.get('count', 0) or 0
                first_record = result.get('min')
                last_record = result.get('max')
            else:
                # 如果是 tuple，使用索引
                total_amount = result[0] or 0
                total_count = result[1] or 0
                first_record = result[2]
                last_record = result[3]
        else:
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
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 取得重置前的統計
        current_stats = self.get_current_stats(user_id)
        
        # 更新重置日期為現在
        reset_date = datetime.now().isoformat()
        
        if self.use_postgresql:
            cursor.execute('''
                INSERT INTO user_settings (user_id, stats_reset_date)
                VALUES (%s, %s)
                ON CONFLICT (user_id) DO UPDATE SET stats_reset_date = EXCLUDED.stats_reset_date
            ''', (user_id, reset_date))
        else:
            cursor.execute('''
                INSERT OR REPLACE INTO user_settings (user_id, stats_reset_date)
                VALUES (?, ?)
            ''', (user_id, reset_date))
        
        conn.commit()
        conn.close()
        
        return current_stats
    
    def save_user_profile(self, user_id, display_name, picture_url, status_message):
        """儲存或更新用戶資料"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if self.use_postgresql:
                cursor.execute('''
                    INSERT INTO user_profiles (user_id, display_name, picture_url, status_message)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        display_name = EXCLUDED.display_name,
                        picture_url = EXCLUDED.picture_url,
                        status_message = EXCLUDED.status_message,
                        last_updated = CURRENT_TIMESTAMP
                ''', (user_id, display_name, picture_url, status_message))
            else:
                cursor.execute('''
                    INSERT OR REPLACE INTO user_profiles (user_id, display_name, picture_url, status_message)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, display_name, picture_url, status_message))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ DATABASE: 儲存用戶資料失敗 - {e}")
            if conn:
                try:
                    conn.close()
                except:
                    pass
            raise e
    
    def get_user_profile(self, user_id):
        """從資料庫取得用戶資料"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if self.use_postgresql:
                cursor.execute('''
                    SELECT display_name, picture_url, status_message, last_updated
                    FROM user_profiles
                    WHERE user_id = %s
                ''', (user_id,))
            else:
                cursor.execute('''
                    SELECT display_name, picture_url, status_message, last_updated
                    FROM user_profiles
                    WHERE user_id = ?
                ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                if self.use_postgresql:
                    return {
                        'display_name': result['display_name'],
                        'picture_url': result['picture_url'],
                        'status_message': result['status_message'],
                        'last_updated': result['last_updated']
                    }
                else:
                    return {
                        'display_name': result[0],
                        'picture_url': result[1],
                        'status_message': result[2],
                        'last_updated': result[3]
                    }
            else:
                return None
                
        except Exception as e:
            print(f"❌ DATABASE: 查詢用戶資料失敗 - {e}")
            if conn:
                try:
                    conn.close()
                except:
                    pass
            return None 