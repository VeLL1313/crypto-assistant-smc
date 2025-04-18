import argparse
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import logging
import os

from exchange import ExchangeClient
from analysis import TechnicalAnalysis, SmartMoneyAnalysis
from config import (
    DEFAULT_EXCHANGE, DEFAULT_TIMEFRAME, DEFAULT_LIMIT, 
    DEFAULT_SYMBOL, COLORS, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
)

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
    
    def plot_chart(self, save_path=None, plot_type='plotly'):
        """
        Строит график с результатами анализа
        
        Args:
            save_path (str): Путь для сохранения графика
            plot_type (str): Тип графика ('plotly' или 'matplotlib')
            
        Returns:
            bool: True если график построен, иначе False
        """
        if self.last_analysis is None:
            logger.error("Нет данных для построения графика. Сначала выполните анализ.")
            return False
        
        df = self.last_analysis['df']
        smc = self.last_analysis['smc']
        symbol = self.last_analysis['result']['symbol']
        timeframe = self.last_analysis['result']['timeframe']
        
        if plot_type == 'plotly':
            return self._plot_plotly(df, smc, symbol, timeframe, save_path)
        else:
            return self._plot_matplotlib(df, smc, symbol, timeframe, save_path)
    
    def _plot_plotly(self, df, smc, symbol, timeframe, save_path=None):
        """
        Строит интерактивный график с использованием Plotly
        
        Args:
            df (pd.DataFrame): DataFrame с данными
            smc (SmartMoneyAnalysis): Объект с результатами анализа
            symbol (str): Торговая пара
            timeframe (str): Таймфрейм
            save_path (str): Путь для сохранения графика
            
        Returns:
            bool: True если график построен, иначе False
        """
        try:
            # Создаем график свечей
            fig = go.Figure(data=[go.Candlestick(
                x=df.index,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='Цена'
            )])
            
            # Добавляем EMA
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['ema20'],
                line=dict(color='blue', width=1),
                name='EMA 20'
            ))
            
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['ema50'],
                line=dict(color='orange', width=1),
                name='EMA 50'
            ))
            
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['ema200'],
                line=dict(color='purple', width=1.5),
                name='EMA 200'
            ))
            
            # Добавляем структуры
            
            # Order Blocks
            for ob in smc.structures['ob_buy']:
                fig.add_shape(
                    type="rect",
                    x0=ob['timestamp'],
                    y0=ob['price_low'],
                    x1=df.index[-1],
                    y1=ob['price_high'],
                    line=dict(color=COLORS['OB_BUY'], width=1),
                    fillcolor=COLORS['OB_BUY'],
                    opacity=0.2,
                    name='OB Buy'
                )
            
            for ob in smc.structures['ob_sell']:
                fig.add_shape(
                    type="rect",
                    x0=ob['timestamp'],
                    y0=ob['price_low'],
                    x1=df.index[-1],
                    y1=ob['price_high'],
                    line=dict(color=COLORS['OB_SELL'], width=1),
                    fillcolor=COLORS['OB_SELL'],
                    opacity=0.2,
                    name='OB Sell'
                )
            
            # Линии EQH/EQL
            for eqh in smc.structures['eqh']:
                fig.add_shape(
                    type="line",
                    x0=eqh['timestamp'],
                    y0=eqh['price'],
                    x1=df.index[-1],
                    y1=eqh['price'],
                    line=dict(color=COLORS['EQH'], width=1, dash="dash"),
                    name='EQH'
                )
            
            for eql in smc.structures['eql']:
                fig.add_shape(
                    type="line",
                    x0=eql['timestamp'],
                    y0=eql['price'],
                    x1=df.index[-1],
                    y1=eql['price'],
                    line=dict(color=COLORS['EQL'], width=1, dash="dash"),
                    name='EQL'
                )
            
            # BOS/BMS
            for bos in smc.structures['bos']:
                fig.add_trace(go.Scatter(
                    x=[bos['timestamp']],
                    y=[bos['price']],
                    mode='markers',
                    marker=dict(
                        symbol='triangle-up' if 'up' in bos['type'] else 'triangle-down',
                        color=COLORS['BOS'],
                        size=12
                    ),
                    name='BOS'
                ))
            
            # SC
            for sc in smc.structures['sc']:
                fig.add_trace(go.Scatter(
                    x=[sc['timestamp']],
                    y=[sc['price']],
                    mode='markers',
                    marker=dict(
                        symbol='star',
                        color=COLORS['SC'],
                        size=12
                    ),
                    name='SC'
                ))
            
            # Wicks
            for wick in smc.structures['wick']:
                fig.add_trace(go.Scatter(
                    x=[wick['timestamp']],
                    y=[wick['price']],
                    mode='markers',
                    marker=dict(
                        symbol='diamond',
                        color=COLORS['WICK'],
                        size=10
                    ),
                    name='Wick'
                ))
            
            # SFP
            for sfp in smc.structures['sfp']:
                fig.add_trace(go.Scatter(
                    x=[sfp['timestamp']],
                    y=[sfp['price']],
                    mode='markers',
                    marker=dict(
                        symbol='x',
                        color=COLORS['SFP'],
                        size=12
                    ),
                    name='SFP'
                ))
            
            # POI
            for poi in smc.structures['poi']:
                fig.add_trace(go.Scatter(
                    x=[poi['timestamp']],
                    y=[(poi['price_high'] + poi['price_low']) / 2],
                    mode='markers',
                    marker=dict(
                        symbol='circle',
                        color=COLORS['POI'],
                        size=14,
                        line=dict(width=2, color='white')
                    ),
                    name='POI'
                ))
            
            # Добавляем OTE зоны
            ote_zones = smc.find_optimal_trade_entry()
            for i, zone in enumerate(ote_zones):
                color = 'green' if 'buy' in zone['type'] else 'red'
                fig.add_shape(
                    type="rect",
                    x0=zone['timestamp'],
                    y0=zone['price_low'],
                    x1=df.index[-1],
                    y1=zone['price_high'],
                    line=dict(color=color, width=1),
                    fillcolor=color,
                    opacity=0.1,
                    name=f'OTE Zone {i+1}'
                )
            
            # Обновляем layout
            fig.update_layout(
                title=f'{symbol} - {timeframe}',
                xaxis_title='Время',
                yaxis_title='Цена',
                height=800,
                width=1200,
                template='plotly_white',
                showlegend=True
            )
            
            # Сохраняем график если нужно
            if save_path:
                fig.write_html(save_path)
                logger.info(f"График сохранен в {save_path}")
            
            # Показываем график
            fig.show()
            
            return True
        
        except Exception as e:
            logger.error(f"Ошибка при построении графика: {e}")
            return False
    
    def _plot_matplotlib(self, df, smc, symbol, timeframe, save_path=None):
        """
        Строит статический график с использованием Matplotlib
        
        Args:
            df (pd.DataFrame): DataFrame с данными
            smc (SmartMoneyAnalysis): Объект с результатами анализа
            symbol (str): Торговая пара
            timeframe (str): Таймфрейм
            save_path (str): Путь для сохранения графика
            
        Returns:
            bool: True если график построен, иначе False
        """
        try:
            # Создаем фигуру и оси
            fig, ax = plt.subplots(figsize=(16, 8))
            
            # Рисуем свечи
            for i in range(len(df)):
                open_price = df['open'].iloc[i]
                close_price = df['close'].iloc[i]
                high_price = df['high'].iloc[i]
                low_price = df['low'].iloc[i]
                
                color = 'green' if close_price >= open_price else 'red'
                
                # Тело свечи
                ax.plot([i, i], [open_price, close_price], color=color, linewidth=4)
                
                # Верхний и нижний фитили
                ax.plot([i, i], [close_price, high_price], color=color, linewidth=1)
                ax.plot([i, i], [open_price, low_price], color=color, linewidth=1)
            
            # Рисуем EMA
            ax.plot(df['ema20'], color='blue', linewidth=1, label='EMA 20')
            ax.plot(df['ema50'], color='orange', linewidth=1, label='EMA 50')
            ax.plot(df['ema200'], color='purple', linewidth=1.5, label='EMA 200')
            
            # Добавляем структуры
            
            # Order Blocks
            for ob in smc.structures['ob_buy']:
                idx = df.index.get_loc(ob['timestamp'])
                ax.axhspan(ob['price_low'], ob['price_high'], xmin=idx/len(df), xmax=1, alpha=0.2, color=COLORS['OB_BUY'])
            
            for ob in smc.structures['ob_sell']:
                idx = df.index.get_loc(ob['timestamp'])
                ax.axhspan(ob['price_low'], ob['price_high'], xmin=idx/len(df), xmax=1, alpha=0.2, color=COLORS['OB_SELL'])
            
            # Линии EQH/EQL
            for eqh in smc.structures['eqh']:
                idx = df.index.get_loc(eqh['timestamp'])
                ax.axhline(y=eqh['price'], xmin=idx/len(df), xmax=1, color=COLORS['EQH'], linestyle='--')
            
            for eql in smc.structures['eql']:
                idx = df.index.get_loc(eql['timestamp'])
                ax.axhline(y=eql['price'], xmin=idx/len(df), xmax=1, color=COLORS['EQL'], linestyle='--')
            
            # BOS/BMS
            for bos in smc.structures['bos']:
                idx = df.index.get_loc(bos['timestamp'])
                marker = '^' if 'up' in bos['type'] else 'v'
                ax.plot(idx, bos['price'], marker=marker, markersize=10, color=COLORS['BOS'])
            
            # SC
            for sc in smc.structures['sc']:
                idx = df.index.get_loc(sc['timestamp'])
                ax.plot(idx, sc['price'], marker='*', markersize=12, color=COLORS['SC'])
            
            # Wicks
            for wick in smc.structures['wick']:
                idx = df.index.get_loc(wick['timestamp'])
                ax.plot(idx, wick['price'], marker='d', markersize=8, color=COLORS['WICK'])
            
            # SFP
            for sfp in smc.structures['sfp']:
                idx = df.index.get_loc(sfp['timestamp'])
                ax.plot(idx, sfp['price'], marker='x', markersize=10, color=COLORS['SFP'])
            
            # POI
            for poi in smc.structures['poi']:
                idx = df.index.get_loc(poi['timestamp'])
                price = (poi['price_high'] + poi['price_low']) / 2
                ax.plot(idx, price, marker='o', markersize=12, color=COLORS['POI'], mfc='none')
            
            # Добавляем OTE зоны
            ote_zones = smc.find_optimal_trade_entry()
            for zone in ote_zones:
                idx = df.index.get_loc(zone['timestamp'])
                color = 'green' if 'buy' in zone['type'] else 'red'
                ax.axhspan(zone['price_low'], zone['price_high'], xmin=idx/len(df), xmax=1, alpha=0.1, color=color)
            
            # Настройка графика
            ax.set_title(f'{symbol} - {timeframe}')
            ax.set_xlabel('Свечи')
            ax.set_ylabel('Цена')
            ax.grid(True, alpha=0.3)
            ax.legend()
            plt.tight_layout()
            
            # Сохраняем график если нужно
            if save_path:
                plt.savefig(save_path)
                logger.info(f"График сохранен в {save_path}")
            
            # Показываем график
            plt.show()
            
            return True
        
        except Exception as e:
            logger.error(f"Ошибка при построении графика: {e}")
            return False
    
    def send_telegram_notification(self, message):
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
            import requests
            
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
                            
                            # Формируем сообщение
                            message = f"*Торговый сигнал!*\n\n"
                            message += f"*Монета:* {symbol}\n"
                            message += f"*Таймфрейм:* {timeframe}\n"
                            message += f"*Текущая цена:* {analysis['last_price']:.8f}\n\n"
                            
                            message += "*Найденные сетапы:*\n"
                            for i, setup in enumerate(setups, 1):
                                message += f"{i}. {setup['type']}: {setup['desc']}\n"
                            
                            # Отправляем уведомление
                            self.send_telegram_notification(message)
                            
                            # Сохраняем график
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            chart_path = f"charts/{symbol.replace('/', '')}_tf{timeframe}_{timestamp}.html"
                            self.plot_chart(chart_path)
                
                logger.info(f"Ожидаем {interval_minutes} минут до следующего анализа...")
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            logger.info("Анализ прерван пользователем")
        except Exception as e:
            logger.error(f"Ошибка при выполнении непрерывного анализа: {e}")
    
    def backtest_strategy(self, symbol, timeframe, start_date=None, end_date=None):
        """
        Выполняет бэктестинг стратегии
        
        Args:
            symbol (str): Торговая пара
            timeframe (str): Таймфрейм
            start_date (str): Начальная дата (формат: 'YYYY-MM-DD')
            end_date (str): Конечная дата (формат: 'YYYY-MM-DD')
            
        Returns:
            dict: Результаты бэктестинга
        """
        logger.info(f"Запуск бэктестинга для {symbol} на {timeframe}")
        
        # Получаем данные
        if start_date:
            # Преобразуем дату в timestamp
            start_timestamp = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp() * 1000)
            
            # Если конечная дата не указана, берем текущую
            if not end_date:
                end_timestamp = int(datetime.now().timestamp() * 1000)
            else:
                end_timestamp = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp() * 1000)
            
            # Получаем данные с учетом дат
            df = self.exchange_client.get_ohlcv(symbol, timeframe, limit=1000, since=start_timestamp, end=end_timestamp)
        else:
            # Если даты не указаны, берем последние 500 свечей
            df = self.exchange_client.get_ohlcv(symbol, timeframe, limit=500)
        
        if df is None or len(df) == 0:
            logger.error(f"Не удалось получить данные для {symbol}")
            return None
        
        # Технический анализ
        ta = TechnicalAnalysis(df)
        
        # Smart Money анализ
        smc = SmartMoneyAnalysis(ta.df)
        
        # Результаты торговли
        trades = []
        equity = 1000  # Начальный капитал
        win_count = 0
        loss_count = 0
        
        # Проходим по всем свечам
        for i in range(50, len(df)-1):  # Начинаем с 50-й свечи для расчета индикаторов
            # Создаем подмножество данных до текущей свечи
            subset_df = df.iloc[:i+1].copy()
            
            # Технический анализ на подмножестве
            subset_ta = TechnicalAnalysis(subset_df)
            
            # Smart Money анализ на подмножестве
            subset_smc = SmartMoneyAnalysis(subset_ta.df)
            
            # Находим торговые сетапы
            trade_setups = subset_smc.find_trade_setups()
            
            # Если найдены сетапы
            if trade_setups:
                for setup in trade_setups:
                    # Проверяем, что сетап на последней свече подмножества
                    if setup['timestamp'] == subset_df.index[-1]:
                        # Получаем данные для следующей свечи
                        next_candle = df.iloc[i+1]
                        
                        # Моделируем торговлю
                        entry_price = next_candle['open']
                        
                        # Определяем направление
                        direction = 1 if setup['type'] == 'buy_setup' else -1
                        
                        # Определяем стоп-лосс и тейк-профит
                        atr = subset_df['high'].iloc[-20:].max() - subset_df['low'].iloc[-20:].min()
                        stop_loss = entry_price - direction * atr * 0.5
                        take_profit = entry_price + direction * atr * 1.5
                        
                        # Симулируем исполнение
                        exit_price = None
                        exit_reason = None
                        
                        # Проверяем следующие свечи
                        for j in range(i+1, min(i+20, len(df))):
                            future_candle = df.iloc[j]
                            
                            # Для покупки
                            if direction == 1:
                                # Сработал стоп-лосс
                                if future_candle['low'] <= stop_loss:
                                    exit_price = stop_loss
                                    exit_reason = 'stop_loss'
                                    break
                                
                                # Сработал тейк-профит
                                if future_candle['high'] >= take_profit:
                                    exit_price = take_profit
                                    exit_reason = 'take_profit'
                                    break
                            
                            # Для продажи
                            else:
                                # Сработал стоп-лосс
                                if future_candle['high'] >= stop_loss:
                                    exit_price = stop_loss
                                    exit_reason = 'stop_loss'
                                    break
                                
                                # Сработал тейк-профит
                                if future_candle['low'] <= take_profit:
                                    exit_price = take_profit
                                    exit_reason = 'take_profit'
                                    break
                        
                        # Если не было выхода из сделки, закрываем по последней цене
                        if exit_price is None:
                            exit_price = df.iloc[min(i+20, len(df)-1)]['close']
                            exit_reason = 'timeout'
                        
                        # Расчет прибыли/убытка
                        pnl = (exit_price - entry_price) * direction
                        pnl_pct = pnl / entry_price * 100
                        
                        # Обновляем капитал
                        equity += equity * pnl_pct / 100
                        
                        # Обновляем статистику
                        if pnl > 0:
                            win_count += 1
                        else:
                            loss_count += 1
                        
                        # Записываем сделку
                        trades.append({
                            'timestamp': setup['timestamp'],
                            'type': setup['type'],
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'exit_reason': exit_reason,
                            'pnl': pnl,
                            'pnl_pct': pnl_pct,
                            'equity': equity
                        })
        
        # Подводим итоги бэктестинга
        total_trades = len(trades)
        win_rate = win_count / total_trades * 100 if total_trades > 0 else 0
        avg_profit = sum(trade['pnl_pct'] for trade in trades) / total_trades if total_trades > 0 else 0
        
        # Расчет просадки
        max_equity = 1000
        max_drawdown = 0
        
        for trade in trades:
            max_equity = max(max_equity, trade['equity'])
            drawdown = (max_equity - trade['equity']) / max_equity * 100
            max_drawdown = max(max_drawdown, drawdown)
        
        # Результаты бэктестинга
        backtest_result = {
            'symbol': symbol,
            'timeframe': timeframe,
            'start_date': df.index[0],
            'end_date': df.index[-1],
            'total_trades': total_trades,
            'win_count': win_count,
            'loss_count': loss_count,
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'final_equity': equity,
            'roi': (equity - 1000) / 1000 * 100,
            'max_drawdown': max_drawdown,
            'trades': trades
        }
        
        return backtest_result
        
    def plot_backtest_results(self, backtest_result, save_path=None):
        """
        Визуализирует результаты бэктестинга
        
        Args:
            backtest_result (dict): Результаты бэктестинга
            save_path (str): Путь для сохранения графика
            
        Returns:
            bool: True если график построен, иначе False
        """
        if not backtest_result or not backtest_result['trades']:
            logger.error("Нет данных для построения графика")
            return False
        
        try:
            # Создаем график
            fig, (ax1, ax2) = pltdef plot_backtest_results(self, backtest_result, save_path=None):
        """
        Визуализирует результаты бэктестинга
        
        Args:
            backtest_result (dict): Результаты бэктестинга
            save_path (str): Путь для сохранения графика
            
        Returns:
            bool: True если график построен, иначе False
        """
        if not backtest_result or not backtest_result['trades']:
            logger.error("Нет данных для построения графика")
            return False
        
        try:
            # Создаем график
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12), gridspec_kw={'height_ratios': [3, 1]})
            
            # Подготавливаем данные для графика
            trades = backtest_result['trades']
            dates = [trade['timestamp'] for trade in trades]
            equity = [trade['equity'] for trade in trades]
            
            # График капитала
            ax1.plot(dates, equity, 'b-', linewidth=2)
            ax1.set_title(f"Результаты бэктестинга для {backtest_result['symbol']} на {backtest_result['timeframe']}")
            ax1.set_ylabel('Капитал')
            ax1.grid(True, alpha=0.3)
            
            # График сделок
            for trade in trades:
                color = 'green' if trade['pnl'] > 0 else 'red'
                marker = '^' if trade['type'] == 'buy_setup' else 'v'
                ax1.scatter(trade['timestamp'], trade['equity'], color=color, marker=marker, s=100)
            
            # График прибыли/убытка
            pnl = [trade['pnl_pct'] for trade in trades]
            colors = ['green' if p > 0 else 'red' for p in pnl]
            ax2.bar(dates, pnl, color=colors)
            ax2.set_ylabel('Прибыль/убыток (%)')
            ax2.set_xlabel('Время')
            ax2.grid(True, alpha=0.3)
            
            # Добавляем статистику на график
            stats_text = f"Всего сделок: {backtest_result['total_trades']}\n"
            stats_text += f"Win Rate: {backtest_result['win_rate']:.2f}%\n"
            stats_text += f"Средняя прибыль: {backtest_result['avg_profit']:.2f}%\n"
            stats_text += f"ROI: {backtest_result['roi']:.2f}%\n"
            stats_text += f"Макс. просадка: {backtest_result['max_drawdown']:.2f}%"
            
            ax1.text(0.02, 0.95, stats_text, transform=ax1.transAxes, fontsize=10,
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.5))
            
            plt.tight_layout()
            
            # Сохраняем график если нужно
            if save_path:
                plt.savefig(save_path)
                logger.info(f"График результатов бэктестинга сохранен в {save_path}")
            
            # Показываем график
            plt.show()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при построении графика результатов бэктестинга: {e}")
            return False


