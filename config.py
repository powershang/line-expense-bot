import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# LINE Bot 設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'your_channel_access_token_here')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', 'your_channel_secret_here')
PORT = int(os.getenv('PORT', 5000))

# 資料庫設定
DATABASE_NAME = 'expense_tracker.db' 