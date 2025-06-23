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
        ]
        
        # 地點關鍵字
        self.location_keywords = [
            '在', '於', '到', '去', '買', '吃', '地點', '位置', '店', '餐廳', '超市', '便利商店', '商店'
        ]
        
        # 類別關鍵字
        self.category_mapping = {
            '餐廳': '餐飲', '吃': '餐飲', '早餐': '餐飲', '午餐': '餐飲', '晚餐': '餐飲', '喝': '餐飲',
            '咖啡': '餐飲', '飲料': '餐飲', '小吃': '餐飲', '食物': '餐飲',
            '超市': '購物', '便利商店': '購物', '商店': '購物', '買': '購物', '購物': '購物',
            '衣服': '購物', '鞋子': '購物', '包包': '購物',
            '交通': '交通', '車費': '交通', '油錢': '交通', '停車': '交通', '捷運': '交通',
            '公車': '交通', '計程車': '交通', 'uber': '交通', 'taxi': '交通',
            '娛樂': '娛樂', '電影': '娛樂', '遊戲': '娛樂', 'ktv': '娛樂',
            '醫療': '醫療', '看病': '醫療', '藥': '醫療', '診所': '醫療', '醫院': '醫療'
        }
    
    def parse_message(self, text):
        """解析訊息，提取金額、地點和類別"""
        result = {
            'amount': None,
            'location': None,
            'category': None,
            'description': text.strip()
        }
        
        # 提取金額
        amount = self.extract_amount(text)
        if amount:
            result['amount'] = amount
        
        # 提取地點
        location = self.extract_location(text)
        if location:
            result['location'] = location
        
        # 推測類別
        category = self.extract_category(text)
        if category:
            result['category'] = category
        
        return result
    
    def extract_amount(self, text):
        """提取金額"""
        for pattern in self.amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except (ValueError, IndexError):
                    continue
        
        # 如果沒有明確的金額模式，尋找純數字
        numbers = re.findall(r'\d+(?:\.\d+)?', text)
        if numbers:
            # 取最大的數字作為金額 (通常金額是最大的數字)
            amounts = [float(n) for n in numbers]
            return max(amounts)
        
        return None
    
    def extract_location(self, text):
        """提取地點"""
        # 尋找地點關鍵字後的內容
        for keyword in self.location_keywords:
            pattern = f'{keyword}([^，,。！？\s]+)'
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        # 尋找常見地點名稱
        location_patterns = [
            r'([\u4e00-\u9fff]+(?:店|館|廳|場|中心|超市|便利商店|餐廳))',  # 中文店名
            r'([A-Za-z\s]+(?:store|shop|restaurant|cafe|market))',  # 英文店名
            r'(7-11|全家|OK|萊爾富|星巴克|麥當勞|肯德基)',  # 連鎖店名
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def extract_category(self, text):
        """根據關鍵字推測類別"""
        text_lower = text.lower()
        
        for keyword, category in self.category_mapping.items():
            if keyword in text_lower:
                return category
        
        return '其他'
    
    def is_valid_expense(self, parsed_data):
        """檢查是否為有效的支出記錄"""
        return parsed_data['amount'] is not None and parsed_data['amount'] > 0
    
    def format_expense_summary(self, parsed_data):
        """格式化支出摘要"""
        if not self.is_valid_expense(parsed_data):
            return None
        
        summary = f"💰 金額: {parsed_data['amount']} 元"
        
        if parsed_data['location']:
            summary += f"\n📍 地點: {parsed_data['location']}"
        
        if parsed_data['category']:
            summary += f"\n🏷️ 類別: {parsed_data['category']}"
        
        return summary 