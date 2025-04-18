#!/usr/bin/env python3
"""
Crypto Assistant - Инструмент для анализа криптовалютных рынков
на основе концепции Smart Money (SMC)

Этот файл является точкой входа в приложение.
"""

import logging
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crypto_assistant.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("CryptoAssistant")

def main():
    """
    Основная функция для запуска приложения из командной строки
    """
    from core import CryptoAssistant
    from cli import parse_args, process_command
    
    # Создаем папку для сохранения графиков
    os.makedirs('charts', exist_ok=True)
    
    # Парсим аргументы командной строки
    args = parse_args()
    
    # Создаем объект CryptoAssistant
    assistant = CryptoAssistant()
    
    # Обрабатываем команду
    process_command(args, assistant)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Приложение завершено пользователем")
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}", exc_info=True)