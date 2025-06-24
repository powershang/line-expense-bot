#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
本地調試工具
用於測試記帳功能而不需要 LINE Bot 環境
"""

import os
import sys
from datetime import datetime

# 設定調試模式
os.environ['DEBUG_MODE'] = 'true'

# 確保可以導入模組
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database_connection():
    """測試資料庫連線"""
    print("🔍 測試資料庫連線...")
    try:
        from database import ExpenseDatabase
        db = ExpenseDatabase()
        print("✅ 資料庫初始化成功")
        return db
    except Exception as e:
        print(f"❌ 資料庫初始化失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_message_parser():
    """測試訊息解析器"""
    print("\n🔍 測試訊息解析器...")
    try:
        from message_parser import MessageParser
        parser = MessageParser()
        
        # 測試案例
        test_messages = [
            "午餐 120",
            "在7-11買飲料50元",
            "捷運票30元",
            "星巴克咖啡150",
            "家樂福買菜500元"
        ]
        
        for msg in test_messages:
            result = parser.parse_message(msg)
            print(f"  輸入: '{msg}'")
            print(f"  解析結果: {result}")
            print()
        
        print("✅ 訊息解析器測試完成")
        return parser
    except Exception as e:
        print(f"❌ 訊息解析器測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_add_expense(db, parser):
    """測試新增支出記錄"""
    print("\n🔍 測試新增支出記錄...")
    
    test_user_id = "debug_user_123"
    test_messages = [
        "午餐 120",
        "在7-11買飲料50元", 
        "捷運票30元"
    ]
    
    for msg in test_messages:
        print(f"\n📝 處理訊息: '{msg}'")
        
        # 解析訊息
        parsed = parser.parse_message(msg)
        print(f"  解析結果: {parsed}")
        
        if parsed['amount'] and parsed['amount'] > 0:
            try:
                # 新增到資料庫
                expense_id = db.add_expense(
                    user_id=test_user_id,
                    amount=parsed['amount'],
                    location=parsed.get('reason', ''),  # 使用 reason 作為 location
                    description=parsed['description'],
                    category=None
                )
                print(f"  ✅ 成功新增記錄，ID: {expense_id}")
            except Exception as e:
                print(f"  ❌ 新增記錄失敗: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"  ⚠️ 解析失敗，跳過此訊息")

def test_query_expenses(db):
    """測試查詢支出記錄"""
    print("\n🔍 測試查詢支出記錄...")
    
    test_user_id = "debug_user_123"
    
    try:
        expenses = db.get_user_expenses(test_user_id, limit=10)
        print(f"✅ 查詢到 {len(expenses)} 筆記錄:")
        
        for i, expense in enumerate(expenses, 1):
            print(f"  {i}. ID: {expense[0]}, 金額: {expense[1]}, 地點: {expense[2]}, 描述: {expense[3]}, 時間: {expense[5]}")
            
    except Exception as e:
        print(f"❌ 查詢記錄失敗: {e}")
        import traceback
        traceback.print_exc()

def interactive_mode(db, parser):
    """互動式測試模式"""
    print("\n🎮 進入互動式測試模式")
    print("輸入記帳訊息來測試，輸入 'quit' 退出")
    print("輸入 'list' 查看記錄")
    print("範例: '午餐 120', '在7-11買飲料50元'")
    print("-" * 50)
    
    test_user_id = "interactive_user"
    
    while True:
        try:
            msg = input("\n💬 請輸入記帳訊息: ").strip()
            
            if msg.lower() in ['quit', 'exit', 'q']:
                break
                
            if msg.lower() == 'list':
                # 顯示記錄
                try:
                    expenses = db.get_user_expenses(test_user_id, limit=5)
                    print(f"\n📋 最近 {len(expenses)} 筆記錄:")
                    for i, expense in enumerate(expenses, 1):
                        print(f"  {i}. {expense[1]}元 - {expense[3]} ({expense[2]}) - {expense[5]}")
                except Exception as e:
                    print(f"❌ 查詢失敗: {e}")
                continue
            
            if not msg:
                continue
                
            # 解析並新增記錄
            parsed = parser.parse_message(msg)
            print(f"🔍 解析結果: {parsed}")
            
            if parsed['amount'] and parsed['amount'] > 0:
                try:
                    expense_id = db.add_expense(
                        user_id=test_user_id,
                        amount=parsed['amount'],
                        location=parsed.get('reason', ''),  # 使用 reason 作為 location
                        description=parsed['description'],
                        category=None
                    )
                    print(f"✅ 成功新增記錄，ID: {expense_id}")
                except Exception as e:
                    print(f"❌ 新增失敗: {e}")
            else:
                print("⚠️ 無法解析出有效金額")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ 發生錯誤: {e}")
    
    print("\n👋 退出互動模式")

def main():
    """主函數"""
    print("🤖 LINE 記帳機器人 - 本地調試工具")
    print("=" * 50)
    
    # 測試資料庫
    db = test_database_connection()
    if not db:
        return
    
    # 測試訊息解析器
    parser = test_message_parser()
    if not parser:
        return
    
    # 選擇測試模式
    print("\n📋 請選擇測試模式:")
    print("1. 自動測試 (預設測試案例)")
    print("2. 互動式測試 (手動輸入)")
    print("3. 僅查詢現有記錄")
    
    try:
        choice = input("\n請選擇 (1-3): ").strip()
        
        if choice == "1":
            test_add_expense(db, parser)
            test_query_expenses(db)
        elif choice == "2":
            interactive_mode(db, parser)
        elif choice == "3":
            test_query_expenses(db)
        else:
            print("無效選擇，執行自動測試...")
            test_add_expense(db, parser)
            test_query_expenses(db)
            
    except KeyboardInterrupt:
        print("\n\n👋 程式已停止")
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")

if __name__ == "__main__":
    main() 