import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from ta.volume import VolumeWeightedAveragePrice
from config import RSI_PERIOD, RSI_OVERBOUGHT, RSI_OVERSOLD, PREMIUM_ZONE, DISCOUNT_ZONE, EQUILIBRIUM_LEVEL

class TechnicalAnalysis:
    def __init__(self, df):
        """
        Инициализирует объект для технического анализа
        
        Args:
            df (pd.DataFrame): DataFrame с OHLCV данными
        """
        self.df = df.copy()
        # Добавляем технические индикаторы
        self._add_indicators()
    
    def _add_indicators(self):
        """Добавляет технические индикаторы в DataFrame"""
        # RSI
        rsi = RSIIndicator(close=self.df['close'], window=RSI_PERIOD)
        self.df['rsi'] = rsi.rsi()
        
        # EMA
        ema20 = EMAIndicator(close=self.df['close'], window=20)
        ema50 = EMAIndicator(close=self.df['close'], window=50)
        ema200 = EMAIndicator(close=self.df['close'], window=200)
        
        self.df['ema20'] = ema20.ema_indicator()
        self.df['ema50'] = ema50.ema_indicator()
        self.df['ema200'] = ema200.ema_indicator()
        
        # Добавляем процентное изменение
        self.df['change_pct'] = self.df['close'].pct_change() * 100
        
        # Добавляем свечные диапазоны
        self.df['body_size'] = abs(self.df['close'] - self.df['open'])
        self.df['upper_wick'] = self.df['high'] - self.df[['open', 'close']].max(axis=1)
        self.df['lower_wick'] = self.df[['open', 'close']].min(axis=1) - self.df['low']
        self.df['candle_range'] = self.df['high'] - self.df['low']
        
        # Индикаторы для определения тренда
        self.df['trend'] = np.where(self.df['ema20'] > self.df['ema50'], 1, 
                            np.where(self.df['ema20'] < self.df['ema50'], -1, 0))

