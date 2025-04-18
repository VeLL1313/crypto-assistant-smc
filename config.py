import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# API ключи для бирж
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')

BYBIT_API_KEY = os.getenv('BYBIT_API_KEY')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET')

MEXC_API_KEY = os.getenv('MEXC_API_KEY')
MEXC_API_SECRET = os.getenv('MEXC_API_SECRET')

# Настройки для уведомлений
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Настройки для торговли
DEFAULT_EXCHANGE = 'binance'  # binance, bybit, mexc
DEFAULT_TIMEFRAME = '4h'  # 1m, 5m, 15m, 30m, 1h, 4h, 1d
DEFAULT_LIMIT = 500  # Количество свечей для анализа
DEFAULT_SYMBOL = 'BTC/USDT'

# Настройки для технического анализа
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# Настройки для SMC анализа
PREMIUM_ZONE = 0.618  # Уровень выше 0.5 для Premium zone
DISCOUNT_ZONE = 0.382  # Уровень ниже 0.5 для Discount zone
EQUILIBRIUM_LEVEL = 0.5  # Уровень равновесия

# Конфигурация для отображения
COLORS = {
    'OB_BUY': 'green',
    'OB_SELL': 'red',
    'EQH': 'blue',
    'EQL': 'blue',
    'BOS': 'purple',
    'BMS': 'orange',
    'SC': 'magenta',
    'WICK': 'cyan',
    'SFP': 'yellow',
    'POI': 'darkgreen'
}