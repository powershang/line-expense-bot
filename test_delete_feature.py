#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
測試後台刪除功能
驗證單筆刪除、批量刪除和清空用戶記錄功能
"""

import requests
import json
from database import ExpenseDatabase

def test_delete_features():
    """測試刪除功能"""
    base_url = "http://localhost:5000"
    
    print("🧪 開始測試刪除功能...")
    print("=" * 50)
    
    # 1. 先添加一些測試記錄
    print("\n1️⃣ 添加測試記錄...")
    db = ExpenseDatabase()
    test_user_id = "TEST_DELETE_USER_123"
    
    # 添加幾筆測試記錄
    test_records = []
    for i in range(5):
        expense_id = db.add_expense(
            user_id=test_user_id,
            amount=100 + i * 10,
            description=f"測試記錄{i+1}",
            category="測試分類",
            location="測試地點"
        )
        test_records.append(expense_id)
        print(f"  ✅ 添加記錄 #{expense_id}: 測試記錄{i+1}")
    
    print(f"\n📊 添加了 {len(test_records)} 筆測試記錄")
    print(f"記錄 IDs: {test_records}")
    
    # 2. 測試單筆刪除
    print("\n2️⃣ 測試單筆刪除...")
    delete_id = test_records[0]
    
    try:
        response = requests.post(f"{base_url}/admin/delete/{delete_id}")
        result = response.json()
        
        if result.get('success'):
            print(f"  ✅ 成功刪除記錄 #{delete_id}")
            test_records.remove(delete_id)
        else:
            print(f"  ❌ 刪除失敗: {result.get('error')}")
    except Exception as e:
        print(f"  ❌ 請求失敗: {e}")
    
    # 3. 測試批量刪除
    print("\n3️⃣ 測試批量刪除...")
    batch_delete_ids = test_records[:2]  # 刪除前兩筆
    
    try:
        response = requests.post(
            f"{base_url}/admin/batch-delete",
            json={"ids": batch_delete_ids},
            headers={"Content-Type": "application/json"}
        )
        result = response.json()
        
        if result.get('success'):
            print(f"  ✅ 成功批量刪除 {result.get('deleted_count')} 筆記錄")
            for id in batch_delete_ids:
                test_records.remove(id)
        else:
            print(f"  ❌ 批量刪除失敗: {result.get('error')}")
    except Exception as e:
        print(f"  ❌ 請求失敗: {e}")
    
    # 4. 測試清空用戶記錄
    print("\n4️⃣ 測試清空用戶記錄...")
    
    try:
        response = requests.post(f"{base_url}/admin/clear-user/{test_user_id}")
        result = response.json()
        
        if result.get('success'):
            print(f"  ✅ 成功清空用戶記錄，刪除了 {result.get('deleted_count')} 筆")
            test_records.clear()
        else:
            print(f"  ❌ 清空失敗: {result.get('error')}")
    except Exception as e:
        print(f"  ❌ 請求失敗: {e}")
    
    # 5. 驗證記錄是否真的被刪除
    print("\n5️⃣ 驗證刪除結果...")
    
    remaining_records = db.get_user_expenses(test_user_id)
    print(f"  剩餘記錄數: {len(remaining_records)}")
    
    if len(remaining_records) == 0:
        print("  ✅ 所有測試記錄已被成功刪除！")
    else:
        print("  ⚠️ 還有記錄未被刪除:")
        for record in remaining_records:
            print(f"    - 記錄 #{record[0]}: {record[3]}")
    
    # 6. 測試管理界面的可訪問性
    print("\n6️⃣ 測試管理界面...")
    
    try:
        # 測試管理首頁
        response = requests.get(f"{base_url}/admin")
        if response.status_code == 200:
            print("  ✅ 管理首頁正常")
        else:
            print(f"  ❌ 管理首頁錯誤: {response.status_code}")
        
        # 測試所有記錄頁面
        response = requests.get(f"{base_url}/admin/expenses")
        if response.status_code == 200:
            print("  ✅ 所有記錄頁面正常")
        else:
            print(f"  ❌ 所有記錄頁面錯誤: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ 界面測試失敗: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 刪除功能測試完成！")
    print("\n💡 現在你可以訪問以下頁面測試刪除功能:")
    print(f"   • 管理首頁: {base_url}/admin")
    print(f"   • 所有記錄: {base_url}/admin/expenses")
    print(f"   • 用戶詳情: {base_url}/admin/user/[USER_ID]")
    
    print("\n🔧 刪除功能說明:")
    print("   • 單筆刪除: 點擊記錄旁的 🗑️ 按鈕")
    print("   • 批量刪除: 勾選記錄後點擊批量刪除按鈕")
    print("   • 清空用戶: 在用戶詳情頁面點擊清空按鈕")
    print("   • 所有刪除操作都有確認提醒，防止誤刪")

if __name__ == "__main__":
    try:
        test_delete_features()
    except KeyboardInterrupt:
        print("\n\n⏹️ 測試被中斷")
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc() 