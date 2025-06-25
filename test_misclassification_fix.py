#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
誤判修復測試腳本
測試 @ai list 90 等查詢指令不會被誤判為記帳
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from line_bot import ExpenseBot

def test_misclassification_fix():
    """測試誤判修復"""
    bot = ExpenseBot()
    test_user_id = "test_user_fix"
    
    print("🧪 誤判修復測試開始...")
    print("=" * 60)
    
    # 測試案例 - 這些應該是查詢，不是記帳
    query_cases = [
        ("@ai list 90", True, "群組中查詢 90 筆"),
        ("@ai 查詢 50", True, "群組中查詢 50 筆"),
        ("@ai 記錄 20", True, "群組中查詢 20 筆記錄"),
        ("@ai 最近 15", True, "群組中查詢最近 15 筆"),
        ("@ai list 10", False, "私聊中查詢 10 筆"),
        ("@ai 查詢 30", False, "私聊中查詢 30 筆"),
    ]
    
    # 測試案例 - 這些應該是記帳，不是查詢
    expense_cases = [
        ("@ai 午餐 120", True, "群組中記帳午餐"),
        ("@ai 咖啡 50", True, "群組中記帳咖啡"),
        ("@ai 停車費 30", False, "私聊中記帳停車費"),
        ("@ai 買書 200", False, "私聊中記帳買書"),
    ]
    
    # 測試案例 - 這些應該是幫助指令
    help_cases = [
        ("@ai ?", True, "群組中求助"),
        ("@ai 指令", True, "群組中查詢指令"),
        ("@ai 幫助", False, "私聊中求助"),
        ("@ai help", False, "私聊中英文求助"),
    ]
    
    print("\n📊 測試查詢指令（不應被誤判為記帳）:")
    for message, is_group, description in query_cases:
        print(f"\n🧪 測試: {description}")
        print(f"   訊息: '{message}'")
        
        try:
            response = bot.handle_message(test_user_id, message, is_group)
            
            if response and hasattr(response, 'text'):
                text = response.text
                
                # 檢查是否為查詢回應（包含"最近"和"筆"）
                if "最近" in text and "筆" in text:
                    print(f"   ✅ 正確識別為查詢指令")
                    # 顯示回應的前50字
                    preview = text[:50] + "..." if len(text) > 50 else text
                    print(f"   內容: {preview}")
                elif "記帳成功" in text:
                    print(f"   ❌ 錯誤：被誤判為記帳!")
                    print(f"   內容: {text[:100]}")
                else:
                    print(f"   ⚠️ 其他回應類型")
                    preview = text[:50] + "..." if len(text) > 50 else text
                    print(f"   內容: {preview}")
            else:
                print(f"   ❌ 無回應")
                
        except Exception as e:
            print(f"   ❌ 測試錯誤: {e}")
    
    print("\n💰 測試記帳指令（應正確識別為記帳）:")
    for message, is_group, description in expense_cases:
        print(f"\n🧪 測試: {description}")
        print(f"   訊息: '{message}'")
        
        try:
            response = bot.handle_message(test_user_id, message, is_group)
            
            if response and hasattr(response, 'text'):
                text = response.text
                
                if "記帳成功" in text:
                    print(f"   ✅ 正確識別為記帳指令")
                    # 顯示記錄編號
                    import re
                    match = re.search(r'記錄編號: #(\d+)', text)
                    if match:
                        print(f"   記錄編號: #{match.group(1)}")
                elif "最近" in text and "筆" in text:
                    print(f"   ❌ 錯誤：被誤判為查詢!")
                    print(f"   內容: {text[:100]}")
                else:
                    print(f"   ⚠️ 其他回應類型")
                    preview = text[:50] + "..." if len(text) > 50 else text
                    print(f"   內容: {preview}")
            else:
                print(f"   ❌ 無回應")
                
        except Exception as e:
            print(f"   ❌ 測試錯誤: {e}")
    
    print("\n❓ 測試幫助指令（應正確識別為幫助）:")
    for message, is_group, description in help_cases:
        print(f"\n🧪 測試: {description}")
        print(f"   訊息: '{message}'")
        
        try:
            response = bot.handle_message(test_user_id, message, is_group)
            
            if response and hasattr(response, 'text'):
                text = response.text
                
                if "幫助" in text or "指令" in text or "歡迎" in text:
                    print(f"   ✅ 正確識別為幫助指令")
                elif "記帳成功" in text:
                    print(f"   ❌ 錯誤：被誤判為記帳!")
                elif "最近" in text and "筆" in text:
                    print(f"   ❌ 錯誤：被誤判為查詢!")
                else:
                    print(f"   ✅ 正確的幫助回應")
                
                preview = text[:50] + "..." if len(text) > 50 else text
                print(f"   內容: {preview}")
            else:
                print(f"   ❌ 無回應")
                
        except Exception as e:
            print(f"   ❌ 測試錯誤: {e}")

def test_edge_cases():
    """測試邊界案例"""
    bot = ExpenseBot()
    test_user_id = "test_edge_user"
    
    print("\n🧪 邊界案例測試...")
    print("=" * 40)
    
    edge_cases = [
        ("@ai list", True, "list 沒有數字 - 應為查詢預設5筆"),
        ("@ai 查詢", True, "查詢沒有數字 - 應為查詢預設5筆"),
        ("@ai list abc", True, "list 無效數字 - 應為查詢預設5筆"),
        ("@ai 查詢 abc", True, "查詢無效數字 - 應為查詢預設5筆"),
        ("@ai list50", True, "list50 連寫 - 應為記帳誤判修正"),
        ("@ai 記錄50", True, "記錄50 連寫 - 應為記帳"),
    ]
    
    for message, is_group, description in edge_cases:
        print(f"\n🧪 測試: {description}")
        print(f"   訊息: '{message}'")
        
        try:
            response = bot.handle_message(test_user_id, message, is_group)
            
            if response and hasattr(response, 'text'):
                text = response.text
                
                if "最近" in text and "筆" in text:
                    print(f"   ✅ 識別為查詢指令")
                elif "記帳成功" in text:
                    print(f"   ⚠️ 識別為記帳指令")
                elif "格式不正確" in text or "幫助" in text:
                    print(f"   ⚠️ 識別為格式錯誤或幫助")
                else:
                    print(f"   ⚠️ 其他類型回應")
                
                preview = text[:60] + "..." if len(text) > 60 else text
                print(f"   內容: {preview}")
            else:
                print(f"   ❌ 無回應")
                
        except Exception as e:
            print(f"   ❌ 測試錯誤: {e}")

if __name__ == "__main__":
    print("🚀 開始測試誤判修復...")
    
    # 主要誤判修復測試
    test_misclassification_fix()
    
    # 邊界案例測試
    test_edge_cases()
    
    print("\n" + "=" * 60)
    print("🎉 誤判修復測試完成！")
    
    print("\n💡 修復重點：")
    print("   • @ai 查詢指令優先於記帳解析檢查")
    print("   • @ai list 90 正確識別為查詢 90 筆")
    print("   • @ai 午餐 120 仍正確識別為記帳")
    print("   • 避免數字被誤判為金額")
    
    print("\n📝 測試的指令：")
    print("   查詢: @ai list 90, @ai 查詢 50")
    print("   記帳: @ai 午餐 120, @ai 咖啡 50")
    print("   幫助: @ai ?, @ai 指令") 