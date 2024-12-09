import sys
import ccxt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QComboBox, QPushButton
from PyQt5.QtCore import QTimer
from datetime import datetime, timedelta

# Шаг 1: Получаем данные с Coinbase API
def fetch_coinbase_data(symbol='BTC-USD', timeframe='1m', limit=1440):  # 1440 минут = 24 часа
    exchange = ccxt.coinbase()  # Используем Coinbase API

    # Получаем данные за последние 24 часа
    since = int((datetime.now() - timedelta(days=1)).timestamp() * 1000)  # 24 часа назад
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)

    # Преобразуем данные в DataFrame
    data = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')  # Преобразуем в datetime
    return data

# Шаг 2: Расчет индикаторов
def calculate_sma(data, window=50):
    data['SMA50'] = data['close'].rolling(window=window).mean()

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
    signal = ""
    
    if data['RSI'].iloc[-1] < 30:
        signal += "Покупка: Актив перепродан, RSI ниже 30.\n"
    elif data['RSI'].iloc[-1] > 70:
        signal += "Продажа: Актив перекуплен, RSI выше 70.\n"
    else:
        signal += "RSI: Рынок в нейтральной зоне.\n"
    
    if data['close'].iloc[-1] > data['SMA50'].iloc[-1]:
        signal += "Дополнительный сигнал: Цена выше SMA50 — потенциальный рост.\n"
    elif data['close'].iloc[-1] < data['SMA50'].iloc[-1]:
        signal += "Дополнительный сигнал: Цена ниже SMA50 — потенциальное падение.\n"
    
    if data['close'].iloc[-2] < data['SMA50'].iloc[-2] and data['close'].iloc[-1] > data['SMA50'].iloc[-1]:
        signal += "Пересечение: Цена пересекла 50-дневную SMA снизу вверх — возможный сигнал на покупку.\n"
    elif data['close'].iloc[-2] > data['SMA50'].iloc[-2] and data['close'].iloc[-1] < data['SMA50'].iloc[-1]:
        signal += "Пересечение: Цена пересекла 50-дневную SMA сверху вниз — возможный сигнал на продажу.\n"
    
    if signal == "":
        signal = "Нет сигнала: Рынок в нейтральной зоне."
    
    return signal

# Шаг 4: Визуализация графика с Matplotlib в PyQt5
class PlotWindow(QMainWindow):
    def __init__(self, data, symbol='BTC-USD'):
        super().__init__()

        self.setWindowTitle(f"График {symbol}")
        self.setGeometry(100, 100, 800, 600)

        self.symbol = symbol

        # Создаем фигуру для графика с Matplotlib
        self.fig, self.ax = plt.subplots(figsize=(8, 5))

        # Строим график цен (close price)
        self.line_close, = self.ax.plot(data['timestamp'], data['close'], label='Цена закрытия', color='blue', lw=2)

        # Добавляем скользящую среднюю
        self.line_sma, = self.ax.plot(data['timestamp'], data['SMA50'], label='50-дневная SMA', color='red', lw=2)

        # Заголовок и метки
        self.ax.set_title(f"График цен {symbol}")
        self.ax.set_xlabel("Дата")
        self.ax.set_ylabel("Цена (USD)")
        self.ax.legend()

        # Вставляем график в PyQt5 с помощью FigureCanvas
        self.canvas = FigureCanvas(self.fig)
        self.setCentralWidget(self.canvas)

        # Таймер для обновления графика каждую минуту
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_graph)
        self.timer.start(60000)  # Обновление каждую минуту

    def refresh_graph(self):
        """Обновляем график каждую минуту"""
        data = fetch_coinbase_data(self.symbol)
        calculate_sma(data)
        calculate_rsi(data)

        # Обновляем данные на графике
        self.line_close.set_data(data['timestamp'], data['close'])
        self.line_sma.set_data(data['timestamp'], data['SMA50'])

        # Обновляем оси
        self.ax.relim()
        self.ax.autoscale_view()

        # Перерисовываем график
        self.canvas.draw()

# Шаг 5: Визуализация текстового анализа в отдельном окне
class TextWindow(QMainWindow):
    def __init__(self, data, symbol='BTC-USD'):
        super().__init__()

        self.setWindowTitle("Технический анализ")
        self.setGeometry(950, 100, 600, 400)

        # Добавляем виджет для текста
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.setCentralWidget(self.text_edit)

        self.symbol = symbol
        self.update_text(data)

        # Создаем таймер для обновления текста каждую минуту
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(60000)  # обновление каждую минуту

    def update_text(self, data):
        signal = generate_signal(data)

        # Используем текущее время для отображения времени последнего обновления
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        text = f"Рынок: {self.symbol}\n"
        text += f"Время последнего обновления: {current_time}\n"
        text += f"Цена закрытия последней свечи: {data['close'].iloc[-1]}\n\n"
        text += "Анализ:\n"
        text += signal

        # Вставляем текст в текстовое окно
        self.text_edit.setText(text)

    def refresh_data(self):
        """Обновляем данные и текстовое окно"""
        data = fetch_coinbase_data(self.symbol)
        calculate_sma(data)
        calculate_rsi(data)
        self.update_text(data)

# Шаг 6: Главный интерфейс
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Криптовалютный анализ")
        self.setGeometry(100, 100, 400, 200)

        # Определяем только BTC-USD
        self.selected_crypto = 'BTC'
        self.selected_currency = 'USD'

        # Комбо-боксы для выбора валюты (оставляем только USD)
        self.combo_currency = QComboBox(self)
        self.combo_currency.addItems(['USD'])
        self.combo_currency.setGeometry(50, 100, 300, 30)

        # Кнопка для запуска анализа
        self.button = QPushButton("Запустить анализ", self)
        self.button.setGeometry(50, 150, 300, 30)
        self.button.clicked.connect(self.run_analysis)

    def run_analysis(self):
        """Запускаем анализ для выбранной валютной пары"""
        symbol = f"{self.selected_crypto}-{self.selected_currency}"
        data = fetch_coinbase_data(symbol)
        calculate_sma(data)
        calculate_rsi(data)

        # Создаем окна с графиком и анализом
        self.plot_window = PlotWindow(data, symbol)
        self.text_window = TextWindow(data, symbol)

        self.plot_window.show()
        self.text_window.show()

# Шаг 7: Основная функция
def analyze_market():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())  # Запуск приложения

# Запуск приложения
analyze_market()
