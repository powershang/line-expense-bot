# n8n LINE 記帳機器人工作流設計

## 🎯 概述

使用 n8n 建立 LINE 記帳機器人的完整工作流設計，無需寫程式碼即可實現智能記帳功能。

## 📊 主要工作流結構

```
LINE Webhook → 解析訊息 → 判斷訊息類型 → 處理邏輯 → 回應用戶
```

## 🔧 詳細節點設計

### 1. Webhook 節點（接收 LINE 訊息）
- **節點類型**: Webhook
- **方法**: POST
- **路徑**: `/line-webhook`
- **用途**: 接收來自 LINE 的訊息

### 2. Function 節點（解析 LINE 資料）
```javascript
// 解析 LINE webhook 資料
const events = $json.events;
if (!events || events.length === 0) {
  return [];
}

const event = events[0];
const messageText = event.message?.text || '';
const userId = event.source?.userId || '';
const replyToken = event.replyToken || '';

return [{
  messageText,
  userId,
  replyToken,
  timestamp: new Date().toISOString()
}];
```

### 3. Switch 節點（判斷訊息類型）
**分支條件**:
- **查詢指令**: `{{ $json.messageText }}` equals `查詢`
- **本月指令**: `{{ $json.messageText }}` equals `本月`
- **幫助指令**: `{{ $json.messageText }}` equals `幫助`
- **記帳訊息**: 預設分支

### 4. Function 節點（金額解析）
```javascript
// 解析金額的正則表達式邏輯
const text = $json.messageText;

// 金額匹配模式
const amountPatterns = [
  /(\d+(?:\.\d+)?)\s*元/,
  /(\d+(?:\.\d+)?)\s*塊/,
  /NT\$?\s*(\d+(?:\.\d+)?)/,
  /\$\s*(\d+(?:\.\d+)?)/,
  /花了?\s*(\d+(?:\.\d+)?)/,
  /(\d+(?:\.\d+)?)\s*錢/
];

let amount = null;
for (const pattern of amountPatterns) {
  const match = text.match(pattern);
  if (match) {
    amount = parseFloat(match[1]);
    break;
  }
}

// 如果沒有明確模式，尋找純數字
if (!amount) {
  const numbers = text.match(/\d+(?:\.\d+)?/g);
  if (numbers) {
    amount = Math.max(...numbers.map(n => parseFloat(n)));
  }
}

// 地點識別
const locationKeywords = ['在', '於', '到', '去', '買', '吃'];
let location = null;

for (const keyword of locationKeywords) {
  const regex = new RegExp(`${keyword}([^，,。！？\\s]+)`);
  const match = text.match(regex);
  if (match) {
    location = match[1].trim();
    break;
  }
}

// 類別識別
const categoryMap = {
  '餐廳': '餐飲', '吃': '餐飲', '午餐': '餐飲', '咖啡': '餐飲',
  '超市': '購物', '買': '購物', '衣服': '購物',
  '車費': '交通', '停車': '交通', '捷運': '交通',
  '電影': '娛樂', 'ktv': '娛樂',
  '醫院': '醫療', '診所': '醫療'
};

let category = '其他';
for (const [keyword, cat] of Object.entries(categoryMap)) {
  if (text.toLowerCase().includes(keyword)) {
    category = cat;
    break;
  }
}

return [{
  ...json,
  amount,
  location,
  category,
  isValidExpense: amount && amount > 0
}];
```

### 5. PostgreSQL/MySQL 節點（儲存記帳資料）
**操作**: Insert
**SQL**:
```sql
INSERT INTO expenses (user_id, amount, location, description, category, timestamp)
VALUES ('{{ $json.userId }}', {{ $json.amount }}, '{{ $json.location }}', '{{ $json.messageText }}', '{{ $json.category }}', NOW())
RETURNING id;
```

### 6. Function 節點（組裝回應訊息）
```javascript
const { amount, location, category, isValidExpense } = $json;

if (!isValidExpense) {
  return [{
    replyText: `🤔 無法識別金額: "${$json.messageText}"\n\n💡 請試試:\n• "在7-11買飲料50元"\n• "午餐花了120塊"\n• "停車費30元"`
  }];
}

let response = `✅ 記帳成功！\n\n💰 金額: ${amount} 元`;
if (location) response += `\n📍 地點: ${location}`;
if (category) response += `\n🏷️ 類別: ${category}`;

// 假設從資料庫插入返回了 ID
const expenseId = $('PostgreSQL').item(0).json.id;
response += `\n\n記錄編號: #${expenseId}`;

