#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LINE 記帳機器人啟動腳本
"""

import os
import sys
from config import LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET

def check_environment():
    """檢查環境設定"""
    print("🔍 檢查環境設定...")
    
    # 檢查 TOKEN 和 SECRET
    if LINE_CHANNEL_ACCESS_TOKEN == 'your_channel_access_token_here':
        print("❌ 請設定 LINE_CHANNEL_ACCESS_TOKEN")
        return False
    
    if LINE_CHANNEL_SECRET == 'your_channel_secret_here':
        print("❌ 請設定 LINE_CHANNEL_SECRET")
        return False
    
    print("✅ 環境設定檢查完成")
    return True

def main():
    """主函數"""
    print("🤖 LINE 記帳機器人")
    print("=" * 40)
    
    # 檢查環境
    if not check_environment():
        print("\n📝 設定步驟:")
        print("1. 建立 .env 檔案")
        print("2. 設定 LINE_CHANNEL_ACCESS_TOKEN 和 LINE_CHANNEL_SECRET")
        print("3. 重新執行此腳本")
        return
    
    # 初始化資料庫
    print("📊 初始化資料庫...")
    from database import ExpenseDatabase
    db = ExpenseDatabase()
    print("✅ 資料庫初始化完成")
    
    # 測試訊息解析器
    print("🧪 測試訊息解析器...")
    from message_parser import MessageParser
    parser = MessageParser()
    test_result = parser.parse_message("測試在7-11買飲料50元")
    if test_result['amount'] == 50.0:
        print("✅ 訊息解析器測試通過")
    else:
        print("❌ 訊息解析器測試失敗")
        return
    
    print("\n🚀 啟動 LINE Bot...")
    print("📡 Webhook URL: http://localhost:5000/callback")
    print("💡 提示: 使用 ngrok 建立公開 URL 用於測試")
    
    # 啟動應用程式
    from line_bot import app, PORT
    app.run(host='0.0.0.0', port=PORT, debug=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 程式已停止")
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        sys.exit(1) 