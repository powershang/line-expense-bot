import sys
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
        # 檢查是否為 @ai 記帳指令
        if message_text.strip().lower().startswith('@ai'):
            # 嘗試解析為支出記錄
            parsed_data = parser.parse_message(message_text)
            
            if parser.is_valid_expense(parsed_data):
                return self.add_expense(user_id, parsed_data)
            else:
                return self.suggest_ai_format(message_text)
        
        # 檢查是否為其他指令
        elif message_text.strip() in self.commands:
            return self.commands[message_text.strip()](user_id)
        
        # 如果不是 @ai 開頭也不是指令，提示使用 @ai 格式
        else:
            return self.suggest_ai_usage()
    
    def add_expense(self, user_id, parsed_data):
        """新增支出記錄"""
        try:
            # 檢查解析資料是否有效
            if not parsed_data.get('amount'):
                return TextSendMessage(text="❌ 無法識別金額，請重新輸入。")
            
            expense_id = db.add_expense(
                user_id=user_id,
                amount=parsed_data['amount'],
                description=parsed_data['reason'] or parsed_data['description'],
                location=None,  # 不再使用地點
                category=None   # 不再使用分類
            )
            
            if expense_id is None or expense_id == 0:
                return TextSendMessage(text="❌ 記帳失敗：無法取得記錄ID。")
            
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
                
                # 格式化時間 - 添加錯誤處理
                try:
                    if timestamp:
                        # 處理不同的時間格式
                        if isinstance(timestamp, str):
                            # 移除 Z 並替換為 +00:00，或直接使用原格式
                            if 'Z' in timestamp:
                                timestamp_clean = timestamp.replace('Z', '+00:00')
                            elif '+' in timestamp or 'T' in timestamp:
                                timestamp_clean = timestamp
                            else:
                                # 如果是 YYYY-MM-DD HH:MM:SS 格式，直接解析
                                timestamp_clean = timestamp
                            
                            dt = datetime.fromisoformat(timestamp_clean)
                        else:
                            # 如果是 datetime 對象
                            dt = timestamp
                        
                        time_str = dt.strftime('%m/%d %H:%M')
                    else:
                        time_str = '時間未知'
                except Exception as time_error:
                    print(f"❌ 時間格式化錯誤: {time_error}, timestamp: {timestamp}, type: {type(timestamp)}")
                    time_str = '時間格式錯誤'
                
                response += f"#{expense_id} - {time_str}\n"
                response += f"📝 {description} - 💰 {amount:.0f} 元\n\n"
            
            response += f"總計: {total:.0f} 元"
            
            return TextSendMessage(text=response)
            
        except Exception as e:
            print(f"❌ 查詢支出記錄詳細錯誤: {type(e).__name__}: {str(e)}")
            print(f"❌ 錯誤完整信息: {repr(e)}")
            import traceback
            traceback.print_exc()
            logger.error(f"查詢支出記錄時發生錯誤: {e}")
            return TextSendMessage(text="❌ 查詢失敗，請稍後再試。")
    
    def show_monthly_summary(self, user_id):
        """顯示本月支出摘要（簡化版）"""
        try:
            now = datetime.now()
            print(f"🔍 DEBUG: 正在查詢用戶 {user_id} 的 {now.year}年{now.month}月 資料")
            total_amount, total_count = db.get_monthly_total(user_id, now.year, now.month)
            print(f"🔍 DEBUG: 查詢結果 - 金額:{total_amount}, 筆數:{total_count}")
            
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
            print(f"🔍 DEBUG: 例外詳細資訊 - 類型:{type(e)}, 值:{e}, 字串:{str(e)}")
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
            
            # 顯示統計期間 - 添加錯誤處理
            if current_stats['reset_date']:
                try:
                    reset_date_str = current_stats['reset_date']
                    if isinstance(reset_date_str, str):
                        if 'Z' in reset_date_str:
                            reset_date_str = reset_date_str.replace('Z', '+00:00')
                        reset_dt = datetime.fromisoformat(reset_date_str)
                    else:
                        reset_dt = reset_date_str
                    response += f"\n📅 統計開始: {reset_dt.strftime('%Y/%m/%d %H:%M')}\n"
                except Exception as e:
                    print(f"❌ 重置日期格式化錯誤: {e}, reset_date: {current_stats['reset_date']}")
                    response += f"\n📅 統計開始: 日期格式錯誤\n"
            
            if current_stats['last_record']:
                try:
                    last_record_str = current_stats['last_record']
                    if isinstance(last_record_str, str):
                        if 'Z' in last_record_str:
                            last_record_str = last_record_str.replace('Z', '+00:00')
                        last_dt = datetime.fromisoformat(last_record_str)
                    else:
                        last_dt = last_record_str
                    response += f"📅 最近記錄: {last_dt.strftime('%Y/%m/%d %H:%M')}\n"
                except Exception as e:
                    print(f"❌ 最近記錄日期格式化錯誤: {e}, last_record: {current_stats['last_record']}")
                    response += f"📅 最近記錄: 日期格式錯誤\n"
            
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
            
            # 顯示記錄期間 - 添加錯誤處理
            if stats['first_record'] and stats['last_record']:
                try:
                    first_record_str = stats['first_record']
                    last_record_str = stats['last_record']
                    
                    if isinstance(first_record_str, str):
                        if 'Z' in first_record_str:
                            first_record_str = first_record_str.replace('Z', '+00:00')
                        first_dt = datetime.fromisoformat(first_record_str)
                    else:
                        first_dt = first_record_str
                    
                    if isinstance(last_record_str, str):
                        if 'Z' in last_record_str:
                            last_record_str = last_record_str.replace('Z', '+00:00')
                        last_dt = datetime.fromisoformat(last_record_str)
                    else:
                        last_dt = last_record_str
                    
                    response += f"\n📅 記錄期間:\n"
                    response += f"   開始: {first_dt.strftime('%Y/%m/%d')}\n"
                    response += f"   最近: {last_dt.strftime('%Y/%m/%d')}\n"
                except Exception as e:
                    print(f"❌ 記錄期間日期格式化錯誤: {e}")
                    response += f"\n📅 記錄期間: 日期格式錯誤\n"
            
            # 顯示最近幾個月的統計
            if stats['monthly_stats']:
                response += f"\n📊 最近月份統計:\n"
                for month_str, amount, count in stats['monthly_stats'][:5]:
                    try:
                        year, month = month_str.split('-')
                        response += f"   {year}年{int(month)}月: {amount:.0f} 元 ({count} 筆)\n"
                    except Exception as e:
                        print(f"❌ 月份統計格式化錯誤: {e}, month_str: {month_str}")
                        response += f"   日期格式錯誤: {amount:.0f} 元 ({count} 筆)\n"
            
            response += f"\n💡 「當前統計」顯示重置後的累積金額"
            
            return TextSendMessage(text=response)
            
        except Exception as e:
            logger.error(f"查詢總統計時發生錯誤: {e}")
            return TextSendMessage(text="❌ 查詢失敗，請稍後再試。")

    def show_expense_help(self, user_id):
        """顯示記帳格式說明"""
        help_text = parser.get_help_message()
        return TextSendMessage(text=help_text)
    
    def show_help(self, user_id):
        """顯示主要幫助訊息"""
        help_text = """🤖 LINE 記帳機器人

💡 **新版本 - 簡化記帳**

🚀 記帳方式:
必須以 @ai 開頭，格式：@ai 原因 金額

📝 範例:
• @ai 午餐 120
• @ai 咖啡 50元
• @ai 停車費 30

📋 查詢指令:
• "查詢" - 查看最近記錄  
• "本月" - 本月支出摘要
• "總金額" - 每月總金額統計
• "當前統計" - 當前累積統計金額 ⭐
• "統計" - 歷史總統計報告
• "重新統計" - 🔄 重置當前統計金額
• "記帳" - 查看記帳格式說明
• "幫助" - 顯示此說明

⚠️ **重要提醒**：
只有以 @ai 開頭的訊息才會被識別為記帳指令！

✨ **新特色**：
• 簡化格式，只記錄原因和金額
• 避免誤判，明確區分記帳和聊天
• 更快速的記帳體驗"""

        quick_reply = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="當前統計", text="當前統計")),
            QuickReplyButton(action=MessageAction(label="查詢記錄", text="查詢")),
            QuickReplyButton(action=MessageAction(label="記帳說明", text="記帳"))
        ])

        return TextSendMessage(text=help_text, quick_reply=quick_reply)
    
    def suggest_ai_format(self, message_text):
        """建議正確的 @ai 格式"""
        suggestion = f"""🤔 我發現您使用了 @ai 但格式不正確：
"{message_text}"

💡 正確格式：@ai 原因 金額

📝 範例：
• @ai 午餐 120
• @ai 咖啡 50元
• @ai 停車費 30
• @ai 買飲料 45元

請再試一次！"""

        return TextSendMessage(text=suggestion)
    
    def suggest_ai_usage(self):
        """建議使用 @ai 格式記帳"""
        suggestion = """🤖 記帳機器人提醒：

💡 要記帳請使用 @ai 開頭：
格式：@ai 原因 金額

📝 範例：
• @ai 午餐 120
• @ai 咖啡 50元
• @ai 停車費 30

📋 其他功能：
• "查詢" - 查看最近記錄
• "當前統計" - 查看統計金額
• "幫助" - 查看說明"""

        quick_reply = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="查詢記錄", text="查詢")),
            QuickReplyButton(action=MessageAction(label="當前統計", text="當前統計")),
            QuickReplyButton(action=MessageAction(label="幫助", text="幫助"))
        ])

        return TextSendMessage(text=suggestion, quick_reply=quick_reply)

    def suggest_format(self, message_text):
        """建議正確的記帳格式（舊方法，重導向到新格式）"""
        return self.suggest_ai_usage()

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
        
        # 回覆訊息 - 加入更好的錯誤處理
        try:
            line_bot_api.reply_message(event.reply_token, reply_message)
        except Exception as reply_error:
            # 如果是 reply token 問題，不要拋出錯誤（避免 500 錯誤）
            if "Invalid reply token" in str(reply_error):
                logger.info("Reply token 已過期或重複使用，這是正常的重送請求")
            else:
                raise reply_error
        
    except Exception as e:
        logger.error(f"處理訊息時發生錯誤: {e}")
        
        # 只有在 reply token 有效時才嘗試回覆錯誤訊息
        try:
            error_message = TextSendMessage(text="❌ 系統發生錯誤，請稍後再試。")
            line_bot_api.reply_message(event.reply_token, error_message)
        except:
            logger.info("無法發送錯誤訊息，可能是 reply token 問題")

