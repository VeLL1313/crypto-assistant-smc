#!/usr/bin/env python
"""
Пример мультитаймфреймного анализа нескольких криптовалют
"""

import os
import sys
import argparse
from datetime import datetime
from tabulate import tabulate

# Добавляем родительскую директорию в sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from exchange import ExchangeClient
from analysis import TechnicalAnalysis, SmartMoneyAnalysis
from config import DEFAULT_EXCHANGE

def format_price(price):
    """Форматирует цену для вывода с разделителями разрядов"""
    return f"{price:,.2f}" if price >= 1 else f"{price:.8f}"

def analyze_multi_timeframe(symbols, timeframes, exchange_id=DEFAULT_EXCHANGE):
    """
    Выполняет анализ нескольких криптовалют на нескольких таймфреймах
    
    Args:
        symbols (list): Список торговых пар для анализа
        timeframes (list): Список таймфреймов для анализа
        exchange_id (str): ID биржи
    """
    # Инициализируем клиент биржи
    exchange = ExchangeClient(exchange_id)
    
    # Сохраняем результаты анализа
    all_results = []
    
    for symbol in symbols:
        for timeframe in timeframes:
            print(f"Анализируем {symbol} на таймфрейме {timeframe}...")
            
            # Получаем OHLCV данные
            df = exchange.get_ohlcv(symbol, timeframe, 200)
            
            if df is None or len(df) == 0:
                print(f"Не удалось получить данные для {symbol} на таймфрейме {timeframe}")
                continue
            
            # Выполняем технический анализ
            ta = TechnicalAnalysis(df)
            
            # Smart Money анализ
            smc = SmartMoneyAnalysis(ta.df)
            
            # Находим торговые сетапы
            trade_setups = smc.find_trade_setups()
            
            # Получаем текущий контекст рынка
            market_context = smc.get_current_market_context()
            
            # Находим оптимальные зоны для входа
            ote_zones = smc.find_optimal_trade_entry()
            
            # Собираем рекомендацию
            recommendation = "НЕЙТРАЛЬНО"
            reason = "Нет явных сигналов"
            
            # Если есть сетапы
            if trade_setups:
                # Проверяем соответствие сетапов тренду
                trend = market_context['trend']
                
                buy_setups = [s for s in trade_setups if "buy" in s['type'].lower()]
                sell_setups = [s for s in trade_setups if "sell" in s['type'].lower()]
                
                if buy_setups and trend == "Восходящий":
                    recommendation = "ПОКУПКА"
                    reason = buy_setups[0]['desc']
                elif sell_setups and trend == "Нисходящий":
                    recommendation = "ПРОДАЖА"
                    reason = sell_setups[0]['desc']
            
            # Добавляем результат в общий список
            all_results.append({
                'symbol': symbol,
                'timeframe': timeframe,
                'price': df['close'].iloc[-1],
                'trend': market_context['trend'],
                'rsi': ta.df['rsi'].iloc[-1],
                'trade_setups_count': len(trade_setups),
                'ote_zones_count': len(ote_zones),
                'nearest_support': market_context['nearest_support'],
                'nearest_resistance': market_context['nearest_resistance'],
                'recommendation': recommendation,
                'reason': reason
            })
    
    # Выводим результаты в виде таблицы
    if all_results:
        print("\n" + "=" * 80)
        print(f"Мультитаймфреймный анализ - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Преобразуем результаты для вывода в таблицу
        table_data = []
        for result in all_results:
            table_data.append([
                result['symbol'],
                result['timeframe'],
                format_price(result['price']),
                result['trend'],
                f"{result['rsi']:.1f}",
                result['trade_setups_count'],
                result['ote_zones_count'],
                result['recommendation']
            ])
        
        # Выводим таблицу с результатами
        headers = ['Символ', 'Таймфрейм', 'Цена', 'Тренд', 'RSI', 'Сетапы', 'OTE Зоны', 'Рекомендация']
        print(tabulate(table_data, headers=headers, tablefmt='psql'))
        
        # Выводим подробности по рекомендациям
        print("\nПодробности по рекомендациям:")
        for result in all_results:
            if result['recommendation'] != "НЕЙТРАЛЬНО":
                print(f"{result['symbol']} ({result['timeframe']}): {result['recommendation']} - {result['reason']}")
    else:
        print("Не удалось получить результаты анализа")

def main():
    """Основная функция для запуска из командной строки"""
    parser = argparse.ArgumentParser(description='Мультитаймфреймный анализ криптовалют')
    
    parser.add_argument('-s', '--symbols', nargs='+', default=['BTC/USDT', 'ETH/USDT', 'SOL/USDT'],
                        help='Торговые пары для анализа')
    parser.add_argument('-t', '--timeframes', nargs='+', default=['4h', '1d'],
                        help='Таймфреймы для анализа')
    parser.add_argument('-e', '--exchange', default=DEFAULT_EXCHANGE,
                        help=f'Биржа для получения данных (по умолчанию: {DEFAULT_EXCHANGE})')
    
    args = parser.parse_args()
    
    analyze_multi_timeframe(args.symbols, args.timeframes, args.exchange)

if __name__ == "__main__":
    main()
