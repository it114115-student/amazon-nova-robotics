"""
Message templates for API responses
"""

from typing import Dict

# Welcome messages by language
WELCOME_MESSAGES = {
    "zh": "你好！我是智能助手，很高興為您服務。有什麼我可以幫助您的嗎？",
    "en": "Hello! I'm your AI assistant. How can I help you today?",
}

# Goodbye messages by language
GOODBYE_MESSAGES = {
    "zh": "再見！期待下次為您服務。",
    "en": "Goodbye! Looking forward to serving you again.",
}

# Recommended questions by language
RECOMMENDED_QUESTIONS = {
    "zh": [
        "你能做什麼？",
        "幫我控制機器人",
        "機器人向前移動",
        "停止所有動作",
        "顯示機器人狀態",
    ],
    "en": [
        "What can you do?",
        "Help me control the robot",
        "Move the robot forward",
        "Stop all actions",
        "Show robot status",
    ],
}


def get_message(message_dict: Dict[str, str], language_code: str, default_lang: str = "zh") -> str:
    """
    Get message for specified language with fallback.
    
    Args:
        message_dict: Dictionary mapping language codes to messages
        language_code: Requested language code
        default_lang: Default language if requested not found
        
    Returns:
        Message string in requested or default language
    """
    return message_dict.get(language_code, message_dict.get(default_lang, ""))
