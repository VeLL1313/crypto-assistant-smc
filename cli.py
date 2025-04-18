import argparse
import logging
from config import (
    DEFAULT_EXCHANGE, DEFAULT_TIMEFRAME, DEFAULT_LIMIT, DEFAULT_SYMBOL
)

logger = logging.getLogger("CryptoAssistant.CLI")

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

def handle_analyze_command(args, crypto_assistant):
    """
    Обрабатывает команду 'analyze'
    
    Args:
        args: Аргументы командной строки
        crypto_assistant: Объект CryptoAssistant
    """
    from visualization import plot_chart
    
    # Анализируем рынок
    result = crypto_assistant.analyze_market(args.symbol, args.timeframe, args.limit)
    
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
            plot_chart(crypto_assistant, args.output)
    else:
        print(f"Не удалось выполнить анализ для {args.symbol}")

def handle_monitor_command(args, crypto_assistant):
    """
    Обрабатывает команду 'monitor'
    
    Args:
        args: Аргументы командной строки
        crypto_assistant: Объект CryptoAssistant
    """
    # Запускаем непрерывный анализ
    crypto_assistant.run_continuous_analysis(args.symbols, args.timeframes, args.interval)

def handle_backtest_command(args, crypto_assistant):
    """
    Обрабатывает команду 'backtest'
    
    Args:
        args: Аргументы командной строки
        crypto_assistant: Объект CryptoAssistant
    """
    from backtest import backtest_strategy, plot_backtest_results
    
    # Выполняем бэктестинг
    result = backtest_strategy(crypto_assistant.exchange_client, args.symbol, args.timeframe, args.start_date, args.end_date)
    
    if result:
        print(f"\nБэктестинг для {args.symbol} на таймфрейме {args.timeframe} завершен.")
        print(f"Всего сделок: {result['total_trades']}")
        print(f"Win Rate: {result['win_rate']:.2f}%")
        print(f"Средняя прибыль: {result['avg_profit']:.2f}%")
        print(f"ROI: {result['roi']:.2f}%")
        print(f"Макс. просадка: {result['max_drawdown']:.2f}%")
        
        # Строим график если нужно
        if args.plot:
            plot_backtest_results(result, args.output)
    else:
        print(f"Не удалось выполнить бэктестинг для {args.symbol}")

def process_command(args, crypto_assistant):
    """
    Обрабатывает команду из командной строки
    
    Args:
        args: Аргументы командной строки
        crypto_assistant: Объект CryptoAssistant
    """
    if args.command == 'analyze':
        handle_analyze_command(args, crypto_assistant)
    elif args.command == 'monitor':
        handle_monitor_command(args, crypto_assistant)
    elif args.command == 'backtest':
        handle_backtest_command(args, crypto_assistant)
    else:
        print("Команда не указана. Используйте --help для получения справки.")