def parse_args():
    """
    Парсинг аргументов командной строки
    
    Returns:
        argparse.Namespace: Аргументы командной строки
    """
    parser = argparse.ArgumentParser(description='Crypto Assistant - инструмент для анализа криптовалютных рынков')
    
    subparsers = parser.add_subparsers(dest='command', help='Команды')
    
    # Команда для анализа рынка
    analyze_parser = subparsers.add_parser('analyze', help='Анализировать рынок')
    analyze_parser.add_argument('-s', '--symbol', default=DEFAULT_SYMBOL, help=f'Торговая пара (по умолчанию: {DEFAULT_SYMBOL})')
    analyze_parser.add_argument('-t', '--timeframe', default=DEFAULT_TIMEFRAME, help=f'Таймфрейм (по умолчанию: {DEFAULT_TIMEFRAME})')
    analyze_parser.add_argument('-l', '--limit', type=int, default=DEFAULT_LIMIT, help=f'Количество свечей (по умолчанию: {DEFAULT_LIMIT})')
    analyze_parser.add_argument('-p', '--plot', action='store_true', help='Построить график')
    analyze_parser.add_argument('-o', '--output', help='Путь для сохранения графика')
    
    # Команда для непрерывного анализа
    monitor_parser = subparsers.add_parser('monitor', help='Непрерывный анализ рынка')
    monitor_parser.add_argument('-s', '--symbols', nargs='+', default=[DEFAULT_SYMBOL], help=f'Торговые пары (по умолчанию: {DEFAULT_SYMBOL})')
    monitor_parser.add_argument('-t', '--timeframes', nargs='+', default=[DEFAULT_TIMEFRAME], help=f'Таймфреймы (по умолчанию: {DEFAULT_TIMEFRAME})')
    monitor_parser.add_argument('-i', '--interval', type=int, default=5, help='Интервал между анализами в минутах (по умолчанию: 5)')
    
    # Команда для бэктестинга
    backtest_parser = subparsers.add_parser('backtest', help='Бэктестинг стратегии')
    backtest_parser.add_argument('-s', '--symbol', default=DEFAULT_SYMBOL, help=f'Торговая пара (по умолчанию: {DEFAULT_SYMBOL})')
    backtest_parser.add_argument('-t', '--timeframe', default=DEFAULT_TIMEFRAME, help=f'Таймфрейм (по умолчанию: {DEFAULT_TIMEFRAME})')
    backtest_parser.add_argument('-sd', '--start-date', help='Начальная дата (формат: YYYY-MM-DD)')
    backtest_parser.add_argument('-ed', '--end-date', help='Конечная дата (формат: YYYY-MM-DD)')
    backtest_parser.add_argument('-p', '--plot', action='store_true', help='Построить график результатов')
    backtest_parser.add_argument('-o', '--output', help='Путь для сохранения графика')
    
    return parser.parse_args()


