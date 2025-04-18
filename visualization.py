import matplotlib.pyplot as plt
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os
from datetime import datetime
import logging
from config import COLORS

# Настройка логирования
logger = logging.getLogger("CryptoAssistant.Visualization")

class ChartVisualizer:
    """
    Класс для визуализации графиков и результатов анализа
    """
    def __init__(self, save_dir='charts'):
        """
        Инициализирует визуализатор графиков
        
        Args:
            save_dir (str): Директория для сохранения графиков
        """
        self.save_dir = save_dir
        
        # Создаем директорию для сохранения графиков, если её нет
        os.makedirs(save_dir, exist_ok=True)
    
    def plot_with_plotly(self, df, smc_structures, symbol, timeframe, save_path=None):
        """
        Строит интерактивный график с использованием Plotly
        
        Args:
            df (pd.DataFrame): DataFrame с данными
            smc_structures (dict): Словарь с структурами SMC
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
            if 'ema20' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df['ema20'],
                    line=dict(color='blue', width=1),
                    name='EMA 20'
                ))
            
            if 'ema50' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df['ema50'],
                    line=dict(color='orange', width=1),
                    name='EMA 50'
                ))
            
            if 'ema200' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df['ema200'],
                    line=dict(color='purple', width=1.5),
                    name='EMA 200'
                ))
            
            # Добавляем структуры
            
            # Order Blocks
            if 'ob_buy' in smc_structures:
                for ob in smc_structures['ob_buy']:
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
            
            if 'ob_sell' in smc_structures:
                for ob in smc_structures['ob_sell']:
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
            if 'eqh' in smc_structures:
                for eqh in smc_structures['eqh']:
                    fig.add_shape(
                        type="line",
                        x0=eqh['timestamp'],
                        y0=eqh['price'],
                        x1=df.index[-1],
                        y1=eqh['price'],
                        line=dict(color=COLORS['EQH'], width=1, dash="dash"),
                        name='EQH'
                    )
            
            if 'eql' in smc_structures:
                for eql in smc_structures['eql']:
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
            if 'bos' in smc_structures:
                for bos in smc_structures['bos']:
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
            if 'sc' in smc_structures:
                for sc in smc_structures['sc']:
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
            if 'wick' in smc_structures:
                for wick in smc_structures['wick']:
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
            if 'sfp' in smc_structures:
                for sfp in smc_structures['sfp']:
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
            if 'poi' in smc_structures:
                for poi in smc_structures['poi']:
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
            
            # Добавляем OTE зоны если есть
            if 'ote_zones' in smc_structures:
                for i, zone in enumerate(smc_structures['ote_zones']):
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
            logger.error(f"Ошибка при построении графика с Plotly: {e}")
            return False
    
    def plot_with_matplotlib(self, df, smc_structures, symbol, timeframe, save_path=None):
        """
        Строит статический график с использованием Matplotlib
        
        Args:
            df (pd.DataFrame): DataFrame с данными
            smc_structures (dict): Словарь с структурами SMC
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
            if 'ema20' in df.columns:
                ax.plot(df['ema20'], color='blue', linewidth=1, label='EMA 20')
            
            if 'ema50' in df.columns:
                ax.plot(df['ema50'], color='orange', linewidth=1, label='EMA 50')
            
            if 'ema200' in df.columns:
                ax.plot(df['ema200'], color='purple', linewidth=1.5, label='EMA 200')
            
            # Добавляем структуры
            
            # Order Blocks
            if 'ob_buy' in smc_structures:
                for ob in smc_structures['ob_buy']:
                    idx = df.index.get_loc(ob['timestamp'])
                    ax.axhspan(ob['price_low'], ob['price_high'], xmin=idx/len(df), xmax=1, alpha=0.2, color=COLORS['OB_BUY'])
            
            if 'ob_sell' in smc_structures:
                for ob in smc_structures['ob_sell']:
                    idx = df.index.get_loc(ob['timestamp'])
                    ax.axhspan(ob['price_low'], ob['price_high'], xmin=idx/len(df), xmax=1, alpha=0.2, color=COLORS['OB_SELL'])
            
            # Линии EQH/EQL
            if 'eqh' in smc_structures:
                for eqh in smc_structures['eqh']:
                    idx = df.index.get_loc(eqh['timestamp'])
                    ax.axhline(y=eqh['price'], xmin=idx/len(df), xmax=1, color=COLORS['EQH'], linestyle='--')
            
            if 'eql' in smc_structures:
                for eql in smc_structures['eql']:
                    idx = df.index.get_loc(eql['timestamp'])
                    ax.axhline(y=eql['price'], xmin=idx/len(df), xmax=1, color=COLORS['EQL'], linestyle='--')
            
            # BOS/BMS
            if 'bos' in smc_structures:
                for bos in smc_structures['bos']:
                    idx = df.index.get_loc(bos['timestamp'])
                    marker = '^' if 'up' in bos['type'] else 'v'
                    ax.plot(idx, bos['price'], marker=marker, markersize=10, color=COLORS['BOS'])
            
            # SC
            if 'sc' in smc_structures:
                for sc in smc_structures['sc']:
                    idx = df.index.get_loc(sc['timestamp'])
                    ax.plot(idx, sc['price'], marker='*', markersize=12, color=COLORS['SC'])
            
            # Wicks
            if 'wick' in smc_structures:
                for wick in smc_structures['wick']:
                    idx = df.index.get_loc(wick['timestamp'])
                    ax.plot(idx, wick['price'], marker='d', markersize=8, color=COLORS['WICK'])
            
            # SFP
            if 'sfp' in smc_structures:
                for sfp in smc_structures['sfp']:
                    idx = df.index.get_loc(sfp['timestamp'])
                    ax.plot(idx, sfp['price'], marker='x', markersize=10, color=COLORS['SFP'])
            
            # POI
            if 'poi' in smc_structures:
                for poi in smc_structures['poi']:
                    idx = df.index.get_loc(poi['timestamp'])
                    price = (poi['price_high'] + poi['price_low']) / 2
                    ax.plot(idx, price, marker='o', markersize=12, color=COLORS['POI'], mfc='none')
            
            # Добавляем OTE зоны если есть
            if 'ote_zones' in smc_structures:
                for zone in smc_structures['ote_zones']:
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
            logger.error(f"Ошибка при построении графика с Matplotlib: {e}")
            return False
    
    def plot_backtest_results(self, backtest_result, save_path=None):
        """
        Визуализирует результаты бэктестинга
        
        Args:
            backtest_result (dict): Результаты бэктестинга
            save_path (str): Путь для сохранения графика
            
        Returns:
            bool: True если график построен, иначе False
        """
        if not backtest_result or not backtest_result.get('trades', []):
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
    
    def create_heatmap(self, df, title="Тепловая карта"):
        """
        Создает тепловую карту корреляций для DataFrame
        
        Args:
            df (pd.DataFrame): DataFrame с данными
            title (str): Заголовок графика
            
        Returns:
            matplotlib.figure.Figure: Объект фигуры
        """
        try:
            # Вычисляем корреляцию
            corr = df.corr()
            
            # Создаем тепловую карту
            fig, ax = plt.subplots(figsize=(10, 8))
            cax = ax.matshow(corr, cmap='coolwarm')
            plt.colorbar(cax)
            
            # Добавляем метки
            ticks = np.arange(0, len(df.columns), 1)
            ax.set_xticks(ticks)
            ax.set_yticks(ticks)
            ax.set_xticklabels(df.columns, rotation=90)
            ax.set_yticklabels(df.columns)
            
            plt.title(title)
            plt.tight_layout()
            
            return fig
            
        except Exception as e:
            logger.error(f"Ошибка при создании тепловой карты: {e}")
            return None