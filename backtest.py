import logging
import matplotlib.pyplot as plt
from datetime import datetime

from analysis import TechnicalAnalysis, SmartMoneyAnalysis

logger = logging.getLogger("CryptoAssistant.Backtest")

def backtest_strategy(exchange_client, symbol, timeframe, start_date=None, end_date=None):
    """
    Выполняет бэктестинг стратегии
    
    Args:
        exchange_client: Объект ExchangeClient для получения данных
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
        df = exchange_client.get_ohlcv(symbol, timeframe, limit=1000, since=start_timestamp, end=end_timestamp)
    else:
        # Если даты не указаны, берем последние 500 свечей
        df = exchange_client.get_ohlcv(symbol, timeframe, limit=500)
    
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

def plot_backtest_results(backtest_result, save_path=None):
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