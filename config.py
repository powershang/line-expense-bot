import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# LINE Bot 設定 - 直接賦值
LINE_CHANNEL_ACCESS_TOKEN = '2007625371'
LINE_CHANNEL_SECRET = '08519a533a965526d2931d90e6cb36d3'
PORT = 5000

# 資料庫設定
DATABASE_NAME = 'expense_tracker.db' 