import ccxt
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh


# Функция для получения данных с Coinbase API
def fetch_coinbase_data(symbol='BTC-USD', timeframe='1m', limit=180):
    try:
        exchange = ccxt.coinbase()  # Используем Coinbase API
        since = int((datetime.now() - timedelta(days=1)).timestamp() * 1000)  # Данные за последние 24 часа
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)

        # Преобразуем данные в DataFrame
        data = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
        return data
    except Exception as e:
        st.error(f"Ошибка при запросе данных: {e}")
        return None


# Функция для расчета индикаторов
def calculate_indicators(data):
    # Скользящая средняя (SMA)
    data['SMA50'] = data['close'].rolling(window=50).mean()

    # RSI
    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    data['RSI'] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = data['close'].ewm(span=12, adjust=False).mean()
    ema26 = data['close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = ema12 - ema26
    data['Signal Line'] = data['MACD'].ewm(span=9, adjust=False).mean()

    # Прогноз на основе простого линейного тренда
    if len(data) >= 10:
        data['Trend'] = data['close'].rolling(window=10).mean()


# Генерация всех торговых сигналов
def generate_signals(data):
    signals = []
    details = {}

    # RSI
    rsi_value = data['RSI'].iloc[-1]
    if rsi_value < 30:
        signals.append("Покупка: Актив перепродан, RSI ниже 30.")
        details['RSI'] = f"RSI = {rsi_value:.2f} (перепродан)"
    elif rsi_value > 70:
        signals.append("Продажа: Актив перекуплен, RSI выше 70.")
        details['RSI'] = f"RSI = {rsi_value:.2f} (перекуплен)"
    else:
        details['RSI'] = f"RSI = {rsi_value:.2f} (нейтрально)"

    # MACD
    macd_value = data['MACD'].iloc[-1]
    signal_line = data['Signal Line'].iloc[-1]
    if macd_value > signal_line:
        signals.append("Покупка: MACD пересек сигнальную линию снизу вверх.")
        details['MACD'] = f"MACD = {macd_value:.2f}, Сигнальная линия = {signal_line:.2f} (бычий сигнал)"
    elif macd_value < signal_line:
        signals.append("Продажа: MACD пересек сигнальную линию сверху вниз.")
        details['MACD'] = f"MACD = {macd_value:.2f}, Сигнальная линия = {signal_line:.2f} (медвежий сигнал)"
    else:
        details['MACD'] = f"MACD = {macd_value:.2f}, Сигнальная линия = {signal_line:.2f} (нейтрально)"

    # Trend
    if 'Trend' in data.columns:
        trend_value = data['Trend'].iloc[-1]
        close_price = data['close'].iloc[-1]
        if close_price > trend_value:
            signals.append("Покупка: Цена выше прогноза тренда.")
            details['Trend'] = f"Цена = {close_price:.2f}, Тренд = {trend_value:.2f} (бычий сигнал)"
        else:
            signals.append("Продажа: Цена ниже прогноза тренда.")
            details['Trend'] = f"Цена = {close_price:.2f}, Тренд = {trend_value:.2f} (медвежий сигнал)"

    if not signals:
        signals.append("Рынок в нейтральной зоне.")

    return signals, details


# Streamlit приложение
def main():
    st.set_page_config(page_title="Криптовалютный анализ", layout="wide")

    # Заголовок
    st.title("Криптовалютный анализ")
    st.subheader("BTC-USD")

    # Автообновление через таймер
    refresh_interval = st.number_input("Интервал автообновления (в секундах)", min_value=10, max_value=3600, value=60)
    st_autorefresh(interval=refresh_interval * 1000, limit=None, key="auto_refresh")

    # Получение данных
    with st.spinner("Загружаются данные..."):
        data = fetch_coinbase_data()

    if data is not None:
        calculate_indicators(data)

        # Выбор отображения индикаторов
        show_sma = st.checkbox("Показать SMA (50)", value=True)
        show_macd = st.checkbox("Показать MACD", value=True)
        show_trend = st.checkbox("Показать прогноз тренда", value=True)

        # Отображение графика
        st.write("### График цен за последние 24 часа")
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(data['timestamp'], data['close'], label='Цена закрытия', color='blue')

        if show_sma:
            ax.plot(data['timestamp'], data['SMA50'], label='50-дневная SMA', color='red')

        if show_trend and 'Trend' in data.columns:
            ax.plot(data['timestamp'], data['Trend'], label='Прогноз цены (тренд)', color='green', linestyle='--')

        if show_macd:
            ax2 = ax.twinx()
            ax2.plot(data['timestamp'], data['MACD'], label='MACD', color='purple')
            ax2.plot(data['timestamp'], data['Signal Line'], label='Сигнальная линия MACD', color='orange')
            ax2.set_ylabel("MACD")

        # Легенда и метки
        ax.set_xlabel("Время")
        ax.set_ylabel("Цена (USD)")
        ax.legend(loc='upper left')
        if show_macd:
            ax2.legend(loc='upper right')
        st.pyplot(fig)

        # Текущая информация
        st.write("### Текущая информация")
        st.write(f"Последнее обновление: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"Цена закрытия: {data['close'].iloc[-1]:.2f} USD")

        # Торговые сигналы
        st.write("### Торговые сигналы")
        signals, details = generate_signals(data)
        for signal in signals:
            st.write(f"- {signal}")

        # Дополнительная информация
        st.write("### Детали индикаторов")
        for key, value in details.items():
            st.write(f"- {key}: {value}")


if __name__ == "__main__":
    main()