def main():
    """
    Основная функция для запуска из командной строки
    """
    args = parse_args()
    
    # Создаем объект CryptoAssistant
    assistant = CryptoAssistant()
    
    if args.command == 'analyze':
        # Анализируем рынок
        result = assistant.analyze_market(args.symbol, args.timeframe, args.limit)
        
        if result:
            print(f"\nАнализ рынка для {args.symbol} на таймфрейме {args.timeframe} завершен.")
            print(f"Текущая цена: {result['last_price']}")
            print(f"Контекст рынка: {result['market_context']}")
            
            if result['trade_setups']:
                print("\nНайденные торговые сетапы:")
                for i, setup in enumerate(result['trade_setups'], 1):
                    print(f"{i}. {setup['type']}: {setup['desc']}")
            else:
                print("\nТорговые сетапы не найдены.")
            
            if result['ote_zones']:
                print("\nОптимальные зоны для входа:")
                for i, zone in enumerate(result['ote_zones'], 1):
                    print(f"{i}. {zone['type']}: {zone['price_low']} - {zone['price_high']}")
            else:
                print("\nОптимальные зоны для входа не найдены.")
            
            # Строим график если нужно
            if args.plot:
                assistant.plot_chart(args.output)
        
    elif args.command == 'monitor':
        # Запускаем непрерывный анализ
        assistant.run_continuous_analysis(args.symbols, args.timeframes, args.interval)
        
    elif args.command == 'backtest':
        # Выполняем бэктестинг
        result = assistant.backtest_strategy(args.symbol, args.timeframe, args.start_date, args.end_date)
        
        if result:
            print(f"\nБэктестинг для {args.symbol} на таймфрейме {args.timeframe} завершен.")
            print(f"Всего сделок: {result['total_trades']}")
            print(f"Win Rate: {result['win_rate']:.2f}%")
            print(f"Средняя прибыль: {result['avg_profit']:.2f}%")
            print(f"ROI: {result['roi']:.2f}%")
            print(f"Макс. просадка: {result['max_drawdown']:.2f}%")
            
            # Строим график если нужно
            if args.plot:
                assistant.plot_backtest_results(result, args.output)
    
    else:
        print("Команда не указана. Используйте --help для получения справки.")


if __name__ == '__main__':
    main()