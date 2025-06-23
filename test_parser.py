#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
測試腳本：驗證訊息解析器功能
"""

from message_parser import MessageParser

def test_message_parser():
    """測試訊息解析器的各種情況"""
    parser = MessageParser()
    
    # 測試案例
    test_cases = [
        "在7-11買飲料50元",
        "午餐花了120塊",
        "停車費30元",
        "星巴克咖啡150",
        "捷運車費26元",
        "麥當勞吃午餐89元",
        "買衣服花了1500",
        "看電影票價280元",
        "油錢加了800塊",
        "在全家買零食45元",
        "計程車費120",
        "診所掛號費150元",
        "KTV唱歌500元",
        "便利商店買東西35塊",
        "NT$200買書",
        "$50飲料",
        "花了65元買咖啡",
        "今天天氣很好",  # 沒有金額的測試
        "100",  # 只有數字
    ]
    
    print("🧪 訊息解析器測試結果:\n")
    print("=" * 60)
    
    for i, test_message in enumerate(test_cases, 1):
        print(f"\n測試 {i}: {test_message}")
        print("-" * 40)
        
        # 解析訊息
        result = parser.parse_message(test_message)
        
        # 顯示結果
        print(f"💰 金額: {result['amount']}")
        print(f"📍 地點: {result['location']}")
        print(f"🏷️ 類別: {result['category']}")
        print(f"📝 描述: {result['description']}")
        
        # 檢查是否為有效支出
        is_valid = parser.is_valid_expense(result)
        print(f"✅ 有效支出: {is_valid}")
        
        # 如果是有效支出，顯示格式化摘要
        if is_valid:
            summary = parser.format_expense_summary(result)
            print(f"📋 摘要:\n{summary}")

if __name__ == "__main__":
    test_message_parser() 