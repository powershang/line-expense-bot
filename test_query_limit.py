#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
查詢筆數功能測試腳本
測試用戶指定顯示筆數的功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from line_bot import ExpenseBot

def test_query_limit_functionality():
    """測試查詢筆數功能"""
    bot = ExpenseBot()
    test_user_id = "test_query_user"
    
    print("🧪 查詢筆數功能測試開始...")
    print("=" * 60)
    
    # 測試案例
    test_cases = [
        # (訊息, 是否群組, 描述, 預期筆數)
        ("@ai 查詢", True, "群組中查詢預設筆數", 5),
        ("@ai 查詢 10", True, "群組中查詢 10 筆", 10),
        ("@ai 查詢 20", True, "群組中查詢 20 筆", 20),
        ("@ai 查詢 100", True, "群組中查詢超限數量", 50),  # 應被限制為 50
        ("@ai 查詢 0", True, "群組中查詢無效數量", 5),   # 應調整為 5
        ("@ai 記錄", True, "群組中使用記錄指令", 5),
        ("@ai 記錄 15", True, "群組中記錄指定筆數", 15),
        ("@ai list", True, "群組中使用英文指令", 5),
        ("@ai list 8", True, "群組中英文指令指定筆數", 8),
        
        ("查詢", False, "私聊中查詢預設筆數", 5),
        ("查詢10", False, "私聊中查詢 10 筆", 10),
        ("查詢25", False, "私聊中查詢 25 筆", 25),
        ("查詢100", False, "私聊中查詢超限數量", 50),  # 應被限制為 50
        ("記錄5", False, "私聊中記錄 5 筆", 5),
        ("最近12", False, "私聊中最近 12 筆", 12),
        ("list7", False, "私聊中英文指令 7 筆", 7),
        
        ("@ai 查詢 abc", True, "群組中無效格式", 5),  # 應回到預設
        ("@ai 查詢", False, "私聊中 @ai 查詢", 5),
        ("@ai 查詢 30", False, "私聊中 @ai 查詢 30 筆", 30),
    ]
    
    for i, (message, is_group, description, expected_limit) in enumerate(test_cases, 1):
        print(f"\n🧪 測試 {i}: {description}")
        print(f"   訊息: '{message}'")
        print(f"   模式: {'群組' if is_group else '私聊'}")
        print(f"   預期筆數: {expected_limit}")
        
        try:
            response = bot.handle_message(test_user_id, message, is_group)
            
            if response is None:
                print(f"   ❌ 無回應")
            else:
                print(f"   ✅ 有回應")
                
                # 檢查回應內容是否包含正確的筆數信息
                if hasattr(response, 'text'):
                    text = response.text
                    
                    # 檢查是否包含預期的筆數描述
                    if f"最近 {expected_limit} 筆" in text or f"最近 0 筆" in text:
                        print(f"   ✅ 筆數正確: 找到預期的筆數描述")
                    elif "最近" in text and "筆" in text:
                        # 提取實際筆數
                        import re
                        match = re.search(r'最近 (\d+) 筆', text)
                        if match:
                            actual_limit = int(match.group(1))
                            if actual_limit <= expected_limit:
                                print(f"   ✅ 筆數合理: 實際 {actual_limit} 筆 (≤ 預期 {expected_limit} 筆)")
                            else:
                                print(f"   ⚠️ 筆數異常: 實際 {actual_limit} 筆 (> 預期 {expected_limit} 筆)")
                        else:
                            print(f"   ⚠️ 無法解析筆數信息")
                    else:
                        print(f"   ⚠️ 回應中沒有筆數信息")
                    
                    # 檢查是否有警告訊息（超限時）
                    if expected_limit == 50 and "最多只能查詢 50 筆" in text:
                        print(f"   ✅ 包含超限警告訊息")
                    elif expected_limit == 5 and message.endswith('0') and "數量不能小於 1" in text:
                        print(f"   ✅ 包含無效數量警告訊息")
                    
                    # 顯示回應預覽
                    preview = text[:80] + "..." if len(text) > 80 else text
                    print(f"   內容預覽: {preview}")
                
        except Exception as e:
            print(f"   ❌ 測試錯誤: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 查詢筆數功能測試完成！")

def test_pattern_matching():
    """測試正則表達式模式匹配"""
    bot = ExpenseBot()
    
    print("\n🧪 模式匹配測試...")
    print("=" * 40)
    
    # @ai 查詢指令測試
    ai_query_tests = [
        ("@ai 查詢", True),
        ("@ai 查詢 10", True),
        ("@ai 查詢  15", True),  # 有空格
        ("@ai 記錄", True),
        ("@ai 記錄 20", True),
        ("@ai 最近", True),
        ("@ai 最近 5", True),
        ("@ai list", True),
        ("@ai list 12", True),
        ("@ai 查詢abc", False),  # 無空格分隔
        ("@ai 查詢記錄", False),  # 不匹配模式
        ("@ai 午餐 120", False),  # 記帳指令
    ]
    
    print("📊 @ai 查詢指令匹配測試:")
    for message, expected in ai_query_tests:
        result = bot.is_ai_query_command(message)
        status = "✅" if result == expected else "❌"
        print(f"   {status} '{message}' -> {result} (預期: {expected})")
    
    # 數字查詢指令測試
    number_query_tests = [
        ("查詢10", True),
        ("查詢5", True),
        ("記錄20", True),
        ("最近15", True),
        ("list30", True),
        ("查詢", False),  # 沒有數字
        ("查詢 10", False),  # 有空格
        ("10查詢", False),  # 順序錯誤
        ("查詢abc", False),  # 非數字
    ]
    
    print("\n📊 數字查詢指令匹配測試:")
    for message, expected in number_query_tests:
        result = bot.is_number_query_command(message)
        status = "✅" if result == expected else "❌"
        print(f"   {status} '{message}' -> {result} (預期: {expected})")

if __name__ == "__main__":
    print("🚀 開始測試查詢筆數功能...")
    
    # 模式匹配測試
    test_pattern_matching()
    
    # 功能完整測試
    test_query_limit_functionality()
    
    print("\n🎉 所有測試完成！")
    print("\n💡 測試重點：")
    print("   • @ai 查詢 [數字] 在群組和私聊中都能運作")
    print("   • 查詢[數字] 只在私聊中運作")
    print("   • 數量限制：1-50 筆，超出範圍會自動調整")
    print("   • 不同模式提供不同的快速回覆按鈕")
    print("   • 支援中英文查詢指令")
    
    print("\n📝 使用範例：")
    print("   群組: @ai 查詢 10")
    print("   私聊: 查詢10 或 @ai 查詢 10")
    print("   範圍: 1-50 筆") 