import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# LINE Bot 設定 - 從環境變數讀取（必須設定）
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
PORT = int(os.getenv('PORT', 5000))

# 檢查必要的環境變數
if not LINE_CHANNEL_ACCESS_TOKEN:
    raise ValueError("❌ 錯誤：環境變數 LINE_CHANNEL_ACCESS_TOKEN 未設定")

if not LINE_CHANNEL_SECRET:
    raise ValueError("❌ 錯誤：環境變數 LINE_CHANNEL_SECRET 未設定")

# 資料庫設定
DATABASE_URL = os.getenv('DATABASE_URL')  # PostgreSQL URL
DATABASE_NAME = 'expense_tracker.db'  # SQLite fallback 