return [{ replyText: response }];
```

### 7. HTTP Request 節點（回應 LINE）
**方法**: POST
**URL**: `https://api.line.me/v2/bot/message/reply`
**Headers**:
```json
{
  "Authorization": "Bearer YOUR_CHANNEL_ACCESS_TOKEN",
  "Content-Type": "application/json"
}
```
**Body**:
```json
{
  "replyToken": "{{ $json.replyToken }}",
  "messages": [
    {
      "type": "text",
      "text": "{{ $json.replyText }}"
    }
  ]
}
```

## 🔍 查詢功能工作流

### 1. PostgreSQL 節點（查詢最近記錄）
```sql
SELECT id, amount, location, category, timestamp
FROM expenses 
WHERE user_id = '{{ $json.userId }}'
ORDER BY timestamp DESC
LIMIT 5;
```

### 2. Function 節點（格式化查詢結果）
```javascript
const expenses = $json;
if (!expenses || expenses.length === 0) {
  return [{ replyText: "📋 目前沒有支出記錄。" }];
}

let response = "📋 最近 5 筆支出記錄:\n\n";
let total = 0;

expenses.forEach((expense, index) => {
  total += expense.amount;
  const date = new Date(expense.timestamp).toLocaleDateString('zh-TW', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
  
  response += `#${expense.id} - ${date}\n`;
  response += `💰 ${expense.amount} 元`;
  if (expense.location) response += ` | 📍 ${expense.location}`;
  if (expense.category) response += ` | 🏷️ ${expense.category}`;
  response += "\n\n";
});

response += `總計: ${total} 元`;
return [{ replyText: response }];
```

## 📊 月度摘要工作流

### 1. PostgreSQL 節點（查詢月度資料）
```sql
SELECT SUM(amount) as total_amount, COUNT(*) as count, category
FROM expenses 
WHERE user_id = '{{ $json.userId }}'
  AND EXTRACT(YEAR FROM timestamp) = EXTRACT(YEAR FROM NOW())
  AND EXTRACT(MONTH FROM timestamp) = EXTRACT(MONTH FROM NOW())
GROUP BY category;
```

### 2. Function 節點（格式化月度摘要）
```javascript
const summary = $json;
if (!summary || summary.length === 0) {
  const currentMonth = new Date().getMonth() + 1;
  const currentYear = new Date().getFullYear();
  return [{ 
    replyText: `📊 ${currentYear}年${currentMonth}月目前沒有支出記錄。` 
  }];
}

let response = `📊 ${new Date().getFullYear()}年${new Date().getMonth() + 1}月支出摘要:\n\n`;
let totalAmount = 0;
let totalCount = 0;

summary.forEach(item => {
  totalAmount += item.total_amount;
  totalCount += item.count;
  response += `🏷️ ${item.category || '其他'}: ${item.total_amount} 元 (${item.count} 筆)\n`;
});

response += `\n💳 總支出: ${totalAmount} 元`;
response += `\n📝 總筆數: ${totalCount} 筆`;
if (totalCount > 0) {
  const avg = totalAmount / totalCount;
  response += `\n📈 平均: ${avg.toFixed(1)} 元/筆`;
}

return [{ replyText: response }];
```

## 🚀 部署設定

### 1. n8n 安裝
```bash
# 使用 Docker
docker run -it --rm --name n8n -p 5678:5678 n8nio/n8n

# 或使用 npm
npm install n8n -g
n8n start
```

### 2. 資料庫設定
- 設定 PostgreSQL 或 MySQL 連線
- 建立 expenses 資料表

### 3. LINE Webhook 設定
- 在 n8n 中啟動工作流
- 取得 Webhook URL（例如：`https://your-n8n.com/webhook/line-webhook`）
- 在 LINE Developers Console 設定此 URL

## ✅ 優點

1. **視覺化開發**: 拖拉即可建立流程
2. **快速原型**: 快速測試和調整
3. **內建節點**: 豐富的預設功能
4. **易於維護**: 非程式人員也能理解和修改
5. **擴展性**: 容易加入新功能

## ❌ 限制

1. **複雜邏輯**: 複雜的文字解析可能較困難
2. **效能**: 對於高並發可能不如純程式碼
3. **客製化**: 受限於 n8n 提供的功能
4. **除錯**: 相對於程式碼，除錯可能較複雜

## 🎯 建議

對於 LINE 記帳機器人，建議：

- **初學者**: 使用 n8n，快速上手
- **進階需求**: 使用 Python，更大彈性
- **混合方式**: 用 n8n 處理主流程，Python 處理複雜邏輯

n8n 非常適合快速建立 MVP（最小可行產品）和原型測試！ 