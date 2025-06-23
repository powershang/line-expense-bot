# LINE 記帳機器人

一個使用 LINE Messaging API 建立的智能記帳機器人，可以自動解析用戶的自然語言訊息，提取地點和金額資訊，並自動記錄支出。

## 功能特色

- 🤖 **自然語言處理**: 支援自然語言記帳，自動識別金額和地點
- 📍 **地點識別**: 自動提取消費地點資訊
- 🏷️ **智能分類**: 根據關鍵字自動分類支出類型
- 📊 **統計分析**: 提供月度支出摘要和統計
- 💬 **友善介面**: 使用 LINE 聊天機器人，操作簡單直覺

## 支援的記帳格式

### 自然語言範例
- "在7-11買飲料50元"
- "午餐花了120塊" 
- "停車費30元"
- "星巴克咖啡150"
- "捷運車費26元"

### 支援的金額格式
- `100元`, `250.5元`
- `100塊`
- `NT$100`, `NT100`
- `$100`
- `花了100`, `花100`

## 自動分類功能

機器人會根據關鍵字自動將支出分類：

- **餐飲**: 餐廳、咖啡、飲料、早餐、午餐、晚餐等
- **購物**: 超市、商店、衣服、鞋子、包包等
- **交通**: 車費、油錢、停車、捷運、公車、計程車等
- **娛樂**: 電影、遊戲、KTV等
- **醫療**: 看病、藥品、診所、醫院等
- **其他**: 未分類項目

## 安裝與設定

### 1. 安裝依賴套件

```bash
pip install -r requirements.txt
```

### 2. 建立 LINE Bot

1. 前往 [LINE Developers Console](https://developers.line.biz/)
2. 建立新的 Provider 和 Channel (Messaging API)
3. 取得 `Channel Access Token` 和 `Channel Secret`

### 3. 設定環境變數

建立 `.env` 檔案並設定以下變數：

```env
LINE_CHANNEL_ACCESS_TOKEN=你的_Channel_Access_Token
LINE_CHANNEL_SECRET=你的_Channel_Secret
PORT=5000
```

### 4. 設定 Webhook URL

在 LINE Developers Console 中設定 Webhook URL：
```
https://your-domain.com/callback
```

### 5. 啟動應用程式

```bash
python line_bot.py
```

## 使用方法

### 基本指令

- **記帳**: 輸入 "記帳" 查看記帳格式說明
- **查詢**: 輸入 "查詢" 查看最近的支出記錄
- **本月**: 輸入 "本月" 查看本月支出摘要
- **幫助**: 輸入 "幫助" 或 "說明" 查看使用說明

### 記帳方式

直接輸入包含金額的自然語言訊息即可記帳：

**範例對話:**
```
用戶: 在麥當勞吃午餐89元
機器人: ✅ 記帳成功！
       💰 金額: 89.0 元
       📍 地點: 麥當勞
       🏷️ 類別: 餐飲
       記錄編號: #1

用戶: 查詢
機器人: 📋 最近 5 筆支出記錄:
       #1 - 12/15 14:30
       💰 89.0 元 | 📍 麥當勞 | 🏷️ 餐飲
       
       總計: 89.0 元
```

## 專案結構

```
line_記帳/
├── line_bot.py          # 主要應用程式
├── config.py            # 設定檔
├── database.py          # 資料庫操作
├── message_parser.py    # 訊息解析器
├── requirements.txt     # Python 依賴套件
└── README.md           # 專案說明
```

## 部署建議

### 使用 ngrok (開發測試)

```bash
# 安裝 ngrok
# 啟動應用程式
python line_bot.py

# 在另一個終端執行
ngrok http 5000
```

### 雲端部署

推薦部署到以下平台：
- Heroku
- Render
- Railway
- Vercel

記得在部署平台設定環境變數。

## 注意事項

1. 請確保 LINE Bot 的 Channel Access Token 和 Channel Secret 正確設定
2. Webhook URL 必須是 HTTPS
3. 資料庫檔案 `expense_tracker.db` 會自動建立
4. 建議定期備份資料庫檔案

## 故障排除

### 常見問題

**Q: 機器人沒有回應**
A: 檢查 Webhook URL 是否正確設定，以及 TOKEN 和 SECRET 是否正確

**Q: 無法識別金額**
A: 確保訊息中包含明確的數字和金額單位（元、塊、$等）

**Q: 地點識別不準確**
A: 可以在訊息中加入地點關鍵字（在、於、到、去等）

## 擴展功能

可以考慮加入的功能：
- 支出預算警告
- 圖表統計顯示
- 匯出 Excel 報表
- 多人共用記帳
- 發票 OCR 識別

## 授權

MIT License 