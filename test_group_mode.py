#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
群組模式測試腳本
測試在群組和私聊模式下的不同行為
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from line_bot import ExpenseBot

def test_group_mode():
    """測試群組模式功能"""
    bot = ExpenseBot()
    test_user_id = "test_user_12345"
    
    print("🧪 群組模式測試開始...")
    print("=" * 50)
    
    # 測試案例
    test_cases = [
        # (訊息, 是否群組, 預期是否有回應, 描述)
        ("你好", True, False, "群組中一般問候"),
        ("指令", True, False, "群組中查詢指令"),
        ("@ai 你好", True, True, "群組中 @ai 問候"),
        ("@ai ?", True, True, "群組中 @ai 求助"),
        ("@ai 指令", True, True, "群組中 @ai 查詢指令"),
        ("@ai 午餐 120", True, True, "群組中 @ai 記帳"),
        ("@ai /del #1", True, True, "群組中 @ai 刪除"),
        ("@ai 錯誤格式", True, True, "群組中 @ai 錯誤格式"),
        
        ("你好", False, True, "私聊中一般問候"),
        ("指令", False, True, "私聊中查詢指令"),
        ("@ai 你好", False, True, "私聊中 @ai 問候"),
        ("@ai ?", False, True, "私聊中 @ai 求助"),
        ("@ai 午餐 120", False, True, "私聊中 @ai 記帳"),
        ("隨便聊天", False, True, "私聊中隨便聊天"),
    ]
    
    for i, (message, is_group, expect_response, description) in enumerate(test_cases, 1):
        print(f"\n🧪 測試 {i}: {description}")
        print(f"   訊息: '{message}'")
        print(f"   模式: {'群組' if is_group else '私聊'}")
        print(f"   預期: {'有回應' if expect_response else '無回應'}")
        
        try:
            response = bot.handle_message(test_user_id, message, is_group)
            
            if response is None:
                actual_response = False
                print(f"   實際: 無回應 ✅" if not expect_response else "   實際: 無回應 ❌")
            else:
                actual_response = True
                print(f"   實際: 有回應 ✅" if expect_response else "   實際: 有回應 ❌")
                
                # 顯示回應內容的前100字
                if hasattr(response, 'text'):
                    text_preview = response.text[:100] + "..." if len(response.text) > 100 else response.text
                    print(f"   內容: {text_preview}")
            
            # 檢查結果
            if actual_response == expect_response:
                print(f"   ✅ 測試通過")
            else:
                print(f"   ❌ 測試失敗")
                
        except Exception as e:
            print(f"   ❌ 測試錯誤: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 群組模式測試完成！")

def test_ai_help_commands():
    """測試 @ai 幫助指令"""
    bot = ExpenseBot()
    test_user_id = "test_user_12345"
    
    print("\n🧪 @ai 幫助指令測試...")
    print("=" * 50)
    
    help_commands = [
        "@ai ?",
        "@ai help",
        "@ai 幫助",
        "@ai 指令",
        "@ai 功能",
        "@ai 歡迎",
        "@ai hello",
        "@ai menu"
    ]
    
    for cmd in help_commands:
        print(f"\n🧪 測試指令: '{cmd}'")
        
        # 測試群組模式
        print("   群組模式:")
        try:
            response = bot.handle_message(test_user_id, cmd, is_group=True)
            if response:
                print(f"   ✅ 有回應")
                # 顯示前50字
                text_preview = response.text[:50] + "..." if len(response.text) > 50 else response.text
                print(f"   內容: {text_preview}")
            else:
                print(f"   ❌ 無回應")
        except Exception as e:
            print(f"   ❌ 錯誤: {e}")
        
        # 測試私聊模式
        print("   私聊模式:")
        try:
            response = bot.handle_message(test_user_id, cmd, is_group=False)
            if response:
                print(f"   ✅ 有回應")
                # 顯示前50字
                text_preview = response.text[:50] + "..." if len(response.text) > 50 else response.text
                print(f"   內容: {text_preview}")
            else:
                print(f"   ❌ 無回應")
        except Exception as e:
            print(f"   ❌ 錯誤: {e}")

if __name__ == "__main__":
    print("🚀 開始測試群組模式功能...")
    
    # 基本群組模式測試
    test_group_mode()
    
    # @ai 幫助指令測試
    test_ai_help_commands()
    
    print("\n🎉 所有測試完成！")
    print("\n💡 測試重點：")
    print("   • 群組中只有 @ai 開頭的訊息會被回應")
    print("   • 私聊中所有訊息都會被回應")
    print("   • @ai 幫助指令在群組和私聊中都能正常運作")
    print("   • 群組和私聊模式會顯示不同的說明內容") 