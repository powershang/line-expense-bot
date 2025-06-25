#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
訊息解析器
解析用戶的記帳訊息，提取金額和描述

新格式要求：@ai 原因 錢
例如：@ai 午餐 120
"""

import re

class MessageParser:
    def __init__(self):
        # 金額相關的正則表達式
        self.amount_patterns = [
            r'(\d+(?:\.\d+)?)\s*[元塊錢]',  # 120元, 50塊, 30錢
            r'NT?\$\s*(\d+(?:\.\d+)?)',      # NT$100, $80
            r'花了?\s*(\d+(?:\.\d+)?)',      # 花了60, 花60
            r'(\d+(?:\.\d+)?)$',             # 純數字在最後
            r'^(\d+(?:\.\d+)?)$',            # 純數字
        ]
    
    def parse_message(self, message):
        """
        解析訊息，新格式：@ai 原因 錢
        
        Args:
            message (str): 用戶輸入的訊息
            
        Returns:
            dict: 解析結果，包含 amount, description, reason
        """
        result = {
            'amount': None,
            'description': '',
            'reason': '',
            'location': None,  # 不再使用
            'category': None,  # 不再使用
            'is_valid_format': False
        }
        
        # 檢查是否以 @ai 開頭
        if not message.strip().lower().startswith('@ai'):
            return result
        
        # 移除 @ai 前綴
        content = message.strip()[3:].strip()
        
        if not content:
            return result
        
        # 標記為有效格式
        result['is_valid_format'] = True
        
        # 提取金額
        amount = self._extract_amount(content)
        
        if amount:
            result['amount'] = amount
            
            # 移除金額部分，剩下的作為原因/描述
            reason = self._extract_reason(content, amount)
            result['reason'] = reason.strip()
            result['description'] = reason.strip()
        
        return result
    
    def _extract_amount(self, text):
        """提取金額"""
        for pattern in self.amount_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1))
                except (ValueError, IndexError):
                    continue
        return None
    
    def _extract_reason(self, text, amount):
        """提取原因，移除金額相關文字"""
        reason = text
        
        # 移除所有找到的金額表達
        for pattern in self.amount_patterns:
            reason = re.sub(pattern, '', reason)
        
        # 清理多餘的空白
        reason = ' '.join(reason.split())
        
        return reason
    
    def is_valid_expense(self, parsed_data):
        """
        檢查是否為有效的支出記錄
        
        Args:
            parsed_data (dict): 解析結果
            
        Returns:
            bool: 是否有效
        """
        return (parsed_data.get('is_valid_format', False) and 
                parsed_data.get('amount') is not None and 
                parsed_data.get('amount') > 0 and
                parsed_data.get('reason', '').strip() != '')
    
    def format_expense_summary(self, parsed_data):
        """
        格式化支出摘要
        
        Args:
            parsed_data (dict): 解析結果
            
        Returns:
            str: 格式化的摘要
        """
        if not self.is_valid_expense(parsed_data):
            return "❌ 無效的支出記錄"
        
        summary = f"📝 原因: {parsed_data['reason']}\n"
        summary += f"💰 金額: {parsed_data['amount']:.0f} 元"
        
        return summary
    
    def get_help_message(self):
        """取得使用說明"""
        return """💡 記帳格式說明:

📌 **新格式要求**：
必須以 @ai 開頭，格式為：@ai 原因 金額

📝 **範例**：
• @ai 午餐 120
• @ai 咖啡 50元
• @ai 停車費 30塊
• @ai 買飲料 45
• @ai 電影票 280
• @ai 油錢 800

💰 **支援的金額格式**：
• 120元、50塊、30錢
• NT$100、$80
• 純數字：120

✅ **簡化版記帳**：
• 只記錄原因和金額
• 不再需要地點和分類
• 更快速的記帳體驗

⚠️ **重要**：
訊息必須以 @ai 開頭才會被識別為記帳指令！""" 