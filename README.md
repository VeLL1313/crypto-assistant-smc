# Crypto Assistant

Криптовалютный ассистент для анализа рынка, основанный на концепции Smart Money (SMC).

## Возможности

- Получение актуальных данных о криптовалютах с Binance, Mexc и Bybit
- Идентификация ключевых уровней и структур SMC (BOS/BMS, EQH/EQL, OB, SC, WICK, SFP и т.д.)
- Технический анализ с использованием индикаторов (RSI, уровни Фибоначчи, объемы)
- Визуализация графиков с отмеченными зонами интереса
- Рекомендации для входа в позицию на основе правил Smart Money
- Бэктестинг торговых стратегий
- Непрерывный мониторинг рынка и уведомления через Telegram

## Требования

- Python 3.8+
- Доступ к API биржи (Binance, Mexc, Bybit)
- Необходимые библиотеки Python (ccxt, pandas, numpy, matplotlib, plotly, ta)

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/VeLL1313/crypto-assistant-smc.git
cd crypto-assistant-smc
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Скопируйте файл `.env.example` в `.env` и настройте его:
```bash
cp .env.example .env
# Отредактируйте .env и укажите API ключи бирж и настройки для уведомлений
```

## Использование

### Анализ рынка

```bash
python app.py analyze -s BTC/USDT -t 4h -p
```

Параметры:
- `-s, --symbol`: Торговая пара (по умолчанию: BTC/USDT)
- `-t, --timeframe`: Таймфрейм (по умолчанию: 4h)
- `-l, --limit`: Количество свечей (по умолчанию: 500)
- `-p, --plot`: Построить график
- `-o, --output`: Путь для сохранения графика

### Мониторинг рынка

```bash
python app.py monitor -s BTC/USDT ETH/USDT -t 1h 4h -i 10
```

Параметры:
- `-s, --symbols`: Список торговых пар
- `-t, --timeframes`: Список таймфреймов
- `-i, --interval`: Интервал между анализами в минутах (по умолчанию: 5)

### Бэктестинг

```bash
python app.py backtest -s BTC/USDT -t 4h -sd 2023-01-01 -ed 2023-06-01 -p
```

Параметры:
- `-s, --symbol`: Торговая пара
- `-t, --timeframe`: Таймфрейм
- `-sd, --start-date`: Начальная дата (формат: YYYY-MM-DD)
- `-ed, --end-date`: Конечная дата (формат: YYYY-MM-DD)
- `-p, --plot`: Построить график результатов
- `-o, --output`: Путь для сохранения графика

## Структура проекта

- `app.py` - Точка входа в приложение
- `backtest.py` - Модуль для бэктестинга стратегий
- `cli.py` - Интерфейс командной строки
- `notification.py` - Система уведомлений
- `visualization.py` - Визуализация графиков и результатов анализа
- `crypto_assistant/` - Основные модули
  - `analysis.py` - Модуль для технического анализа и Smart Money анализа
  - `config.py` - Конфигурация приложения
  - `core.py` - Основные классы и функции
  - `exchange.py` - Взаимодействие с биржами
  - `main.py` - Основная логика
  - `examples/` - Примеры использования
    - `analyze_btc.py` - Пример анализа BTC
    - `multi_timeframe_analysis.py` - Пример анализа на нескольких таймфреймах

## Дальнейшее развитие

- Расширение библиотеки паттернов SMC
- Добавление веб-интерфейса
- Автоматическая торговля на основе сигналов
- Интеграция с дополнительными биржами

## Лицензия

MIT