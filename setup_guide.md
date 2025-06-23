# LINE 記帳機器人設定指南

## 步驟 1: 建立 LINE Bot

1. 前往 [LINE Developers Console](https://developers.line.biz/)
2. 登入你的 LINE 帳號
3. 建立新的 Provider（如果還沒有的話）
4. 在 Provider 下建立新的 Channel，選擇 "Messaging API"
5. 填寫 Channel 資訊：
   - Channel name: LINE 記帳機器人
   - Channel description: 智能記帳助手
   - Category: 生活
   - Subcategory: 其他

## 步驟 2: 取得必要的金鑰

在 Channel 設定頁面中：

1. **Channel Access Token**:
   - 到 "Basic settings" 頁籤
   - 在 "Channel access token" 區域點擊 "Issue"
   - 複製產生的 token

2. **Channel Secret**:
   - 在 "Basic settings" 頁籤
   - 複製 "Channel secret" 的值

## 步驟 3: 建立環境變數檔案

在專案根目錄建立 `.env` 檔案：

```env
# LINE Bot 設定
LINE_CHANNEL_ACCESS_TOKEN=你的_Channel_Access_Token
LINE_CHANNEL_SECRET=你的_Channel_Secret

# 伺服器設定
PORT=5000
```

## 步驟 4: 設定 Webhook URL

### 使用 ngrok (開發測試)

1. 下載並安裝 [ngrok](https://ngrok.com/)
2. 啟動應用程式：
   ```bash
   python start.py
   ```
3. 在另一個終端執行：
   ```bash
   ngrok http 5000
   ```
4. 複製 ngrok 提供的 HTTPS URL，例如：`https://abc123.ngrok.io`

### 在 LINE Developers Console 設定 Webhook

1. 到 Channel 的 "Messaging API" 頁籤
2. 在 "Webhook settings" 區域：
   - Webhook URL: `https://your-ngrok-url.ngrok.io/callback`
   - 點擊 "Update"
   - 啟用 "Use webhook"

## 步驟 5: 啟用機器人功能

在 "Messaging API" 頁籤中：

1. **Auto-reply messages**: 停用
2. **Greeting messages**: 可選擇啟用或停用
3. **Webhook**: 啟用

## 步驟 6: 加入機器人為好友

1. 在 "Messaging API" 頁籤找到 QR code
2. 用手機 LINE 掃描 QR code 加入機器人為好友

## 步驟 7: 測試機器人

發送以下訊息測試：

- `幫助` - 查看使用說明
- `在7-11買飲料50元` - 測試記帳功能
- `查詢` - 查看記錄

## 常見問題

### Q: 機器人沒有回應
**A**: 檢查以下項目：
- Webhook URL 是否正確設定
- TOKEN 和 SECRET 是否正確
- ngrok 是否正在運行
- 應用程式是否正在運行

### Q: 無法識別金額
**A**: 確保訊息包含明確的數字和金額單位（元、塊、$、NT$等）

### Q: 地點識別不準確
**A**: 可以在訊息中加入地點關鍵字（在、於、到、去等）

## 部署到雲端平台

### Heroku 部署

1. 建立 `Procfile`：
   ```
   web: python line_bot.py
   ```

2. 設定環境變數：
   ```bash
   heroku config:set LINE_CHANNEL_ACCESS_TOKEN=你的token
   heroku config:set LINE_CHANNEL_SECRET=你的secret
   ```

3. 部署：
   ```bash
   git add .
   git commit -m "Deploy LINE bot"
   git push heroku main
   ```

### Render 部署

1. 連接 GitHub 倉庫
2. 設定環境變數
3. 啟動指令：`python line_bot.py`

## 安全注意事項

1. **不要** 將 `.env` 檔案提交到 Git
2. **不要** 在程式碼中硬編碼 TOKEN 和 SECRET
3. 定期更新 Channel Access Token
4. 監控機器人的使用狀況 