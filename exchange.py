import ccxt
import pandas as pd
import numpy as np
from datetime import datetime
import time
import pytz
from config import (
    BINANCE_API_KEY, BINANCE_API_SECRET,
    BYBIT_API_KEY, BYBIT_API_SECRET,
    MEXC_API_KEY, MEXC_API_SECRET
)

class ExchangeClient:
    def __init__(self, exchange_id='binance'):
        """
        Инициализирует клиент для работы с биржей
        
        Args:
            exchange_id (str): ID биржи (binance, bybit, mexc)
        """
        self.exchange_id = exchange_id.lower()
        self.exchange = self._init_exchange()
    
    def _init_exchange(self):
        """
        Инициализирует соединение с биржей
        
        Returns:
            ccxt.Exchange: Объект для работы с биржей
        """
        exchange_config = {}
        
        if self.exchange_id == 'binance':
            exchange_config = {
                'apiKey': BINANCE_API_KEY,
                'secret': BINANCE_API_SECRET,
                'enableRateLimit': True,
                'options': {'defaultType': 'future'}  # Используем фьючерсы по умолчанию
            }
            exchange = ccxt.binance(exchange_config)
        
        elif self.exchange_id == 'bybit':
            exchange_config = {
                'apiKey': BYBIT_API_KEY,
                'secret': BYBIT_API_SECRET,
                'enableRateLimit': True,
            }
            exchange = ccxt.bybit(exchange_config)
        
        elif self.exchange_id == 'mexc':
            exchange_config = {
                'apiKey': MEXC_API_KEY,
                'secret': MEXC_API_SECRET,
                'enableRateLimit': True,
            }
            exchange = ccxt.mexc(exchange_config)
        
        else:
            raise ValueError(f"Неподдерживаемая биржа: {self.exchange_id}")
        
        return exchange
    
    def get_ohlcv(self, symbol, timeframe='4h', limit=500):
        """
        Получает OHLCV данные с биржи
        
        Args:
            symbol (str): Торговая пара (например, 'BTC/USDT')
            timeframe (str): Таймфрейм ('1m', '5m', '15m', '30m', '1h', '4h', '1d')
            limit (int): Количество свечей
            
        Returns:
            pd.DataFrame: DataFrame с OHLCV данными
        """
        try:
            # Получаем данные
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            # Преобразуем в DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Конвертируем timestamp в datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
        
        except Exception as e:
            print(f"Ошибка при получении OHLCV данных: {e}")
            return None
    
    def get_ticker(self, symbol):
        """
        Получает текущую информацию о торговой паре
        
        Args:
            symbol (str): Торговая пара (например, 'BTC/USDT')
            
        Returns:
            dict: Информация о торговой паре
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            print(f"Ошибка при получении ticker: {e}")
            return None
    
    def get_order_book(self, symbol, limit=100):
        """
        Получает ордербук для торговой пары
        
        Args:
            symbol (str): Торговая пара (например, 'BTC/USDT')
            limit (int): Глубина ордербука
            
        Returns:
            dict: Ордербук с покупками и продажами
        """
        try:
            order_book = self.exchange.fetch_order_book(symbol, limit)
            return order_book
        except Exception as e:
            print(f"Ошибка при получении ордербука: {e}")
            return None
            
    def get_available_symbols(self):
        """
        Получает список доступных торговых пар
        
        Returns:
            list: Список доступных торговых пар
        """
        try:
            markets = self.exchange.load_markets()
            symbols = list(markets.keys())
            return symbols
        except Exception as e:
            print(f"Ошибка при получении списка символов: {e}")
            return []

    def get_funding_rate(self, symbol):
        """
        Получает текущую ставку финансирования для фьючерсов
        
        Args:
            symbol (str): Торговая пара (например, 'BTC/USDT')
            
        Returns:
            float: Ставка финансирования
        """
        try:
            if hasattr(self.exchange, 'fetch_funding_rate'):
                funding_rate = self.exchange.fetch_funding_rate(symbol)
                return funding_rate
            else:
                return None
        except Exception as e:
            print(f"Ошибка при получении ставки финансирования: {e}")
            return None