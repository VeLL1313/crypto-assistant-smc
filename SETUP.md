# Руководство по установке и настройке Crypto Assistant

Это руководство поможет вам правильно установить и настроить Crypto Assistant для анализа криптовалютного рынка с использованием концепции Smart Money.

## 1. Установка зависимостей

### Требования
- Python 3.8 или выше
- Доступ к API биржи (Binance, Mexc, Bybit)

### Установка необходимых пакетов

```bash
# Клонирование репозитория (если вы используете Git)
# git clone <url-репозитория>
# cd crypto_assistant

# Установка зависимостей
pip install -r requirements.txt
```

## 2. Настройка API ключей

1. Скопируйте файл `.env.example` и переименуйте его в `.env`:
   ```bash
   cp .env.example .env
   ```

2. Отредактируйте файл `.env` и добавьте свои API ключи для необходимых бирж:
   ```
   # API ключи для Binance
   BINANCE_API_KEY=ваш_api_ключ
   BINANCE_API_SECRET=ваш_api_секрет
   
   # API ключи для Bybit
   BYBIT_API_KEY=ваш_api_ключ
   BYBIT_API_SECRET=ваш_api_секрет
   
   # API ключи для MEXC
   MEXC_API_KEY=ваш_api_ключ
   MEXC_API_SECRET=ваш_api_секрет
   
   # Настройки для Telegram-уведомлений (опционально)
   TELEGRAM_BOT_TOKEN=токен_вашего_бота
   TELEGRAM_CHAT_ID=идентификатор_чата
   ```

3. Убедитесь, что файл `.env` добавлен в `.gitignore`, чтобы не раскрывать ваши API ключи

## 3. Использование

### Анализ рынка

```bash
# Базовый анализ
python main.py analyze --symbol BTC/USDT --timeframe 4h

# Анализ с построением графика
python main.py analyze --symbol ETH/USDT --timeframe 1h --plot

# Анализ с сохранением графика
python main.py analyze --symbol SOL/USDT --timeframe 1d --plot --output charts/sol_analysis.html
```

### Непрерывный мониторинг

```bash
# Мониторинг одной торговой пары
python main.py monitor --symbols BTC/USDT --timeframes 4h --interval 15

# Мониторинг нескольких торговых пар и таймфреймов
python main.py monitor --symbols BTC/USDT ETH/USDT --timeframes 1h 4h --interval 30
```

### Бэктестинг стратегии

```bash
# Простой бэктестинг
python main.py backtest --symbol BTC/USDT --timeframe 4h

# Бэктестинг с указанием периода
python main.py backtest --symbol ETH/USDT --timeframe 1d --start-date 2023-01-01 --end-date 2023-12-31

# Бэктестинг с построением графика результатов
python main.py backtest --symbol BTC/USDT --timeframe 4h --plot --output charts/btc_backtest.png
```

## 4. Настройка параметров

Основные параметры для анализа находятся в файле `config.py`. Вы можете изменить их в соответствии с вашими предпочтениями:

```python
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
```

## 5. Получение Telegram-уведомлений

Если вы хотите получать уведомления в Telegram:

1. Создайте бота через [@BotFather](https://t.me/BotFather) и получите токен
2. Узнайте ID вашего чата (можно использовать [@userinfobot](https://t.me/userinfobot))
3. Добавьте данные в файл `.env`
4. Запустите режим мониторинга для получения уведомлений о торговых сигналах

## 6. Дополнительные возможности

### Структуры Smart Money

Crypto Assistant идентифицирует следующие структуры:

- Order Blocks (OB) - блоки заказов
- Equal Highs/Lows (EQH/EQL) - равные максимумы/минимумы
- Break of Structure (BOS) - пробой структуры
- Break of Market Structure (BMS) - пробой рыночной структуры
- Sponsored Candles (SC) - спонсируемые свечи
- Wicks - фитили
- Swing Failure Pattern (SFP) - шаблон неудачного разворота
- Points of Interest (POI) - точки интереса

### Визуализация

Графики могут быть построены с использованием двух библиотек:
- Plotly (интерактивные HTML-графики)
- Matplotlib (статические изображения)

## 7. Устранение неполадок

Если у вас возникают проблемы:

1. Убедитесь, что вы используете правильные API ключи
2. Проверьте журнал ошибок в файле `crypto_assistant.log`
3. Убедитесь, что торговая пара доступна на выбранной бирже
4. Для режима мониторинга требуется стабильное интернет-соединение
