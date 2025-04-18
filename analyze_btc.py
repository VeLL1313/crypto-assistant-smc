#!/usr/bin/env python
"""
Пример скрипта для анализа BTC/USDT с визуализацией
"""

import os
import sys
import pandas as pd
from datetime import datetime

# Добавляем родительскую директорию в sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from exchange import ExchangeClient
from analysis import TechnicalAnalysis, SmartMoneyAnalysis
from config import COLORS

def format_price(price):
    """Форматирует цену для вывода с разделителями разрядов"""
    return f"{price:,.2f}" if price >= 1 else f"{price:.8f}"

def analyze_btc():
    """Анализирует текущее состояние BTC/USDT"""
    # Инициализируем клиент биржи (используем Binance по умолчанию)
    exchange = ExchangeClient("binance")
    
    # Получаем OHLCV данные
    df = exchange.get_ohlcv("BTC/USDT", "4h", 200)
    
    if df is None or len(df) == 0:
        print("Не удалось получить данные. Проверьте соединение с биржей.")
        return None
    
    # Получаем текущую цену
    current_price = df['close'].iloc[-1]
    ticker = exchange.get_ticker("BTC/USDT")
    daily_change = ticker.get('percentage', 0) if ticker else 0
    
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
    
    # Выводим результаты анализа
    print("=" * 50)
    print(f"Анализ BTC/USDT на таймфрейме 4h")
    print(f"Дата и время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    print(f"\nТекущая цена: ${format_price(current_price)} ({daily_change:+.2f}%)")
    
    # Технические индикаторы
    print("\nТехнические индикаторы:")
    print(f"RSI (14): {ta.df['rsi'].iloc[-1]:.2f} - {'Перепродан' if ta.df['rsi'].iloc[-1] < 30 else 'Перекуплен' if ta.df['rsi'].iloc[-1] > 70 else 'Нейтральный'}")
    
    # Отображаем тренд
    trend = market_context['trend']
    print(f"Текущий тренд: {trend}")
    
    # Уровни поддержки и сопротивления
    print("\nКлючевые уровни:")
    if market_context['nearest_resistance']:
        print(f"Ближайшее сопротивление: ${format_price(market_context['nearest_resistance'])}")
    else:
        print("Ближайшее сопротивление: Не найдено")
    
    if market_context['nearest_support']:
        print(f"Ближайшая поддержка: ${format_price(market_context['nearest_support'])}")
    else:
        print("Ближайшая поддержка: Не найдена")
    
    # Структуры Smart Money
    print("\nСтруктуры Smart Money в последних 10 свечах:")
    
    # Подсчет структур
    recent_struct_count = 0
    struct_types = {
        'ob_buy': "Order Block (Buy)",
        'ob_sell': "Order Block (Sell)",
        'eqh': "Equal High",
        'eql': "Equal Low",
        'bos': "Break of Structure", 
        'sc': "Sponsored Candle",
        'wick': "Significant Wick",
        'sfp': "Swing Failure Pattern",
        'poi': "Point of Interest"
    }
    
    for struct_type, struct_name in struct_types.items():
        if struct_type in smc.structures:
            recent_structures = [s for s in smc.structures[struct_type] 
                                if s['index'] >= len(df) - 10]
            if recent_structures:
                recent_struct_count += len(recent_structures)
                print(f"- {struct_name}: {len(recent_structures)} найдено")
    
    if recent_struct_count == 0:
        print("Значимых структур не найдено в последних 10 свечах")
    
    # Торговые сетапы
    print("\nТорговые сетапы:")
    if trade_setups:
        for i, setup in enumerate(trade_setups, 1):
            print(f"{i}. {setup['type'].upper()}: {setup['desc']}")
    else:
        print("Торговые сетапы не найдены")
    
    # Оптимальные точки входа
    print("\nОптимальные зоны для входа:")
    if ote_zones:
        for i, zone in enumerate(ote_zones, 1):
            zone_type = "BUY" if "buy" in zone['type'].lower() else "SELL"
            print(f"{i}. {zone_type}: ${format_price(zone['price_low'])} - ${format_price(zone['price_high'])}")
    else:
        print("Оптимальные зоны для входа не найдены")
    
    # Итоговая рекомендация
    print("\n" + "=" * 50)
    print("ИТОГОВАЯ РЕКОМЕНДАЦИЯ:")
    
    if trade_setups:
        # Если есть сетапы для покупки
        buy_setups = [s for s in trade_setups if "buy" in s['type'].lower()]
        if buy_setups and trend == "Восходящий":
            print("ПОКУПКА РЕКОМЕНДУЕТСЯ")
            for setup in buy_setups[:1]:  # Берем первый сетап для покупки
                print(f"Причина: {setup['desc']}")
        
        # Если есть сетапы для продажи
        sell_setups = [s for s in trade_setups if "sell" in s['type'].lower()]
        if sell_setups and trend == "Нисходящий":
            print("ПРОДАЖА РЕКОМЕНДУЕТСЯ")
            for setup in sell_setups[:1]:  # Берем первый сетап для продажи
                print(f"Причина: {setup['desc']}")
        
        # Если сетапы не согласуются с трендом
        if ((buy_setups and trend != "Восходящий") or 
            (sell_setups and trend != "Нисходящий")):
            print("РЕКОМЕНДУЕТСЯ ОЖИДАНИЕ")
            print("Причина: Торговые сетапы обнаружены, но не согласуются с текущим трендом")
    else:
        print("РЕКОМЕНДУЕТСЯ ОЖИДАНИЕ")
        print("Причина: Подходящие торговые сетапы не обнаружены")
    
    print("=" * 50)
    
    # Создаем график
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    
    fig, ax = plt.subplots(figsize=(16, 9))
    
    # Рисуем свечи
    for i in range(len(df.iloc[-30:])):  # Только последние 30 свечей для ясности
        idx = len(df) - 30 + i
        if idx < 0:
            continue
            
        open_price = df['open'].iloc[idx]
        close_price = df['close'].iloc[idx]
        high_price = df['high'].iloc[idx]
        low_price = df['low'].iloc[idx]
        date = df.index[idx]
        
        color = 'green' if close_price >= open_price else 'red'
        
        # Тело свечи
        ax.plot([date, date], [open_price, close_price], color=color, linewidth=4)
        
        # Верхний и нижний фитили
        ax.plot([date, date], [close_price, high_price], color=color, linewidth=1)
        ax.plot([date, date], [open_price, low_price], color=color, linewidth=1)
    
    # Рисуем EMA
    ax.plot(df.index[-30:], df['ema20'].iloc[-30:], color='blue', linewidth=1, label='EMA 20')
    ax.plot(df.index[-30:], df['ema50'].iloc[-30:], color='orange', linewidth=1, label='EMA 50')
    
    # Добавляем зоны OTE если они есть
    for zone in ote_zones:
        color = 'green' if 'buy' in zone['type'].lower() else 'red'
        ax.axhspan(zone['price_low'], zone['price_high'], alpha=0.2, color=color, 
                  label=f"OTE Zone ({zone['type']})")
    
    # Оформление графика
    ax.set_title(f"BTC/USDT - 4h", fontsize=16)
    ax.set_xlabel("Дата")
    ax.set_ylabel("Цена, USD")
    ax.grid(True, alpha=0.3)
    
    # Форматирование дат на оси X
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    plt.xticks(rotation=45)
    
    plt.legend()
    plt.tight_layout()
    
    # Сохраняем график
    chart_path = "btc_analysis.png"
    plt.savefig(chart_path)
    
    print(f"\nГрафик сохранен как {chart_path}")
    
    return {
        'price': current_price,
        'trend': trend,
        'trade_setups': trade_setups,
        'ote_zones': ote_zones,
        'chart_path': chart_path
    }

if __name__ == "__main__":
    # Устанавливаем максимальную ширину для вывода в консоль
    pd.set_option('display.width', 1000)
    pd.set_option('display.max_columns', 10)
    
    # Запускаем анализ
    analyze_btc()
