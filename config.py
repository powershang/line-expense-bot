import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 檢查是否為調試模式
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'

# LINE Bot 設定 - 從環境變數讀取（必須設定）
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
PORT = int(os.getenv('PORT', 5000))

# 在調試模式下使用假值
if DEBUG_MODE:
    if not LINE_CHANNEL_ACCESS_TOKEN:
        LINE_CHANNEL_ACCESS_TOKEN = 'dummy_token_for_local_debug'
    if not LINE_CHANNEL_SECRET:
        LINE_CHANNEL_SECRET = 'dummy_secret_for_local_debug'

# 檢查必要的環境變數（非調試模式才檢查）
if not DEBUG_MODE:
    if not LINE_CHANNEL_ACCESS_TOKEN:
        raise ValueError("❌ 錯誤：環境變數 LINE_CHANNEL_ACCESS_TOKEN 未設定")

    if not LINE_CHANNEL_SECRET:
        raise ValueError("❌ 錯誤：環境變數 LINE_CHANNEL_SECRET 未設定")

# 資料庫設定
DATABASE_URL = os.getenv('DATABASE_URL')  # PostgreSQL URL
DATABASE_NAME = 'expense_tracker.db'  # SQLite fallback 