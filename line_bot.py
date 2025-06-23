from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction
)
from datetime import datetime
import logging

from config import LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, PORT
from database import ExpenseDatabase
from message_parser import MessageParser

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化 Flask 應用程式
app = Flask(__name__)

# 初始化 LINE Bot API
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 初始化資料庫和訊息解析器
db = ExpenseDatabase()
parser = MessageParser()

class ExpenseBot:
    def __init__(self):
        self.commands = {
            '記帳': self.show_expense_help,
            '查詢': self.show_recent_expenses,
            '本月': self.show_monthly_summary,
            '幫助': self.show_help,
            '說明': self.show_help
        }
    
    def handle_message(self, user_id, message_text):
        """處理用戶訊息"""
        # 檢查是否為指令
        if message_text.strip() in self.commands:
            return self.commands[message_text.strip()](user_id)
        
        # 嘗試解析為支出記錄
        parsed_data = parser.parse_message(message_text)
        
        if parser.is_valid_expense(parsed_data):
            return self.add_expense(user_id, parsed_data)
        else:
            return self.suggest_format(message_text)
    
    def add_expense(self, user_id, parsed_data):
        """新增支出記錄"""
        try:
            expense_id = db.add_expense(
                user_id=user_id,
                amount=parsed_data['amount'],
                location=parsed_data['location'],
                description=parsed_data['description'],
                category=parsed_data['category']
            )
            
            summary = parser.format_expense_summary(parsed_data)
            
            response = f"✅ 記帳成功！\n\n{summary}\n\n記錄編號: #{expense_id}"
            
            # 添加快速回覆選項
            quick_reply = QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="查詢記錄", text="查詢")),
                QuickReplyButton(action=MessageAction(label="本月摘要", text="本月")),
                QuickReplyButton(action=MessageAction(label="繼續記帳", text="記帳"))
            ])
            
            return TextSendMessage(text=response, quick_reply=quick_reply)
            
        except Exception as e:
            logger.error(f"新增支出記錄時發生錯誤: {e}")
            return TextSendMessage(text="❌ 記帳失敗，請稍後再試。")
    
    def show_recent_expenses(self, user_id):
        """顯示最近的支出記錄"""
        try:
            expenses = db.get_user_expenses(user_id, limit=5)
            
            if not expenses:
                return TextSendMessage(text="📋 目前沒有支出記錄。")
            
            response = "📋 最近 5 筆支出記錄:\n\n"
            total = 0
            
            for expense in expenses:
                expense_id, amount, location, description, category, timestamp = expense
                total += amount
                
                # 格式化時間
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%m/%d %H:%M')
                
                response += f"#{expense_id} - {time_str}\n"
                response += f"💰 {amount} 元"
                
                if location:
                    response += f" | 📍 {location}"
                if category:
                    response += f" | 🏷️ {category}"
                
                response += "\n\n"
            
            response += f"總計: {total} 元"
            
            return TextSendMessage(text=response)
            
        except Exception as e:
            logger.error(f"查詢支出記錄時發生錯誤: {e}")
            return TextSendMessage(text="❌ 查詢失敗，請稍後再試。")
    
    def show_monthly_summary(self, user_id):
        """顯示本月支出摘要"""
        try:
            now = datetime.now()
            summary = db.get_monthly_summary(user_id, now.year, now.month)
            
            if not summary:
                return TextSendMessage(text=f"📊 {now.year}年{now.month}月目前沒有支出記錄。")
            
            response = f"📊 {now.year}年{now.month}月支出摘要:\n\n"
            total_amount = 0
            total_count = 0
            
            for amount, count, category in summary:
                if amount and count:
                    total_amount += amount
                    total_count += count
                    response += f"🏷️ {category or '其他'}: {amount} 元 ({count} 筆)\n"
            
            response += f"\n💳 總支出: {total_amount} 元"
            response += f"\n📝 總筆數: {total_count} 筆"
            
            if total_count > 0:
                avg = total_amount / total_count
                response += f"\n📈 平均: {avg:.1f} 元/筆"
            
            return TextSendMessage(text=response)
            
        except Exception as e:
            logger.error(f"查詢月度摘要時發生錯誤: {e}")
            return TextSendMessage(text="❌ 查詢失敗，請稍後再試。")
    
    def show_expense_help(self, user_id):
        """顯示記帳格式說明"""
        help_text = """💡 記帳格式說明:

你可以用自然語言記帳，我會自動識別金額和地點！

📝 範例:
• "在7-11買飲料50元"
• "午餐花了120塊"
• "停車費30元"
• "星巴克咖啡150"
• "捷運車費26元"

🏷️ 我會自動分類:
• 餐飲: 餐廳、咖啡、飲料等
• 購物: 超市、商店、衣服等  
• 交通: 車費、油錢、停車等
• 娛樂: 電影、遊戲、KTV等
• 醫療: 看病、藥品等

💡 指令:
• "查詢" - 查看最近記錄
• "本月" - 本月支出摘要
• "幫助" - 顯示說明"""

        return TextSendMessage(text=help_text)
    
    def show_help(self, user_id):
        """顯示主要幫助訊息"""
        help_text = """🤖 LINE 記帳機器人

我可以幫你輕鬆記帳！

🚀 開始使用:
直接傳送包含金額和地點的訊息，例如:
"在麥當勞吃午餐89元"

📋 功能指令:
• "記帳" - 記帳格式說明
• "查詢" - 查看最近記錄  
• "本月" - 本月支出摘要
• "幫助" - 顯示此說明

💡 小提示:
支援多種金額格式 (元、塊、$、NT$)
自動識別地點和消費類別"""

        quick_reply = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="記帳說明", text="記帳")),
            QuickReplyButton(action=MessageAction(label="查詢記錄", text="查詢")),
            QuickReplyButton(action=MessageAction(label="本月摘要", text="本月"))
        ])

        return TextSendMessage(text=help_text, quick_reply=quick_reply)
    
    def suggest_format(self, message_text):
        """建議正確的記帳格式"""
        suggestion = f"""🤔 我無法從這個訊息中識別出金額:
"{message_text}"

💡 請試試這些格式:
• "在[地點][消費內容][金額]元"
• "花了[金額]元買[物品]"
• "[地點][金額]塊"

📝 範例:
• "在7-11買飲料50元"
• "午餐花了120元"
• "停車費30塊"

或輸入 "記帳" 查看詳細說明。"""

        return TextSendMessage(text=suggestion)

# 初始化機器人
bot = ExpenseBot()

@app.route("/callback", methods=['POST'])
def callback():
    """LINE Webhook 回調函數"""
    # 取得 X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # 取得 request body
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 處理 webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """處理文字訊息"""
    user_id = event.source.user_id
    message_text = event.message.text
    
    logger.info(f"收到用戶 {user_id} 的訊息: {message_text}")
    
    try:
        # 使用機器人處理訊息
        reply_message = bot.handle_message(user_id, message_text)
        
        # 回覆訊息
        line_bot_api.reply_message(event.reply_token, reply_message)
        
    except Exception as e:
        logger.error(f"處理訊息時發生錯誤: {e}")
        error_message = TextSendMessage(text="❌ 系統發生錯誤，請稍後再試。")
        line_bot_api.reply_message(event.reply_token, error_message)

@app.route("/")
def index():
    """首頁"""
    return "LINE 記帳機器人運行中！"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=PORT, debug=True) 