import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# LINE Bot 設定 - 直接賦值
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
PORT = 5000

# 資料庫設定
DATABASE_NAME = 'expense_tracker.db' 