@app.route("/")
def index():
    """首頁"""
    return "LINE 記帳機器人運行中！"

@app.route("/version")
def version_info():
    """顯示當前版本信息"""
    import subprocess
    import os
    from datetime import datetime
    
    try:
        # 嘗試獲取 Git commit 信息
        try:
            commit_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('utf-8').strip()
            commit_message = subprocess.check_output(['git', 'log', '-1', '--pretty=%B']).decode('utf-8').strip()
            commit_date = subprocess.check_output(['git', 'log', '-1', '--pretty=%ci']).decode('utf-8').strip()
        except:
            commit_hash = "無法取得"
            commit_message = "Git 信息不可用"
            commit_date = "未知"
        
        # 獲取環境信息
        database_type = "PostgreSQL" if DATABASE_URL else "SQLite"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>版本信息 - LINE 記帳機器人</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 8px; margin-bottom: 20px; }}
                .info-item {{ margin: 15px 0; padding: 10px; background-color: #f9f9f9; border-left: 4px solid #4CAF50; }}
                .commit-hash {{ font-family: monospace; background: #e8e8e8; padding: 2px 6px; border-radius: 3px; }}
                .timestamp {{ color: #666; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 版本信息</h1>
                    <p>LINE 記帳機器人部署狀態</p>
                </div>
                
                <div class="info-item">
                    <strong>📋 當前 Commit:</strong><br>
                    <span class="commit-hash">{commit_hash}</span>
                </div>
                
                <div class="info-item">
                    <strong>💬 Commit 訊息:</strong><br>
                    {commit_message}
                </div>
                
                <div class="info-item">
                    <strong>📅 Commit 時間:</strong><br>
                    <span class="timestamp">{commit_date}</span>
                </div>
                
                <div class="info-item">
                    <strong>🗄️ 資料庫類型:</strong><br>
                    {database_type}
                </div>
                
                <div class="info-item">
                    <strong>⏰ 檢查時間:</strong><br>
                    <span class="timestamp">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (伺服器時間)</span>
                </div>
                
                <div class="info-item">
                    <strong>🌐 環境:</strong><br>
                    {'Render (線上環境)' if DATABASE_URL else '本地開發環境'}
                </div>
                
                <div style="text-align: center; margin-top: 20px;">
                    <a href="/admin" style="color: #4CAF50; text-decoration: none;">📊 管理界面</a> |
                    <a href="/" style="color: #4CAF50; text-decoration: none;">🏠 首頁</a>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        return f"版本檢查錯誤: {str(e)}"

def get_user_profile(user_id):
    """獲取 LINE 用戶資料，優先從資料庫查詢"""
    try:
        # 先從資料庫查詢
        profile_data = db.get_user_profile(user_id)
        
        if profile_data:
            # 如果資料庫有資料，直接使用
            return profile_data
        else:
            # 如果資料庫沒有，從 LINE API 查詢
            try:
                profile = line_bot_api.get_profile(user_id)
                profile_data = {
                    'display_name': profile.display_name,
                    'picture_url': profile.picture_url,
                    'status_message': profile.status_message
                }
                
                # 儲存到資料庫供下次使用
                db.save_user_profile(
                    user_id, 
                    profile.display_name, 
                    profile.picture_url, 
                    profile.status_message
                )
                
                return profile_data
                
            except Exception as api_error:
                logger.error(f"LINE API 查詢失敗: {api_error}")
                return {
                    'display_name': f'用戶 {user_id[:8]}...',
                    'picture_url': None,
                    'status_message': None
                }
                
    except Exception as e:
        logger.error(f"獲取用戶資料失敗: {e}")
        return {
            'display_name': f'用戶 {user_id[:8]}...',
            'picture_url': None,
            'status_message': None
        }

@app.route("/admin")
def admin_dashboard():
    """管理員儀表板"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # 取得所有用戶的記錄統計
        if db.use_postgresql:
            cursor.execute('''
                SELECT user_id, COUNT(*) as count, SUM(amount) as total, MAX(timestamp) as last_record
                FROM expenses
                GROUP BY user_id
                ORDER BY last_record DESC
            ''')
        else:
            cursor.execute('''
                SELECT user_id, COUNT(*) as count, SUM(amount) as total, MAX(timestamp) as last_record
                FROM expenses
                GROUP BY user_id
                ORDER BY last_record DESC
            ''')
        
        users = cursor.fetchall()
        conn.close()
        
        # 轉換 PostgreSQL 結果
        if db.use_postgresql:
            users = [tuple(user.values()) for user in users]
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>LINE 記帳機器人 - 資料庫管理</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .stats {{ background-color: #f9f9f9; padding: 15px; margin: 20px 0; }}
                .user-info {{ display: flex; align-items: center; }}
                .user-avatar {{ width: 30px; height: 30px; border-radius: 50%; margin-right: 10px; }}
                .user-name {{ font-weight: bold; }}
                .user-id {{ font-size: 0.8em; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 LINE 記帳機器人 - 資料庫管理</h1>
                <p>資料庫類型: {'PostgreSQL' if db.use_postgresql else 'SQLite'}</p>
            </div>
            
            <div class="stats">
                <h2>👥 用戶統計總覽</h2>
                <p>總用戶數: {len(users)}</p>
            </div>
            
            <h2>📋 用戶記錄概覽</h2>
            <table>
                <tr>
                    <th>用戶資料</th>
                    <th>記錄筆數</th>
                    <th>總金額</th>
                    <th>最後記錄時間</th>
                    <th>操作</th>
                </tr>
        """
        
        for user_id, count, total, last_record in users:
            # 獲取用戶資料
            user_profile = get_user_profile(user_id)
            display_name = user_profile['display_name']
            picture_url = user_profile['picture_url']
            
            # 建立用戶顯示信息
            avatar_img = f'<img src="{picture_url}" class="user-avatar" alt="頭像">' if picture_url else '👤'
            
            html += f"""
                <tr>
                    <td>
                        <div class="user-info">
                            {avatar_img}
                            <div>
                                <div class="user-name">{display_name}</div>
                                <div class="user-id">{user_id[:20]}...</div>
                            </div>
                        </div>
                    </td>
                    <td>{count}</td>
                    <td>${total:.0f}</td>
                    <td>{last_record}</td>
                    <td><a href="/admin/user/{user_id}">查看詳細</a></td>
                </tr>
            """
        
        html += """
            </table>
            
            <div style="margin-top: 30px;">
                <h3>🔧 管理工具</h3>
                <p><a href="/admin/expenses">📋 查看所有記錄</a></p>
                <p><a href="/admin/stats">📊 詳細統計</a></p>
            </div>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        return f"錯誤: {str(e)}"

@app.route("/admin/user/<user_id>")
def admin_user_detail(user_id):
    """查看特定用戶的詳細記錄"""
    try:
        # 獲取用戶資料
        user_profile = get_user_profile(user_id)
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        if db.use_postgresql:
            cursor.execute('''
                SELECT id, amount, location, description, category, timestamp
                FROM expenses
                WHERE user_id = %s
                ORDER BY timestamp DESC
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT id, amount, location, description, category, timestamp
                FROM expenses
                WHERE user_id = ?
                ORDER BY timestamp DESC
            ''', (user_id,))
        
        expenses = cursor.fetchall()
        conn.close()
        
        # 轉換 PostgreSQL 結果
        if db.use_postgresql:
            expenses = [tuple(expense.values()) for expense in expenses]
        
        # 計算統計
        total = sum(expense[1] for expense in expenses)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>用戶詳情 - LINE 記帳機器人</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .header {{ background-color: #FF9800; color: white; padding: 20px; text-align: center; }}
                .user-info {{ background-color: #e3f2fd; padding: 20px; margin: 20px 0; border-radius: 5px; }}
                .user-avatar {{ width: 60px; height: 60px; border-radius: 50%; margin-right: 15px; vertical-align: middle; }}
                .back {{ margin: 20px 0; }}
                .stats {{ background-color: #f9f9f9; padding: 15px; margin: 20px 0; }}
                .delete-btn {{ background-color: #f44336; color: white; padding: 4px 8px; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; }}
                .delete-btn:hover {{ background-color: #da190b; }}
                .batch-actions {{ margin: 20px 0; padding: 15px; background-color: #fff3e0; border-radius: 5px; border-left: 4px solid #FF9800; }}
                .select-all {{ margin-right: 10px; }}
                .batch-delete-btn {{ background-color: #f44336; color: white; padding: 8px 16px; border: none; border-radius: 5px; cursor: pointer; }}
                .batch-delete-btn:hover {{ background-color: #da190b; }}
                .clear-all-btn {{ background-color: #ff5722; color: white; padding: 8px 16px; border: none; border-radius: 5px; cursor: pointer; margin-left: 10px; }}
                .clear-all-btn:hover {{ background-color: #d84315; }}
            </style>
            <script>
                function deleteRecord(id, description) {{
                    if (confirm('確定要刪除記錄 #' + id + ' "' + description + '" 嗎？\\n此操作無法撤銷！')) {{
                        fetch('/admin/delete/' + id, {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json'
                            }}
                        }})
                        .then(response => response.json())
                        .then(data => {{
                            if (data.success) {{
                                alert('刪除成功！');
                                location.reload();
                            }} else {{
                                alert('刪除失敗：' + data.error);
                            }}
                        }})
                        .catch(error => {{
                            alert('刪除失敗：' + error);
                        }});
                    }}
                }}
                
                function toggleSelectAll() {{
                    const selectAll = document.getElementById('selectAll');
                    const checkboxes = document.querySelectorAll('input[name="selected_ids"]');
                    checkboxes.forEach(cb => cb.checked = selectAll.checked);
                    updateBatchDeleteButton();
                }}
                
                function updateBatchDeleteButton() {{
                    const selected = document.querySelectorAll('input[name="selected_ids"]:checked');
                    const batchBtn = document.getElementById('batchDeleteBtn');
                    batchBtn.disabled = selected.length === 0;
                    batchBtn.textContent = `刪除選中的 ${{selected.length}} 筆記錄`;
                }}
                
                function batchDelete() {{
                    const selected = document.querySelectorAll('input[name="selected_ids"]:checked');
                    const ids = Array.from(selected).map(cb => cb.value);
                    
                    if (ids.length === 0) {{
                        alert('請選擇要刪除的記錄');
                        return;
                    }}
                    
                    if (confirm(`確定要刪除選中的 ${{ids.length}} 筆記錄嗎？\\n此操作無法撤銷！`)) {{
                        fetch('/admin/batch-delete', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json'
                            }},
                            body: JSON.stringify({{ids: ids}})
                        }})
                        .then(response => response.json())
                        .then(data => {{
                            if (data.success) {{
                                alert(`成功刪除 ${{data.deleted_count}} 筆記錄！`);
                                location.reload();
                            }} else {{
                                alert('批量刪除失敗：' + data.error);
                            }}
                        }})
                        .catch(error => {{
                            alert('批量刪除失敗：' + error);
                        }});
                    }}
                }}
                
                function clearAllUserRecords() {{
                    const userId = '{user_id}';
                    const userName = '{user_profile.get("displayName", "用戶")}';
                    
                    if (confirm(`⚠️ 危險操作 ⚠️\\n\\n確定要刪除用戶 "${{userName}}" 的所有記錄嗎？\\n\\n這將刪除該用戶的所有 {len(expenses)} 筆記錄！\\n此操作無法撤銷！\\n\\n請再次確認！`)) {{
                        if (confirm(`最後確認：真的要刪除用戶 "${{userName}}" 的所有記錄嗎？`)) {{
                            fetch('/admin/clear-user/' + userId, {{
                                method: 'POST',
                                headers: {{
                                    'Content-Type': 'application/json'
                                }}
                            }})
                            .then(response => response.json())
                            .then(data => {{
                                if (data.success) {{
                                    alert(`成功刪除 ${{data.deleted_count}} 筆記錄！`);
                                    location.reload();
                                }} else {{
                                    alert('刪除失敗：' + data.error);
                                }}
                            }})
                            .catch(error => {{
                                alert('刪除失敗：' + error);
                            }});
                        }}
                    }}
                }}
            </script>
        </head>
        <body>
            <div class="header">
                <h1>👤 用戶詳情管理</h1>
                <p>查看和管理用戶記錄</p>
            </div>
            
            <div class="back">
                <a href="/admin">← 返回管理首頁</a>
            </div>
            
            <div class="user-info">
                <h2>👤 用戶資訊</h2>
        """
        
        if user_profile.get('pictureUrl'):
            html += f'<img src="{user_profile["pictureUrl"]}" alt="頭像" class="user-avatar">'
        
        html += f"""
                <strong>姓名:</strong> {user_profile.get('displayName', '未知')} <br>
                <strong>用戶ID:</strong> {user_id} <br>
                <strong>狀態:</strong> {user_profile.get('statusMessage', '無狀態訊息')} <br>
            </div>
        """
        
        if expenses:
            html += f"""
            <div class="batch-actions">
                <h3>🔧 批量操作</h3>
                <label class="select-all">
                    <input type="checkbox" id="selectAll" onchange="toggleSelectAll()"> 全選
                </label>
                <button id="batchDeleteBtn" class="batch-delete-btn" onclick="batchDelete()" disabled>
                    刪除選中的 0 筆記錄
                </button>
                <button class="clear-all-btn" onclick="clearAllUserRecords()">
                    🗑️ 清空該用戶所有記錄
                </button>
            </div>
            
            <table>
                <tr>
                    <th>選擇</th>
                    <th>ID</th>
                    <th>金額</th>
                    <th>地點</th>
                    <th>描述</th>
                    <th>分類</th>
                    <th>時間</th>
                    <th>操作</th>
                </tr>
            """
            
            for expense in expenses:
                expense_id, amount, location, description, category, timestamp = expense
                html += f"""
                <tr>
                    <td><input type="checkbox" name="selected_ids" value="{expense_id}" onchange="updateBatchDeleteButton()"></td>
                    <td>#{expense_id}</td>
                    <td>${amount:.0f}</td>
                    <td>{location or '-'}</td>
                    <td>{description}</td>
                    <td>{category or '-'}</td>
                    <td>{timestamp}</td>
                    <td>
                        <button class="delete-btn" onclick="deleteRecord({expense_id}, '{description}')">
                            🗑️ 刪除
                        </button>
                    </td>
                </tr>
                """
            
            html += "</table>"
        else:
            html += "<p>該用戶暫無記錄</p>"
        
        html += f"""
            <div class="stats">
                <h3>📊 統計摘要</h3>
                <p>記錄數量: {len(expenses)}</p>
                <p>總支出: ${total:.0f}</p>
                <p>平均支出: ${total/len(expenses):.0f if expenses else 0}</p>
            </div>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        return f"錯誤: {str(e)}"

@app.route("/admin/expenses")
def admin_all_expenses():
    """查看所有記錄"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        if db.use_postgresql:
            cursor.execute('''
                SELECT id, user_id, amount, location, description, category, timestamp
                FROM expenses
                ORDER BY timestamp DESC
                LIMIT 100
            ''')
        else:
            cursor.execute('''
                SELECT id, user_id, amount, location, description, category, timestamp
                FROM expenses
                ORDER BY timestamp DESC
                LIMIT 100
            ''')
        
        expenses = cursor.fetchall()
        conn.close()
        
        # 轉換 PostgreSQL 結果
        if db.use_postgresql:
            expenses = [tuple(expense.values()) for expense in expenses]
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>所有記錄 - LINE 記帳機器人</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; font-size: 12px; }}
                th, td {{ border: 1px solid #ddd; padding: 6px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .header {{ background-color: #FF9800; color: white; padding: 20px; text-align: center; }}
                .back {{ margin: 20px 0; }}
                .delete-btn {{ background-color: #f44336; color: white; padding: 4px 8px; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; }}
                .delete-btn:hover {{ background-color: #da190b; }}
                .batch-actions {{ margin: 20px 0; padding: 15px; background-color: #f9f9f9; border-radius: 5px; }}
                .select-all {{ margin-right: 10px; }}
                .batch-delete-btn {{ background-color: #f44336; color: white; padding: 8px 16px; border: none; border-radius: 5px; cursor: pointer; }}
                .batch-delete-btn:hover {{ background-color: #da190b; }}
                .stats {{ background-color: #e3f2fd; padding: 15px; margin: 20px 0; border-radius: 5px; }}
            </style>
            <script>
                function deleteRecord(id, description) {{
                    if (confirm('確定要刪除記錄 #' + id + ' "' + description + '" 嗎？\\n此操作無法撤銷！')) {{
                        fetch('/admin/delete/' + id, {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json'
                            }}
                        }})
                        .then(response => response.json())
                        .then(data => {{
                            if (data.success) {{
                                alert('刪除成功！');
                                location.reload();
                            }} else {{
                                alert('刪除失敗：' + data.error);
                            }}
                        }})
                        .catch(error => {{
                            alert('刪除失敗：' + error);
                        }});
                    }}
                }}
                
                function toggleSelectAll() {{
                    const selectAll = document.getElementById('selectAll');
                    const checkboxes = document.querySelectorAll('input[name="selected_ids"]');
                    checkboxes.forEach(cb => cb.checked = selectAll.checked);
                    updateBatchDeleteButton();
                }}
                
                function updateBatchDeleteButton() {{
                    const selected = document.querySelectorAll('input[name="selected_ids"]:checked');
                    const batchBtn = document.getElementById('batchDeleteBtn');
                    batchBtn.disabled = selected.length === 0;
                    batchBtn.textContent = `刪除選中的 ${{selected.length}} 筆記錄`;
                }}
                
                function batchDelete() {{
                    const selected = document.querySelectorAll('input[name="selected_ids"]:checked');
                    const ids = Array.from(selected).map(cb => cb.value);
                    
                    if (ids.length === 0) {{
                        alert('請選擇要刪除的記錄');
                        return;
                    }}
                    
                    if (confirm(`確定要刪除選中的 ${{ids.length}} 筆記錄嗎？\\n此操作無法撤銷！`)) {{
                        fetch('/admin/batch-delete', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json'
                            }},
                            body: JSON.stringify({{ids: ids}})
                        }})
                        .then(response => response.json())
                        .then(data => {{
                            if (data.success) {{
                                alert(`成功刪除 ${{data.deleted_count}} 筆記錄！`);
                                location.reload();
                            }} else {{
                                alert('批量刪除失敗：' + data.error);
                            }}
                        }})
                        .catch(error => {{
                            alert('批量刪除失敗：' + error);
                        }});
                    }}
                }}
            </script>
        </head>
        <body>
            <div class="header">
                <h1>📋 所有記錄管理</h1>
                <p>最近 100 筆記錄 (可刪除)</p>
            </div>
            
            <div class="back">
                <a href="/admin">← 返回管理首頁</a>
            </div>
            
            <div class="batch-actions">
                <h3>🔧 批量操作</h3>
                <label class="select-all">
                    <input type="checkbox" id="selectAll" onchange="toggleSelectAll()"> 全選
                </label>
                <button id="batchDeleteBtn" class="batch-delete-btn" onclick="batchDelete()" disabled>
                    刪除選中的 0 筆記錄
                </button>
            </div>
            
            <table>
                <tr>
                    <th>選擇</th>
                    <th>ID</th>
                    <th>用戶ID</th>
                    <th>金額</th>
                    <th>地點</th>
                    <th>描述</th>
                    <th>分類</th>
                    <th>時間</th>
                    <th>操作</th>
                </tr>
        """
        
        total = 0
        for expense in expenses:
            expense_id, user_id, amount, location, description, category, timestamp = expense
            total += amount
            html += f"""
                <tr>
                    <td><input type="checkbox" name="selected_ids" value="{expense_id}" onchange="updateBatchDeleteButton()"></td>
                    <td>#{expense_id}</td>
                    <td>{user_id[:15]}...</td>
                    <td>${amount:.0f}</td>
                    <td>{location or '-'}</td>
                    <td>{description}</td>
                    <td>{category or '-'}</td>
                    <td>{timestamp}</td>
                    <td>
                        <button class="delete-btn" onclick="deleteRecord({expense_id}, '{description}')">
                            🗑️ 刪除
                        </button>
                    </td>
                </tr>
            """
        
        html += f"""
            </table>
            
            <div class="stats">
                <h3>📊 統計摘要</h3>
                <p>顯示記錄數: {len(expenses)}</p>
                <p>顯示總金額: ${total:.0f}</p>
            </div>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        return f"錯誤: {str(e)}"

@app.route("/admin/delete/<int:expense_id>", methods=['POST'])
def admin_delete_expense(expense_id):
    """刪除單筆記錄"""
    try:
        # 先獲取記錄詳情用於記錄
        conn = db.get_connection()
        cursor = conn.cursor()
        
        if db.use_postgresql:
            cursor.execute('SELECT user_id, amount, description FROM expenses WHERE id = %s', (expense_id,))
        else:
            cursor.execute('SELECT user_id, amount, description FROM expenses WHERE id = ?', (expense_id,))
        
        record = cursor.fetchone()
        if not record:
            conn.close()
            return {"success": False, "error": "記錄不存在"}
        
        # 執行刪除
        if db.use_postgresql:
            cursor.execute('DELETE FROM expenses WHERE id = %s', (expense_id,))
        else:
            cursor.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted_count > 0:
            logger.info(f"管理員刪除記錄: ID={expense_id}, 用戶={record[0] if db.use_postgresql else record[0]}")
            return {"success": True, "message": "刪除成功"}
        else:
            return {"success": False, "error": "記錄不存在或已被刪除"}
            
    except Exception as e:
        logger.error(f"刪除記錄失敗: {e}")
        return {"success": False, "error": str(e)}

@app.route("/admin/batch-delete", methods=['POST'])
def admin_batch_delete():
    """批量刪除記錄"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        
        if not ids:
            return {"success": False, "error": "沒有選擇要刪除的記錄"}
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # 構建批量刪除 SQL
        if db.use_postgresql:
            placeholders = ','.join(['%s'] * len(ids))
            cursor.execute(f'DELETE FROM expenses WHERE id IN ({placeholders})', ids)
        else:
            placeholders = ','.join(['?'] * len(ids))
            cursor.execute(f'DELETE FROM expenses WHERE id IN ({placeholders})', ids)
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"管理員批量刪除: {deleted_count} 筆記錄, IDs={ids}")
        return {"success": True, "deleted_count": deleted_count, "message": f"成功刪除 {deleted_count} 筆記錄"}
        
    except Exception as e:
        logger.error(f"批量刪除失敗: {e}")
        return {"success": False, "error": str(e)}

@app.route("/admin/clear-user/<user_id>", methods=['POST'])
def admin_clear_user_records(user_id):
    """清空特定用戶的所有記錄"""
    try:
        # 先檢查用戶是否存在記錄
        conn = db.get_connection()
        cursor = conn.cursor()
        
        if db.use_postgresql:
            cursor.execute('SELECT COUNT(*) FROM expenses WHERE user_id = %s', (user_id,))
        else:
            cursor.execute('SELECT COUNT(*) FROM expenses WHERE user_id = ?', (user_id,))
        
        count_result = cursor.fetchone()
        record_count = count_result[0] if isinstance(count_result, (list, tuple)) else count_result['count']
        
        if record_count == 0:
            conn.close()
            return {"success": False, "error": "該用戶沒有記錄可刪除"}
        
        # 執行刪除
        if db.use_postgresql:
            cursor.execute('DELETE FROM expenses WHERE user_id = %s', (user_id,))
        else:
            cursor.execute('DELETE FROM expenses WHERE user_id = ?', (user_id,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"管理員清空用戶記錄: 用戶={user_id}, 刪除數量={deleted_count}")
        return {"success": True, "deleted_count": deleted_count, "message": f"成功清空用戶所有記錄"}
        
    except Exception as e:
        logger.error(f"清空用戶記錄失敗: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=PORT, debug=True) 