#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
驗證資料庫持久化腳本
用於確認資料是否真的存在資料庫中，而不是內存中
"""

import os
import sys
import sqlite3
from datetime import datetime

# 設定調試模式
os.environ['DEBUG_MODE'] = 'true'

def direct_sqlite_query():
    """直接查詢 SQLite 資料庫，不經過我們的 ExpenseDatabase 類別"""
    print("🔍 直接查詢 SQLite 資料庫檔案...")
    
    db_file = 'expense_tracker.db'
    
    if not os.path.exists(db_file):
        print(f"❌ 資料庫檔案 {db_file} 不存在")
        return
    
    print(f"✅ 資料庫檔案存在: {db_file}")
    print(f"📁 檔案大小: {os.path.getsize(db_file)} bytes")
    print(f"🕐 最後修改時間: {datetime.fromtimestamp(os.path.getmtime(db_file))}")
    
    try:
        # 直接連線 SQLite
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # 查詢表格結構
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"\n📊 資料表: {[table[0] for table in tables]}")
        
        # 查詢 expenses 表的所有記錄
        cursor.execute("SELECT COUNT(*) FROM expenses")
        total_count = cursor.fetchone()[0]
        print(f"📈 總記錄數: {total_count}")
        
        if total_count > 0:
            cursor.execute("""
                SELECT id, user_id, amount, location, description, timestamp 
                FROM expenses 
                ORDER BY timestamp DESC 
                LIMIT 10
            """)
            records = cursor.fetchall()
            
            print("\n📋 最近 10 筆記錄:")
            for i, record in enumerate(records, 1):
                print(f"  {i}. ID:{record[0]} | User:{record[1]} | 金額:{record[2]} | 地點:{record[3]} | 描述:{record[4]} | 時間:{record[5]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 直接查詢失敗: {e}")

def test_our_database_class():
    """測試我們的 ExpenseDatabase 類別是否能讀取持久化的資料"""
    print("\n🔍 使用我們的 ExpenseDatabase 類別查詢...")
    
    try:
        from database import ExpenseDatabase
        db = ExpenseDatabase()
        
        # 查詢不同用戶的記錄
        test_users = ['debug_user_123', 'interactive_user']
        
        for user_id in test_users:
            expenses = db.get_user_expenses(user_id, limit=5)
            print(f"\n👤 用戶 {user_id}: {len(expenses)} 筆記錄")
            
            for i, expense in enumerate(expenses, 1):
                print(f"  {i}. {expense[1]}元 - {expense[3]} ({expense[2]}) - {expense[5]}")
        
    except Exception as e:
        print(f"❌ ExpenseDatabase 查詢失敗: {e}")
        import traceback
        traceback.print_exc()

def test_persistence():
    """測試持久化：新增一筆記錄，然後重新初始化資料庫類別來查詢"""
    print("\n🔍 測試持久化：新增 -> 重新初始化 -> 查詢...")
    
    test_user = "persistence_test_user"
    test_amount = 999.99
    test_description = f"持久化測試 {datetime.now().strftime('%H:%M:%S')}"
    
    try:
        # 第一次：新增記錄
        from database import ExpenseDatabase
        db1 = ExpenseDatabase()
        
        expense_id = db1.add_expense(
            user_id=test_user,
            amount=test_amount,
            location="測試地點",
            description=test_description,
            category=None
        )
        print(f"✅ 新增記錄 ID: {expense_id}")
        
        # 刪除變數，模擬程式重啟
        del db1
        
        # 第二次：重新初始化並查詢
        db2 = ExpenseDatabase()
        expenses = db2.get_user_expenses(test_user, limit=1)
        
        if expenses and expenses[0][0] == expense_id:
            print(f"✅ 持久化成功！重新初始化後仍能查到記錄: {expenses[0]}")
        else:
            print(f"❌ 持久化失敗！重新初始化後查不到記錄")
            
    except Exception as e:
        print(f"❌ 持久化測試失敗: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🔬 資料庫持久化驗證工具")
    print("=" * 50)
    
    # 1. 直接查詢 SQLite 檔案
    direct_sqlite_query()
    
    # 2. 使用我們的類別查詢
    test_our_database_class()
    
    # 3. 測試持久化
    test_persistence()
    
    print("\n" + "=" * 50)
    print("✅ 驗證完成")

if __name__ == "__main__":
    main() 