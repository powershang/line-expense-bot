import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# LINE Bot 設定 - 從環境變數讀取
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'Pujs/XlSgumYRMVYiLPJEGtrIJwU1FHrD2hetVOqZ2lp/bQgPWSk1CdX/ndpVqDGeYQCe1DaKJ/mOoFkV/9f3G4sqgitf8Yi4Cvm3AuEoGZOzkCdQhbI6KCCTRz8HAdt3VDZ1ucePxNR8Bxx1AS6GgdB04t89/1O/w1cDnyilFU=')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', '08519a533a965526d2931d90e6cb36d3')
PORT = int(os.getenv('PORT', 5000))

# 資料庫設定
DATABASE_URL = os.getenv('DATABASE_URL')  # PostgreSQL URL
DATABASE_NAME = 'expense_tracker.db'  # SQLite fallback 