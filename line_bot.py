import sys
sys.stdout.write(f"🔍 FORCED DEBUG: Starting app\n")
sys.stdout.flush()

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction
)
from datetime import datetime
import logging

from config import LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, PORT, DATABASE_URL
from database import ExpenseDatabase
from message_parser import MessageParser

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🔍 除錯訊息 - 檢查設定
print(f"🔍 DEBUG: TOKEN 長度: {len(LINE_CHANNEL_ACCESS_TOKEN)}")
print(f"🔍 DEBUG: TOKEN 開頭: {LINE_CHANNEL_ACCESS_TOKEN[:30]}...")
print(f"🔍 DEBUG: TOKEN 結尾: ...{LINE_CHANNEL_ACCESS_TOKEN[-10:]}")
print(f"🔍 DEBUG: SECRET 長度: {len(LINE_CHANNEL_SECRET)}")
print(f"🔍 DEBUG: SECRET: {LINE_CHANNEL_SECRET}")
print(f"🔍 DEBUG: DATABASE_URL: {'✅ 已設定 PostgreSQL' if DATABASE_URL else '⚠️ 使用 SQLite'}")

# 詳細的資料庫設定檢查
if DATABASE_URL:
    print(f"🔍 DEBUG: DATABASE_URL 內容: {DATABASE_URL[:50]}...")
    print(f"🔍 DEBUG: DATABASE_URL 長度: {len(DATABASE_URL)}")
else:
    print(f"🔍 DEBUG: DATABASE_URL 為空")

# 檢查 PostgreSQL 支援
try:
    import psycopg2
    print(f"🔍 DEBUG: psycopg2 可用: ✅")
except ImportError:
    print(f"🔍 DEBUG: psycopg2 不可用: ❌")

print(f"🔍 DEBUG: PORT: {PORT}")

# 初始化 Flask 應用程式
app = Flask(__name__)

# 初始化 LINE Bot API
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 初始化資料庫和訊息解析器
db = ExpenseDatabase()
parser = MessageParser()

print(f"🔍 DEBUG: 資料庫類型: {'PostgreSQL' if db.use_postgresql else 'SQLite'}")

