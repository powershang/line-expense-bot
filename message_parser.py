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
        解析訊息，支援格式：
        1. @ai 原因 錢 (記帳)
        2. @ai /del #數字 (刪除記錄)
        
        Args:
            message (str): 用戶輸入的訊息
            
        Returns:
            dict: 解析結果，包含 amount, description, reason, delete_id
        """
        result = {
            'amount': None,
            'description': '',
            'reason': '',
            'location': None,  # 不再使用
            'category': None,  # 不再使用
            'is_valid_format': False,
            'delete_id': None,  # 新增：要刪除的記錄 ID
            'action_type': None  # 新增：動作類型 ('expense' 或 'delete')
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
        
        # 檢查是否為刪除指令
        if content.lower().startswith('/del'):
            return self._parse_delete_command(content, result)
        
        # 否則解析為記帳指令
        return self._parse_expense_command(content, result)
    
    def _parse_delete_command(self, content, result):
        """解析刪除指令：/del #數字"""
        result['action_type'] = 'delete'
        
        # 使用正則表達式匹配 /del #數字 格式
        delete_pattern = r'/del\s+#(\d+)'
        match = re.search(delete_pattern, content, re.IGNORECASE)
        
        if match:
            try:
                delete_id = int(match.group(1))
                result['delete_id'] = delete_id
                result['description'] = f'刪除記錄 #{delete_id}'
            except ValueError:
                pass
        
        return result
    
    def _parse_expense_command(self, content, result):
        """解析記帳指令：原因 金額"""
        result['action_type'] = 'expense'
        
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
        if not parsed_data.get('is_valid_format', False):
            return False
            
        action_type = parsed_data.get('action_type')
        
        if action_type == 'expense':
            return (parsed_data.get('amount') is not None and 
                    parsed_data.get('amount') > 0 and
                    parsed_data.get('reason', '').strip() != '')
        
        # 刪除指令不算作支出記錄
        return False
    
    def is_valid_delete(self, parsed_data):
        """
        檢查是否為有效的刪除指令
        
        Args:
            parsed_data (dict): 解析結果
            
        Returns:
            bool: 是否有效的刪除指令
        """
        return (parsed_data.get('is_valid_format', False) and
                parsed_data.get('action_type') == 'delete' and
                parsed_data.get('delete_id') is not None and
                parsed_data.get('delete_id') > 0)

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

📌 **記帳格式**：
@ai 原因 金額

📝 **記帳範例**：
• @ai 午餐 120
• @ai 咖啡 50元
• @ai 停車費 30塊
• @ai 買飲料 45
• @ai 電影票 280
• @ai 油錢 800

🗑️ **刪除記錄格式**：
@ai /del #記錄編號

📝 **刪除範例**：
• @ai /del #23
• @ai /del #156
• @ai /del #7

💰 **支援的金額格式**：
• 120元、50塊、30錢
• NT$100、$80
• 純數字：120

✅ **簡化版記帳**：
• 只記錄原因和金額
• 不再需要地點和分類
• 更快速的記帳體驗
• 支援直接刪除記錄

⚠️ **重要**：
• 訊息必須以 @ai 開頭才會被識別！
• 只能刪除自己的記錄
• 刪除後無法復原，請小心使用""" 