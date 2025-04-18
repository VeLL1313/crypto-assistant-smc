import logging
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger("CryptoAssistant.Notification")

def send_telegram_notification(message):
    """
    Отправляет уведомление в Telegram
    
    Args:
        message (str): Текст сообщения
        
    Returns:
        bool: True если сообщение отправлено, иначе False
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Не настроены Telegram уведомления. Проверьте конфигурацию.")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            logger.info("Уведомление в Telegram отправлено успешно")
            return True
        else:
            logger.error(f"Ошибка при отправке уведомления в Telegram: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления в Telegram: {e}")
        return False

def send_email_notification(subject, message, to_email):
    """
    Отправляет уведомление по электронной почте
    
    Args:
        subject (str): Тема письма
        message (str): Текст сообщения
        to_email (str): Email получателя
        
    Returns:
        bool: True если сообщение отправлено, иначе False
    """
    # TODO: Реализовать отправку email уведомлений
    logger.warning("Функция отправки email уведомлений еще не реализована")
    return False