class SmartMoneyAnalysis:
    def __init__(self, df):
        """
        Инициализирует объект для анализа по концепции Smart Money
        
        Args:
            df (pd.DataFrame): DataFrame с OHLCV данными и техническими индикаторами
        """
        self.df = df.copy()
        # Создаем копию для идентификации структур
        self.structures_df = self.df.copy()
        
        # Инициализируем структуры для анализа
        self.structures = {
            'swing_highs': [],
            'swing_lows': [],
            'ob_buy': [],  # Order Blocks (покупки)
            'ob_sell': [],  # Order Blocks (продажи)
            'eqh': [],  # Equal Highs
            'eql': [],  # Equal Lows
            'bos': [],  # Break of Structure
            'bms': [],  # Break of Market Structure
            'sc': [],  # Sponsored Candles
            'wick': [],  # Wicks
            'sfp': [],  # Swing Failure Pattern
            'poi': []   # Points of Interest
        }
        
        # Находим структурные точки
        self._find_structures()
    
    def _find_structures(self):
        """Находит все структуры для Smart Money анализа"""
        self._find_swing_points()
        self._find_equal_levels()
        self._find_bos_bms()
        self._find_order_blocks()
        self._find_sponsored_candles()
        self._find_wicks()
        self._find_sfp()
        self._find_poi()
    
    def _find_swing_points(self, window=5):
        """
        Находит точки разворота (swing highs и swing lows)
        
        Args:
            window (int): Размер окна для определения точек разворота
        """
        # Находим swing highs
        for i in range(window, len(self.df) - window):
            if all(self.df['high'].iloc[i] > self.df['high'].iloc[i-j] for j in range(1, window+1)) and \
               all(self.df['high'].iloc[i] > self.df['high'].iloc[i+j] for j in range(1, window+1)):
                self.structures['swing_highs'].append({
                    'index': i,
                    'timestamp': self.df.index[i],
                    'price': self.df['high'].iloc[i],
                    'type': 'swing_high'
                })
        
        # Находим swing lows
        for i in range(window, len(self.df) - window):
            if all(self.df['low'].iloc[i] < self.df['low'].iloc[i-j] for j in range(1, window+1)) and \
               all(self.df['low'].iloc[i] < self.df['low'].iloc[i+j] for j in range(1, window+1)):
                self.structures['swing_lows'].append({
                    'index': i,
                    'timestamp': self.df.index[i],
                    'price': self.df['low'].iloc[i],
                    'type': 'swing_low'
                })

    def _find_equal_levels(self, tolerance=0.001):
        """
        Находит равные уровни (EQH и EQL)
        
        Args:
            tolerance (float): Допустимая погрешность для определения равных уровней
        """
        # Находим Equal Highs (EQH)
        for i in range(1, len(self.structures['swing_highs'])):
            current = self.structures['swing_highs'][i]['price']
            previous = self.structures['swing_highs'][i-1]['price']
            
            if abs(current - previous) / previous < tolerance:
                self.structures['eqh'].append({
                    'index': self.structures['swing_highs'][i]['index'],
                    'timestamp': self.structures['swing_highs'][i]['timestamp'],
                    'price': current,
                    'type': 'eqh'
                })
        
        # Находим Equal Lows (EQL)
        for i in range(1, len(self.structures['swing_lows'])):
            current = self.structures['swing_lows'][i]['price']
            previous = self.structures['swing_lows'][i-1]['price']
            
            if abs(current - previous) / previous < tolerance:
                self.structures['eql'].append({
                    'index': self.structures['swing_lows'][i]['index'],
                    'timestamp': self.structures['swing_lows'][i]['timestamp'],
                    'price': current,
                    'type': 'eql'
                })

    def _find_bos_bms(self):
        """Находит Break of Structure (BOS) и Break of Market Structure (BMS)"""
        # Проходим по swing highs и ищем пробои структуры вниз
        for i in range(1, len(self.structures['swing_highs'])):
            current_high = self.structures['swing_highs'][i]['price']
            previous_high = self.structures['swing_highs'][i-1]['price']
            
            if current_high < previous_high:
                # Ищем подтверждение BMS
                for j in range(self.structures['swing_highs'][i]['index'] + 1, len(self.df)):
                    if self.df['high'].iloc[j] < self.structures['swing_highs'][i]['price']:
                        self.structures['bos'].append({
                            'index': j,
                            'timestamp': self.df.index[j],
                            'price': self.df['high'].iloc[j],
                            'type': 'bos_down'
                        })
                        break
        
        # Проходим по swing lows и ищем пробои структуры вверх
        for i in range(1, len(self.structures['swing_lows'])):
            current_low = self.structures['swing_lows'][i]['price']
            previous_low = self.structures['swing_lows'][i-1]['price']
            
            if current_low > previous_low:
                # Ищем подтверждение BMS
                for j in range(self.structures['swing_lows'][i]['index'] + 1, len(self.df)):
                    if self.df['low'].iloc[j] > self.structures['swing_lows'][i]['price']:
                        self.structures['bos'].append({
                            'index': j,
                            'timestamp': self.df.index[j],
                            'price': self.df['low'].iloc[j],
                            'type': 'bos_up'
                        })
                        break

    def _find_order_blocks(self, num_candles=5):
        """
        Находит Order Blocks (OB)
        
        Args:
            num_candles (int): Количество свечей для анализа перед импульсным движением
        """
        # Проходим по DataFrame и ищем импульсные движения
        for i in range(num_candles, len(self.df)-1):
            # Находим бычьи OB (сильное движение вверх после)
            if self.df['close'].iloc[i+1] > self.df['open'].iloc[i+1] and \
               (self.df['close'].iloc[i+1] - self.df['open'].iloc[i+1]) / self.df['open'].iloc[i+1] > 0.01:
                # Ищем свечу продавца перед импульсом
                for j in range(i, i-num_candles, -1):
                    if self.df['close'].iloc[j] < self.df['open'].iloc[j]:  # Медвежья свеча
                        self.structures['ob_buy'].append({
                            'index': j,
                            'timestamp': self.df.index[j],
                            'price_high': self.df['high'].iloc[j],
                            'price_low': self.df['low'].iloc[j],
                            'type': 'ob_buy'
                        })
                        break
            
            # Находим медвежьи OB (сильное движение вниз после)
            if self.df['close'].iloc[i+1] < self.df['open'].iloc[i+1] and \
               (self.df['open'].iloc[i+1] - self.df['close'].iloc[i+1]) / self.df['open'].iloc[i+1] > 0.01:
                # Ищем свечу покупателя перед импульсом
                for j in range(i, i-num_candles, -1):
                    if self.df['close'].iloc[j] > self.df['open'].iloc[j]:  # Бычья свеча
                        self.structures['ob_sell'].append({
                            'index': j,
                            'timestamp': self.df.index[j],
                            'price_high': self.df['high'].iloc[j],
                            'price_low': self.df['low'].iloc[j],
                            'type': 'ob_sell'
                        })
                        break

    def _find_sponsored_candles(self, threshold=1.5):
        """
        Находит Sponsored Candles (SC)
        
        Args:
            threshold (float): Пороговое значение для определения спонсированных свечей
        """
        # Вычисляем средний размер свечи
        avg_range = self.df['candle_range'].mean()
        
        for i in range(1, len(self.df)-1):
            # Проверяем большой размер свечи
            if self.df['candle_range'].iloc[i] > avg_range * threshold:
                # Бычья спонсированная свеча
                if self.df['close'].iloc[i] > self.df['open'].iloc[i] and \
                   self.df['close'].iloc[i+1] > self.df['high'].iloc[i]:
                    self.structures['sc'].append({
                        'index': i,
                        'timestamp': self.df.index[i],
                        'price': self.df['high'].iloc[i],
                        'type': 'sc_up'
                    })
                
                # Медвежья спонсированная свеча
                elif self.df['close'].iloc[i] < self.df['open'].iloc[i] and \
                     self.df['close'].iloc[i+1] < self.df['low'].iloc[i]:
                    self.structures['sc'].append({
                        'index': i,
                        'timestamp': self.df.index[i],
                        'price': self.df['low'].iloc[i],
                        'type': 'sc_down'
                    })

    def _find_wicks(self, threshold=1.5):
        """
        Находит значимые фитили (Wicks)
        
        Args:
            threshold (float): Пороговое значение для определения значимых фитилей
        """
        # Вычисляем средние размеры фитилей
        avg_upper_wick = self.df['upper_wick'].mean()
        avg_lower_wick = self.df['lower_wick'].mean()
        
        for i in range(len(self.df)):
            # Длинный верхний фитиль
            if self.df['upper_wick'].iloc[i] > avg_upper_wick * threshold:
                self.structures['wick'].append({
                    'index': i,
                    'timestamp': self.df.index[i],
                    'price': self.df['high'].iloc[i],
                    'type': 'wick_up'
                })
            
            # Длинный нижний фитиль
            if self.df['lower_wick'].iloc[i] > avg_lower_wick * threshold:
                self.structures['wick'].append({
                    'index': i,
                    'timestamp': self.df.index[i],
                    'price': self.df['low'].iloc[i],
                    'type': 'wick_down'
                })

    def _find_sfp(self):
        """Находит Swing Failure Pattern (SFP)"""
        # SFP на вершинах (пробой swing high с последующим возвратом)
        for i in range(len(self.structures['swing_highs'])-1):
            high_idx = self.structures['swing_highs'][i]['index']
            high_price = self.structures['swing_highs'][i]['price']
            
            # Ищем пробой уровня с последующим возвратом
            for j in range(high_idx+1, min(high_idx+10, len(self.df))):
                if self.df['high'].iloc[j] > high_price and self.df['close'].iloc[j] < high_price:
                    self.structures['sfp'].append({
                        'index': j,
                        'timestamp': self.df.index[j],
                        'price': self.df['high'].iloc[j],
                        'type': 'sfp_top'
                    })
                    break
        
        # SFP на впадинах (пробой swing low с последующим возвратом)
        for i in range(len(self.structures['swing_lows'])-1):
            low_idx = self.structures['swing_lows'][i]['index']
            low_price = self.structures['swing_lows'][i]['price']
            
            # Ищем пробой уровня с последующим возвратом
            for j in range(low_idx+1, min(low_idx+10, len(self.df))):
                if self.df['low'].iloc[j] < low_price and self.df['close'].iloc[j] > low_price:
                    self.structures['sfp'].append({
                        'index': j,
                        'timestamp': self.df.index[j],
                        'price': self.df['low'].iloc[j],
                        'type': 'sfp_bottom'
                    })
                    break

    def _find_poi(self):
        """Находит Points of Interest (POI) - зоны, где пересекаются несколько структур"""
        # Все индексы с структурами
        all_structures = []
        for struct_type in self.structures:
            if struct_type != 'poi':  # Исключаем сами POI
                for structure in self.structures[struct_type]:
                    if 'index' in structure:
                        all_structures.append({
                            'index': structure['index'],
                            'type': structure['type']
                        })
        
        # Индексы со скоплением структур
        poi_indices = {}
        for structure in all_structures:
            idx = structure['index']
            if idx in poi_indices:
                poi_indices[idx].append(structure['type'])
            else:
                poi_indices[idx] = [structure['type']]
        
        # Точки с несколькими структурами считаем POI
        for idx, types in poi_indices.items():
            if len(types) >= 2:  # Минимум две структуры
                self.structures['poi'].append({
                    'index': idx,
                    'timestamp': self.df.index[idx],
                    'price_high': self.df['high'].iloc[idx],
                    'price_low': self.df['low'].iloc[idx],
                    'structures': types,
                    'type': 'poi'
                })
    
    def find_optimal_trade_entry(self):
        """
        Находит Optimal Trade Entry (OTE) зоны на основе анализа структур
        
        Returns:
            list: Список оптимальных зон для входа в сделку
        """
        ote_zones = []
        
        # Анализируем POI
        for poi in self.structures['poi']:
            # Если в POI содержатся ключевые структуры
            key_structures = set(['ob_buy', 'ob_sell', 'eqh', 'eql', 'sfp_top', 'sfp_bottom', 'wick_up', 'wick_down'])
            
            if any(s in key_structures for s in poi['structures']):
                # Анализируем текущий тренд
                current_idx = poi['index']
                current_trend = self.df['trend'].iloc[current_idx]
                
                # Находим Fibonacci уровни
                if current_trend > 0:  # Восходящий тренд
                    # Ищем предыдущий swing low
                    prev_swing_lows = [sl for sl in self.structures['swing_lows'] if sl['index'] < current_idx]
                    
                    if prev_swing_lows:
                        last_swing_low = prev_swing_lows[-1]
                        swing_range = poi['price_high'] - last_swing_low['price']
                        
                        # Зона 0.5-0.618 (Premium)
                        premium_zone = {
                            'timestamp': poi['timestamp'],
                            'price_low': poi['price_high'] - swing_range * PREMIUM_ZONE,
                            'price_high': poi['price_high'] - swing_range * EQUILIBRIUM_LEVEL,
                            'type': 'ote_buy_premium'
                        }
                        
                        ote_zones.append(premium_zone)
                
                else:  # Нисходящий тренд
                    # Ищем предыдущий swing high
                    prev_swing_highs = [sh for sh in self.structures['swing_highs'] if sh['index'] < current_idx]
                    
                    if prev_swing_highs:
                        last_swing_high = prev_swing_highs[-1]
                        swing_range = last_swing_high['price'] - poi['price_low']
                        
                        # Зона 0.5-0.618 (Discount)
                        discount_zone = {
                            'timestamp': poi['timestamp'],
                            'price_low': poi['price_low'] + swing_range * EQUILIBRIUM_LEVEL,
                            'price_high': poi['price_low'] + swing_range * DISCOUNT_ZONE,
                            'type': 'ote_sell_discount'
                        }
                        
                        ote_zones.append(discount_zone)
        
        return ote_zones
    
    def find_trade_setups(self):
        """
        Находит потенциальные торговые сетапы на основе анализа структур
        
        Returns:
            list: Список потенциальных торговых сетапов
        """
        setups = []
        
        # Находим OTE зоны
        ote_zones = self.find_optimal_trade_entry()
        
        # Находим BOS/BMS
        for bos in self.structures['bos']:
            # Для покупки (BOS вверх)
            if bos['type'] == 'bos_up':
                # Проверяем наличие OTE зон рядом
                for ote in ote_zones:
                    if 'ote_buy' in ote['type'] and bos['index'] - 5 <= ote['timestamp'] <= bos['index'] + 5:
                        # Проверяем наличие OB, SC или WICK рядом
                        has_ob = any(ob['index'] - 3 <= bos['index'] <= ob['index'] + 3 for ob in self.structures['ob_buy'])
                        has_sc = any(sc['index'] - 3 <= bos['index'] <= sc['index'] + 3 for sc in self.structures['sc'] if sc['type'] == 'sc_up')
                        has_wick = any(w['index'] - 3 <= bos['index'] <= w['index'] + 3 for w in self.structures['wick'] if w['type'] == 'wick_down')
                        
                        if has_ob or has_sc or has_wick:
                            setups.append({
                                'timestamp': bos['timestamp'],
                                'price': bos['price'],
                                'type': 'buy_setup',
                                'desc': 'BOS вверх с подтверждением OTE и дополнительными структурами'
                            })
            
            # Для продажи (BOS вниз)
            elif bos['type'] == 'bos_down':
                # Проверяем наличие OTE зон рядом
                for ote in ote_zones:
                    if 'ote_sell' in ote['type'] and bos['index'] - 5 <= ote['timestamp'] <= bos['index'] + 5:
                        # Проверяем наличие OB, SC или WICK рядом
                        has_ob = any(ob['index'] - 3 <= bos['index'] <= ob['index'] + 3 for ob in self.structures['ob_sell'])
                        has_sc = any(sc['index'] - 3 <= bos['index'] <= sc['index'] + 3 for sc in self.structures['sc'] if sc['type'] == 'sc_down')
                        has_wick = any(w['index'] - 3 <= bos['index'] <= w['index'] + 3 for w in self.structures['wick'] if w['type'] == 'wick_up')
                        
                        if has_ob or has_sc or has_wick:
                            setups.append({
                                'timestamp': bos['timestamp'],
                                'price': bos['price'],
                                'type': 'sell_setup',
                                'desc': 'BOS вниз с подтверждением OTE и дополнительными структурами'
                            })
        
        # Находим SFP сетапы
        for sfp in self.structures['sfp']:
            # SFP на вершине (для продажи)
            if sfp['type'] == 'sfp_top':
                setups.append({
                    'timestamp': sfp['timestamp'],
                    'price': sfp['price'],
                    'type': 'sell_setup',
                    'desc': 'SFP на вершине - ложный пробой максимума'
                })
            
            # SFP на дне (для покупки)
            elif sfp['type'] == 'sfp_bottom':
                setups.append({
                    'timestamp': sfp['timestamp'],
                    'price': sfp['price'],
                    'type': 'buy_setup',
                    'desc': 'SFP на дне - ложный пробой минимума'
                })
        
        return setups
    
    def get_current_market_context(self):
        """
        Получает текущий контекст рынка на основе анализа структур
        
        Returns:
            dict: Текущий контекст рынка
        """
        # Берем последнюю свечу
        last_idx = len(self.df) - 1
        last_timestamp = self.df.index[-1]
        last_close = self.df['close'].iloc[-1]
        
        # Определяем текущий тренд
        current_trend = self.df['trend'].iloc[-1]
        trend_desc = "Восходящий" if current_trend > 0 else "Нисходящий" if current_trend < 0 else "Боковой"
        
        # Определяем ближайшие структуры
        nearby_structures = []
        
        # Проходим по всем структурам и ищем ближайшие
        for struct_type, structures in self.structures.items():
            if struct_type not in ['swing_highs', 'swing_lows']:  # Исключаем базовые структуры
                for struct in structures:
                    if 'index' in struct and last_idx - 10 <= struct['index'] <= last_idx:
                        nearby_structures.append({
                            'type': struct['type'],
                            'timestamp': struct['timestamp'],
                            'price': struct['price'] if 'price' in struct else (struct['price_high'] + struct['price_low']) / 2 if 'price_high' in struct and 'price_low' in struct else None
                        })
        
        # Находим ближайшие уровни поддержки и сопротивления
        support_levels = []
        resistance_levels = []
        
        # Swing lows как поддержка
        for sl in self.structures['swing_lows']:
            if sl['price'] < last_close:
                support_levels.append(sl['price'])
        
        # Swing highs как сопротивление
        for sh in self.structures['swing_highs']:
            if sh['price'] > last_close:
                resistance_levels.append(sh['price'])
        
        # Order blocks как поддержка/сопротивление
        for ob in self.structures['ob_buy']:
            level = (ob['price_high'] + ob['price_low']) / 2
            if level < last_close:
                support_levels.append(level)
        
        for ob in self.structures['ob_sell']:
            level = (ob['price_high'] + ob['price_low']) / 2
            if level > last_close:
                resistance_levels.append(level)
        
        # Находим ближайшие
        if support_levels:
            nearest_support = max(support_levels)
        else:
            nearest_support = None
        
        if resistance_levels:
            nearest_resistance = min(resistance_levels)
        else:
            nearest_resistance = None
        
        # Формируем контекст
        context = {
            'timestamp': last_timestamp,
            'close': last_close,
            'trend': trend_desc,
            'nearby_structures': nearby_structures,
            'nearest_support': nearest_support,
            'nearest_resistance': nearest_resistance,
            'rsi': self.df['rsi'].iloc[-1],
            'is_overbought': self.df['rsi'].iloc[-1] > RSI_OVERBOUGHT,
            'is_oversold': self.df['rsi'].iloc[-1] < RSI_OVERSOLD
        }
        
        return context