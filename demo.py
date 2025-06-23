#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LINE 記帳機器人本地演示
可以在不設定 LINE Bot 的情況下測試核心功能
"""

from database import ExpenseDatabase
from message_parser import MessageParser
from datetime import datetime

class LocalDemo:
    def __init__(self):
        self.db = ExpenseDatabase()
        self.parser = MessageParser()
        self.user_id = "demo_user"
        
    def process_message(self, message):
        """處理訊息並返回回應"""
        # 檢查指令
        if message.strip() == "查詢":
            return self.show_recent_expenses()
        elif message.strip() == "本月":
            return self.show_monthly_summary()
        elif message.strip() == "幫助":
            return self.show_help()
        
        # 嘗試解析為支出記錄
        parsed_data = self.parser.parse_message(message)
        
        if self.parser.is_valid_expense(parsed_data):
            return self.add_expense(parsed_data)
        else:
            return self.suggest_format(message)
    
    def add_expense(self, parsed_data):
        """新增支出記錄"""
        expense_id = self.db.add_expense(
            user_id=self.user_id,
            amount=parsed_data['amount'],
            location=parsed_data['location'],
            description=parsed_data['description'],
            category=parsed_data['category']
        )
        
        summary = self.parser.format_expense_summary(parsed_data)
        return f"✅ 記帳成功！\n\n{summary}\n\n記錄編號: #{expense_id}"
    
    def show_recent_expenses(self):
        """顯示最近的支出記錄"""
        expenses = self.db.get_user_expenses(self.user_id, limit=5)
        
        if not expenses:
            return "📋 目前沒有支出記錄。"
        
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
        return response
    
    def show_monthly_summary(self):
        """顯示本月支出摘要"""
        now = datetime.now()
        summary = self.db.get_monthly_summary(self.user_id, now.year, now.month)
        
        if not summary:
            return f"📊 {now.year}年{now.month}月目前沒有支出記錄。"
        
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
        
        return response
    
    def show_help(self):
        """顯示幫助訊息"""
        return """🤖 LINE 記帳機器人 (本地演示)

💬 支援的訊息格式:
• "在7-11買飲料50元"
• "午餐花了120塊"  
• "停車費30元"
• "星巴克咖啡150"

📋 指令:
• "查詢" - 查看最近記錄
• "本月" - 本月支出摘要
• "幫助" - 顯示此說明
• "exit" - 結束程式

🏷️ 自動分類：餐飲、購物、交通、娛樂、醫療"""
    
    def suggest_format(self, message):
        """建議正確格式"""
        return f"""🤔 無法識別金額: "{message}"

💡 請試試:
• "在[地點][消費內容][金額]元"
• "花了[金額]元買[物品]"
• "[地點][金額]塊"

或輸入 "幫助" 查看說明。"""

def main():
    """主程式"""
    print("🤖 LINE 記帳機器人 - 本地演示")
    print("=" * 50)
    print("💡 輸入 'exit' 結束程式\n")
    
    demo = LocalDemo()
    
    # 顯示歡迎訊息
    print(demo.show_help())
    print("\n" + "=" * 50 + "\n")
    
    while True:
        try:
            # 取得用戶輸入
            user_input = input("💬 請輸入訊息: ").strip()
            
            if user_input.lower() == 'exit':
                print("👋 再見！")
                break
            
            if not user_input:
                continue
            
            # 處理訊息
            response = demo.process_message(user_input)
            print(f"\n🤖 機器人回應:\n{response}\n")
            print("-" * 50 + "\n")
            
        except KeyboardInterrupt:
            print("\n👋 程式已結束")
            break
        except Exception as e:
            print(f"\n❌ 發生錯誤: {e}\n")

if __name__ == "__main__":
    main() 