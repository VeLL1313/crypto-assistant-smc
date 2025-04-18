import logging
import os
import time
from datetime import datetime

from exchange import ExchangeClient
from analysis import TechnicalAnalysis, SmartMoneyAnalysis
from config import (
    DEFAULT_EXCHANGE, DEFAULT_TIMEFRAME, DEFAULT_LIMIT, 
    DEFAULT_SYMBOL
)

logger = logging.getLogger("CryptoAssistant.Core")

class CryptoAssistant:
    def __init__(self, exchange_id=DEFAULT_EXCHANGE):
        """
        Инициализирует CryptoAssistant
        
        Args:
            exchange_id (str): ID биржи (binance, bybit, mexc)
        """
        self.exchange_client = ExchangeClient(exchange_id)
        self.last_analysis = None
        
        # Создаем папку для сохранения графиков
        os.makedirs('charts', exist_ok=True)
    
    def analyze_market(self, symbol=DEFAULT_SYMBOL, timeframe=DEFAULT_TIMEFRAME, limit=DEFAULT_LIMIT):
        """
        Анализирует рынок и находит торговые возможности
        
        Args:
            symbol (str): Торговая пара (например, 'BTC/USDT')
            timeframe (str): Таймфрейм ('1m', '5m', '15m', '30m', '1h', '4h', '1d')
            limit (int): Количество свечей для анализа
            
        Returns:
            dict: Результаты анализа
        """
        logger.info(f"Анализируем {symbol} на таймфрейме {timeframe}")
        
        # Получаем данные
        df = self.exchange_client.get_ohlcv(symbol, timeframe, limit)
        
        if df is None or len(df) == 0:
            logger.error(f"Не удалось получить данные для {symbol}")
            return None
        
        # Технический анализ
        ta = TechnicalAnalysis(df)
        
        # Smart Money анализ
        smc = SmartMoneyAnalysis(ta.df)
        
        # Находим торговые сетапы
        trade_setups = smc.find_trade_setups()
        
        # Получаем текущий контекст рынка
        market_context = smc.get_current_market_context()
        
        # Находим оптимальные зоны для входа
        ote_zones = smc.find_optimal_trade_entry()
        
        # Формируем результат анализа
        analysis_result = {
            'symbol': symbol,
            'timeframe': timeframe,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'last_price': df['close'].iloc[-1],
            'market_context': market_context,
            'trade_setups': trade_setups,
            'ote_zones': ote_zones,
            'structures': smc.structures
        }
        
        # Сохраняем результат для последующего доступа
        self.last_analysis = {
            'df': df,
            'ta': ta,
            'smc': smc,
            'result': analysis_result
        }
        
        return analysis_result
    
    def run_continuous_analysis(self, symbols, timeframes, interval_minutes=5):
        """
        Запускает непрерывный анализ рынка с заданным интервалом
        
        Args:
            symbols (list): Список торговых пар
            timeframes (list): Список таймфреймов
            interval_minutes (int): Интервал между анализами в минутах
        """
        logger.info(f"Запуск непрерывного анализа. Интервал: {interval_minutes} минут")
        
        try:
            while True:
                logger.info("Начинаем новый цикл анализа...")
                
                for symbol in symbols:
                    for timeframe in timeframes:
                        # Анализируем рынок
                        analysis = self.analyze_market(symbol, timeframe)
                        
                        if not analysis:
                            continue
                        
                        # Получаем сетапы
                        setups = analysis['trade_setups']
                        
                        # Если есть сетапы, отправляем уведомление и сохраняем график
                        if setups:
                            logger.info(f"Найдены торговые сетапы для {symbol} на {timeframe}")
                            
                            # Импортируем модули динамически для избежания циклических импортов
                            from notification import send_telegram_notification
                            from visualization import plot_chart
                            
                            # Формируем сообщение
                            message = f"*Торговый сигнал!*\n\n"
                            message += f"*Монета:* {symbol}\n"
                            message += f"*Таймфрейм:* {timeframe}\n"
                            message += f"*Текущая цена:* {analysis['last_price']:.8f}\n\n"
                            
                            message += "*Найденные сетапы:*\n"
                            for i, setup in enumerate(setups, 1):
                                message += f"{i}. {setup['type']}: {setup['desc']}\n"
                            
                            # Отправляем уведомление
                            send_telegram_notification(message)
                            
                            # Сохраняем график
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            chart_path = f"charts/{symbol.replace('/', '')}_tf{timeframe}_{timestamp}.html"
                            plot_chart(self, chart_path)
                
                logger.info(f"Ожидаем {interval_minutes} минут до следующего анализа...")
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            logger.info("Анализ прерван пользователем")
        except Exception as e:
            logger.error(f"Ошибка при выполнении непрерывного анализа: {e}")
            
    def get_available_symbols(self):
        """
        Получает список доступных торговых пар с биржи
        
        Returns:
            list: Список доступных торговых пар
        """
        return self.exchange_client.get_available_symbols()
        
    def get_available_timeframes(self):
        """
        Получает список доступных таймфреймов
        
        Returns:
            list: Список доступных таймфреймов
        """
        return ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M']