class ExpenseBot:
    def __init__(self):
        self.commands = {
            '記帳': self.show_expense_help,
            '查詢': self.show_recent_expenses,
            '本月': self.show_monthly_summary,
            '總金額': self.show_monthly_total,
            '統計': self.show_all_time_stats,
            '當前統計': self.show_current_stats,
            '重新統計': self.confirm_reset_current_stats,
            '確認重新統計': self.reset_current_stats,
            '取消重新統計': self.cancel_reset_stats,
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
                description=parsed_data['reason'] or parsed_data['description'],
                location=None,  # 不再使用地點
                category=None   # 不再使用分類
            )
            
            summary = parser.format_expense_summary(parsed_data)
            
            response = f"✅ 記帳成功！\n\n{summary}\n\n記錄編號: #{expense_id}"
            
            # 添加快速回覆選項
            quick_reply = QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="當前統計", text="當前統計")),
                QuickReplyButton(action=MessageAction(label="查詢記錄", text="查詢")),
                QuickReplyButton(action=MessageAction(label="本月", text="本月"))
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
                response += f"📝 {description} - 💰 {amount:.0f} 元\n\n"
            
            response += f"總計: {total:.0f} 元"
            
            return TextSendMessage(text=response)
            
        except Exception as e:
            logger.error(f"查詢支出記錄時發生錯誤: {e}")
            return TextSendMessage(text="❌ 查詢失敗，請稍後再試。")
    
    def show_monthly_summary(self, user_id):
        """顯示本月支出摘要（簡化版）"""
        try:
            now = datetime.now()
            total_amount, total_count = db.get_monthly_total(user_id, now.year, now.month)
            
            if total_count == 0:
                return TextSendMessage(text=f"📊 {now.year}年{now.month}月目前沒有支出記錄。")
            
            response = f"📊 {now.year}年{now.month}月支出摘要:\n\n"
            response += f"💳 總支出: {total_amount:.0f} 元\n"
            response += f"📝 總筆數: {total_count} 筆\n"
            
            if total_count > 0:
                avg = total_amount / total_count
                response += f"📈 平均: {avg:.1f} 元/筆"
            
            return TextSendMessage(text=response)
            
        except Exception as e:
            logger.error(f"查詢月度摘要時發生錯誤: {e}")
            return TextSendMessage(text="❌ 查詢失敗，請稍後再試。")
    
    def show_monthly_total(self, user_id):
        """顯示每月總金額"""
        try:
            now = datetime.now()
            
            # 獲取最近12個月的資料
            monthly_data = []
            for i in range(12):
                # 計算月份
                month = now.month - i
                year = now.year
                if month <= 0:
                    month += 12
                    year -= 1
                
                total_amount, total_count = db.get_monthly_total(user_id, year, month)
                if total_count > 0:
                    monthly_data.append((year, month, total_amount, total_count))
            
            if not monthly_data:
                return TextSendMessage(text="📊 目前沒有任何支出記錄。")
            
            response = "📊 每月總金額統計:\n\n"
            
            for year, month, amount, count in monthly_data[:6]:  # 顯示最近6個月
                response += f"📅 {year}年{month}月: {amount:.0f} 元 ({count} 筆)\n"
            
            # 計算總計
            total_all = sum(amount for _, _, amount, _ in monthly_data)
            count_all = sum(count for _, _, _, count in monthly_data)
            
            response += f"\n💰 總計: {total_all:.0f} 元"
            response += f"\n📊 總筆數: {count_all} 筆"
            
            return TextSendMessage(text=response)
            
        except Exception as e:
            logger.error(f"查詢每月總金額時發生錯誤: {e}")
            return TextSendMessage(text="❌ 查詢失敗，請稍後再試。")
    
    def show_current_stats(self, user_id):
        """顯示當前統計金額（從重置日期開始計算）"""
        try:
            current_stats = db.get_current_stats(user_id)
            
            if current_stats['total_count'] == 0:
                return TextSendMessage(text="📊 當前統計期間內沒有任何記錄。")
            
            response = "📊 當前統計金額:\n\n"
            response += f"💰 當前總支出: {current_stats['total_amount']:.0f} 元\n"
            response += f"📝 當前筆數: {current_stats['total_count']} 筆\n"
            
            if current_stats['total_count'] > 0:
                avg = current_stats['total_amount'] / current_stats['total_count']
                response += f"📈 平均: {avg:.1f} 元/筆\n"
            
            # 顯示統計期間
            if current_stats['reset_date']:
                reset_dt = datetime.fromisoformat(current_stats['reset_date'].replace('Z', '+00:00'))
                response += f"\n📅 統計開始: {reset_dt.strftime('%Y/%m/%d %H:%M')}\n"
            
            if current_stats['last_record']:
                last_dt = datetime.fromisoformat(current_stats['last_record'].replace('Z', '+00:00'))
                response += f"📅 最近記錄: {last_dt.strftime('%Y/%m/%d %H:%M')}\n"
            
            response += f"\n💡 提示: 使用「重新統計」可重置當前統計金額"
            
            return TextSendMessage(text=response)
            
        except Exception as e:
            logger.error(f"查詢當前統計時發生錯誤: {e}")
            return TextSendMessage(text="❌ 查詢失敗，請稍後再試。")

    def show_all_time_stats(self, user_id):
        """顯示總統計資料（所有時間的記錄）"""
        try:
            stats = db.get_all_time_stats(user_id)
            
            if stats['total_count'] == 0:
                return TextSendMessage(text="📊 目前沒有任何支出記錄。")
            
            response = "📊 歷史總統計報告:\n\n"
            response += f"💰 歷史總支出: {stats['total_amount']:.0f} 元\n"
            response += f"📝 歷史總筆數: {stats['total_count']} 筆\n"
            
            if stats['total_count'] > 0:
                avg = stats['total_amount'] / stats['total_count']
                response += f"📈 歷史平均: {avg:.1f} 元/筆\n"
            
            # 顯示記錄期間
            if stats['first_record'] and stats['last_record']:
                first_dt = datetime.fromisoformat(stats['first_record'].replace('Z', '+00:00'))
                last_dt = datetime.fromisoformat(stats['last_record'].replace('Z', '+00:00'))
                response += f"\n📅 記錄期間:\n"
                response += f"   開始: {first_dt.strftime('%Y/%m/%d')}\n"
                response += f"   最近: {last_dt.strftime('%Y/%m/%d')}\n"
            
            # 顯示最近幾個月的統計
            if stats['monthly_stats']:
                response += f"\n📊 最近月份統計:\n"
                for month_str, amount, count in stats['monthly_stats'][:5]:
                    year, month = month_str.split('-')
                    response += f"   {year}年{int(month)}月: {amount:.0f} 元 ({count} 筆)\n"
            
            response += f"\n💡 「當前統計」顯示重置後的累積金額"
            
            return TextSendMessage(text=response)
            
        except Exception as e:
            logger.error(f"查詢總統計時發生錯誤: {e}")
            return TextSendMessage(text="❌ 查詢失敗，請稍後再試。")

    def show_expense_help(self, user_id):
        """顯示記帳格式說明"""
        help_text = """💡 記帳格式說明:

簡單的格式：原因 + 價錢

📝 範例:
• "午餐 120"
• "咖啡 50元"
• "停車費 30塊"
• "買飲料 45"
• "電影票 280元"

💡 支援的金額格式:
• 120元、50塊、30錢
• NT$100、$80
• 花了60、60 (純數字)

🕐 系統會自動記錄時間
📋 查詢時顯示：原因 + 價錢 + 日期時間

📊 統計功能:
• "本月" - 本月支出摘要
• "總金額" - 每月總金額統計
• "統計" - 完整統計報告"""

        return TextSendMessage(text=help_text)
    
    def show_help(self, user_id):
        """顯示主要幫助訊息"""
        help_text = """🤖 LINE 記帳機器人

簡單記帳，輕鬆管理！

🚀 開始使用:
直接輸入「原因 + 價錢」，例如:
"午餐 120元"

📋 功能指令:
• "記帳" - 記帳格式說明
• "查詢" - 查看最近記錄  
• "本月" - 本月支出摘要
• "總金額" - 每月總金額統計
• "當前統計" - 當前累積統計金額 ⭐
• "統計" - 歷史總統計報告
• "重新統計" - 🔄 重置當前統計金額
• "幫助" - 顯示此說明

💡 統計說明:
• 當前統計：從重置日期開始累積
• 歷史統計：包含所有時間記錄
• 重新統計：只重置當前金額，保留歷史"""

        quick_reply = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="當前統計", text="當前統計")),
            QuickReplyButton(action=MessageAction(label="查詢記錄", text="查詢")),
            QuickReplyButton(action=MessageAction(label="總金額", text="總金額"))
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

    def confirm_reset_current_stats(self, user_id):
        """確認是否要重新統計當前金額"""
        try:
            # 取得當前統計資料
            current_stats = db.get_current_stats(user_id)
            
            if current_stats['total_count'] == 0:
                return TextSendMessage(text="📊 當前統計金額為 0，無需重新統計。")
            
            warning_text = f"""⚠️ 重新統計確認

您即將重置「當前統計金額」！

📊 當前統計:
💰 當前總支出: {current_stats['total_amount']:.0f} 元
📝 當前筆數: {current_stats['total_count']} 筆

✅ 保留內容:
• 所有記帳記錄不會被刪除
• 每月總金額統計不受影響
• 歷史資料完整保留

🔄 重置內容:
• 當前統計金額歸零
• 重新開始累積計算

確定要執行嗎？"""

            quick_reply = QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="✅ 確認重新統計", text="確認重新統計")),
                QuickReplyButton(action=MessageAction(label="❌ 取消", text="取消重新統計"))
            ])

            return TextSendMessage(text=warning_text, quick_reply=quick_reply)
            
        except Exception as e:
            logger.error(f"確認重新統計時發生錯誤: {e}")
            return TextSendMessage(text="❌ 操作失敗，請稍後再試。")
    
    def reset_current_stats(self, user_id):
        """執行重新統計（重置當前統計金額）"""
        try:
            old_stats = db.reset_current_stats(user_id)
            
            success_text = f"""✅ 重新統計完成！

📊 重置結果:
🔄 重置前金額: {old_stats['total_amount']:.0f} 元
🔄 重置前筆數: {old_stats['total_count']} 筆
💰 當前統計金額: 0 元

✅ 保留內容:
• 所有記帳記錄完整保留
• 每月總金額統計正常運作
• 可隨時查看歷史統計

🎉 現在開始重新累積當前統計金額！"""
            
            quick_reply = QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="查看當前統計", text="當前統計")),
                QuickReplyButton(action=MessageAction(label="開始記帳", text="記帳"))
            ])
            
            return TextSendMessage(text=success_text, quick_reply=quick_reply)
                
        except Exception as e:
            logger.error(f"執行重新統計時發生錯誤: {e}")
            return TextSendMessage(text="❌ 重新統計失敗，請稍後再試。")
    
    def cancel_reset_stats(self, user_id):
        """取消重新統計"""
        return TextSendMessage(text="✅ 已取消重新統計，您的記錄保持不變。")

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