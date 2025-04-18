#!/usr/bin/env python
"""
Скрипт для тестирования соединения с криптовалютными биржами
"""

import os
import sys
import logging
from dotenv import load_dotenv
from tabulate import tabulate
from exchange import ExchangeClient

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("ConnectionTest")

def test_exchange_connection(exchange_id):
    """
    Тестирует соединение с биржей и выводит доступные торговые пары
    
    Args:
        exchange_id (str): ID биржи (binance, bybit, mexc)
    """
    try:
        logger.info(f"Тестирование соединения с биржей {exchange_id}...")
        exchange = ExchangeClient(exchange_id)
        
        # Проверка соединения путем получения списка торговых пар
        symbols = exchange.get_available_symbols()
        
        if not symbols:
            logger.error(f"Не удалось получить список торговых пар для {exchange_id}")
            return False
        
        # Выводим первые 10 торговых пар
        logger.info(f"Соединение с {exchange_id} установлено успешно!")
        print(f"\nДоступные торговые пары на {exchange_id.capitalize()} (первые 10):")
        for i, symbol in enumerate(symbols[:10], 1):
            print(f"{i}. {symbol}")
        
        # Проверяем получение OHLCV данных для BTC/USDT
        if "BTC/USDT" in symbols:
            logger.info("Тестирование получения OHLCV данных для BTC/USDT...")
            ohlcv = exchange.get_ohlcv("BTC/USDT", "1h", 5)
            
            if ohlcv is not None and not ohlcv.empty:
                print("\nПоследние данные OHLCV для BTC/USDT:")
                print(tabulate(ohlcv.tail(), headers='keys', tablefmt='psql'))
                
                # Проверяем получение текущего тикера
                ticker = exchange.get_ticker("BTC/USDT")
                if ticker:
                    print(f"\nТекущий тикер для BTC/USDT:")
                    print(f"Цена: {ticker['last']}")
                    print(f"Объем 24ч: {ticker['quoteVolume']}")
                    print(f"Изменение 24ч: {ticker.get('percentage', 'Н/Д')}%")
            else:
                logger.error("Не удалось получить OHLCV данные для BTC/USDT")
        else:
            logger.warning("BTC/USDT не найден в списке доступных торговых пар")
        
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при тестировании соединения с {exchange_id}: {e}")
        return False

def main():
    """
    Основная функция для тестирования соединения
    """
    # Загружаем переменные окружения
    load_dotenv()
    
    # Проверяем наличие API ключей
    binance_key = os.getenv('BINANCE_API_KEY')
    bybit_key = os.getenv('BYBIT_API_KEY')
    mexc_key = os.getenv('MEXC_API_KEY')
    
    print("=== Тестирование подключения к криптовалютным биржам ===\n")
    
    # Список бирж для тестирования
    exchanges = []
    
    if binance_key:
        exchanges.append("binance")
    else:
        logger.warning("API ключи для Binance не найдены в .env файле")
    
    if bybit_key:
        exchanges.append("bybit")
    else:
        logger.warning("API ключи для Bybit не найдены в .env файле")
    
    if mexc_key:
        exchanges.append("mexc")
    else:
        logger.warning("API ключи для MEXC не найдены в .env файле")
    
    if not exchanges:
        logger.error("Ни одного API ключа не найдено. Пожалуйста, настройте .env файл")
        sys.exit(1)
    
    # Тестируем соединение с каждой биржей
    success_count = 0
    for exchange_id in exchanges:
        print(f"\n--- Тестирование {exchange_id.capitalize()} ---")
        if test_exchange_connection(exchange_id):
            success_count += 1
    
    # Выводим итоги
    print(f"\n=== Итоги тестирования ===")
    print(f"Успешных подключений: {success_count} из {len(exchanges)}")
    
    if success_count == len(exchanges):
        print("Все соединения успешны! Система готова к использованию.")
    else:
        print("Некоторые соединения не удались. Проверьте журнал для деталей.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
