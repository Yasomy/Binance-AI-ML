import sys
import ccxt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QMainWindow, QTextEdit, QGraphicsView, QGraphicsScene
from PyQt5.QtCore import Qt

# Шаг 1: Получаем данные с Binance API
def fetch_binance_data(symbol='BTC/USDT', timeframe='1d', limit=100):
    exchange = ccxt.binance()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    
    # Преобразуем данные в DataFrame
    data = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
    
    return data

# Шаг 2: Расчет индикаторов

# 2.1: Расчет 50-дневной скользящей средней
def calculate_sma(data, window=50):
    data['SMA50'] = data['close'].rolling(window=window).mean()

# 2.2: Расчет RSI
def calculate_rsi(data, window=14):
    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    data['RSI'] = rsi

# Шаг 3: Генерация торговых сигналов
def generate_signal(data):
    # Проверка сигналов по RSI
    if data['RSI'].iloc[-1] < 30:
        signal = "Покупка: Актив перепродан, RSI ниже 30."
    elif data['RSI'].iloc[-1] > 70:
        signal = "Продажа: Актив перекуплен, RSI выше 70."
    else:
        signal = "Нет сигнала: Рынок в нейтральной зоне."
    
    # Проверка сигналов по скользящим средним (SMA)
    if data['close'].iloc[-1] > data['SMA50'].iloc[-1]:
        signal += "\nДополнительный сигнал: Цена выше SMA50 — потенциальный рост."
    else:
        signal += "\nДополнительный сигнал: Цена ниже SMA50 — потенциальное падение."
    
    return signal

# Шаг 4: Визуализация графика с Matplotlib в PyQt5 (отдельное окно для графика)
class PlotWindow(QMainWindow):
    def __init__(self, data, symbol='BTC/USDT'):
        super().__init__()

        self.setWindowTitle(f"График {symbol}")
        self.setGeometry(100, 100, 800, 600)

        # Создаем фигуру для графика с Matplotlib
        fig, ax = plt.subplots(figsize=(8, 5))
        
        # Строим график цен (close price)
        ax.plot(data['timestamp'], data['close'], label='Цена закрытия', color='blue', lw=2)

        # Добавляем скользящую среднюю
        ax.plot(data['timestamp'], data['SMA50'], label='50-дневная SMA', color='red', lw=2)

        # Заголовок и метки
        ax.set_title(f"График цен {symbol}")
        ax.set_xlabel("Дата")
        ax.set_ylabel("Цена (USDT)")
        ax.legend()

        # Вставляем график в PyQt5 с помощью FigureCanvas
        self.canvas = FigureCanvas(fig)
        self.setCentralWidget(self.canvas)

# Шаг 5: Визуализация текстового анализа в отдельном окне
class TextWindow(QMainWindow):
    def __init__(self, data, symbol='BTC/USDT'):
        super().__init__()

        self.setWindowTitle("Технический анализ")
        self.setGeometry(950, 100, 600, 400)

        # Добавляем виджет для текста
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.setCentralWidget(self.text_edit)

        # Генерация торгового сигнала
        signal = generate_signal(data)

        # Вставляем результаты анализа в текстовую область
        text = f"Рынок: {symbol}\n"
        text += f"Время последнего обновления: {data['timestamp'].iloc[-1]}\n"
        text += f"Цена закрытия последней свечи: {data['close'].iloc[-1]}\n\n"
        text += "Анализ:\n"
        text += signal

        # Вставляем текст в текстовое окно
        self.text_edit.setText(text)

# Шаг 6: Основная функция, которая запускает оба окна
def analyze_market(symbol='BTC/USDT', timeframe='1d', limit=100):
    # Создаем QApplication (это обязательный объект для работы с PyQt5)
    app = QApplication(sys.argv)

    # 1. Получаем данные с Binance
    data = fetch_binance_data(symbol, timeframe, limit)
    
    # 2. Расчет индикаторов
    calculate_sma(data)
    calculate_rsi(data)

    # Создаем окна
    plot_window = PlotWindow(data, symbol)
    text_window = TextWindow(data, symbol)

    # Показываем окна
    plot_window.show()
    text_window.show()

    # Запускаем главный цикл обработки событий
    sys.exit(app.exec_())

# Запуск анализа для BTC/USDT на интервале 1 день
analyze_market('BTC/USDT', '1d', 100)
