import re
from datetime import datetime

class MessageParser:
    def __init__(self):
        # 金額匹配模式 (支援不同格式)
        self.amount_patterns = [
            r'(\d+(?:\.\d+)?)\s*元',  # 100元, 250.5元
            r'(\d+(?:\.\d+)?)\s*塊',  # 100塊
            r'NT\$?\s*(\d+(?:\.\d+)?)',  # NT$100, NT100
            r'\$\s*(\d+(?:\.\d+)?)',  # $100
            r'(\d+(?:\.\d+)?)\s*dollar',  # 100dollar
            r'花了?\s*(\d+(?:\.\d+)?)',  # 花了100, 花100
            r'(\d+(?:\.\d+)?)\s*錢',  # 100錢
            r'(\d+(?:\.\d+)?)$',  # 純數字在最後
        ]
    
    def parse_message(self, text):
        """解析訊息，提取金額和原因"""
        result = {
            'amount': None,
            'reason': None,
            'description': text.strip()
        }
        
        # 提取金額
        amount = self.extract_amount(text)
        if amount:
            result['amount'] = amount
            # 移除金額部分，剩下的當作原因
            reason = self.extract_reason(text, amount)
            if reason:
                result['reason'] = reason
        
        return result
    
    def extract_amount(self, text):
        """提取金額"""
        for pattern in self.amount_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1))
                except (ValueError, IndexError):
                    continue
        
        # 如果沒有明確的金額模式，尋找純數字
        numbers = re.findall(r'\d+(?:\.\d+)?', text)
        if numbers:
            # 取最後一個數字作為金額（通常格式是 原因 金額）
            return float(numbers[-1])
        
        return None
    
    def extract_reason(self, text, amount):
        """提取原因（移除金額部分）"""
        # 移除金額相關的文字
        for pattern in self.amount_patterns:
            text = re.sub(pattern, '', text)
        
        # 移除常見的連接詞
        text = re.sub(r'[花了買吃喝在於到去]', '', text)
        
        # 清理空白和標點符號
        reason = re.sub(r'[，,。！？\s]+', ' ', text).strip()
        
        # 如果原因為空或太短，使用原始文字
        if not reason or len(reason) < 2:
            return text.strip()
        
        return reason
    
    def is_valid_expense(self, parsed_data):
        """檢查是否為有效的支出記錄"""
        return parsed_data['amount'] is not None and parsed_data['amount'] > 0
    
    def format_expense_summary(self, parsed_data):
        """格式化支出摘要"""
        if not self.is_valid_expense(parsed_data):
            return None
        
        summary = f"💰 金額: {parsed_data['amount']} 元"
        
        if parsed_data['reason']:
            summary += f"\n📝 原因: {parsed_data['reason']}"
        
        # 自動加上時間
        now = datetime.now()
        time_str = now.strftime('%Y/%m/%d %H:%M')
        summary += f"\n🕐 時間: {time_str}"
        
        return summary 