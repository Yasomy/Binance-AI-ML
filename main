import ccxt
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh


# Функция для получения данных с Kraken API
@st.cache_data(ttl=60)
def fetch_kraken_data(symbol='BTC/USD', timeframe='1m', days=1):
    try:
        exchange = ccxt.kraken()  # Используем Kraken API
        since = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)  # Данные за заданное количество дней
        until = int(datetime.now().timestamp() * 1000)  # Включить текущий момент
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since)

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

    # Bollinger Bands
    data['BB_Mid'] = data['close'].rolling(window=20).mean()
    data['BB_Upper'] = data['BB_Mid'] + 2 * data['close'].rolling(window=20).std()
    data['BB_Lower'] = data['BB_Mid'] - 2 * data['close'].rolling(window=20).std()

    # Stochastic Oscillator
    data['Stochastic_K'] = ((data['close'] - data['low'].rolling(window=14).min()) /
                            (data['high'].rolling(window=14).max() - data['low'].rolling(window=14).min())) * 100
    data['Stochastic_D'] = data['Stochastic_K'].rolling(window=3).mean()


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

    # Bollinger Bands
    bb_upper = data['BB_Upper'].iloc[-1]
    bb_lower = data['BB_Lower'].iloc[-1]
    close_price = data['close'].iloc[-1]
    if close_price > bb_upper:
        signals.append("Продажа: Цена выше верхней полосы Боллинджера (перекупленность).")
        details['Bollinger Bands'] = f"Цена = {close_price:.2f}, Верхняя полоса = {bb_upper:.2f} (перекупленность)"
    elif close_price < bb_lower:
        signals.append("Покупка: Цена ниже нижней полосы Боллинджера (перепроданность).")
        details['Bollinger Bands'] = f"Цена = {close_price:.2f}, Нижняя полоса = {bb_lower:.2f} (перепроданность)"
    else:
        details['Bollinger Bands'] = f"Цена = {close_price:.2f} (в пределах полос)"

    # Stochastic Oscillator
    stochastic_k = data['Stochastic_K'].iloc[-1]
    if stochastic_k > 80:
        signals.append("Продажа: Стохастик показывает перекупленность (>80).")
        details['Stochastic'] = f"%K = {stochastic_k:.2f} (перекупленность)"
    elif stochastic_k < 20:
        signals.append("Покупка: Стохастик показывает перепроданность (<20).")
        details['Stochastic'] = f"%K = {stochastic_k:.2f} (перепроданность)"
    else:
        details['Stochastic'] = f"%K = {stochastic_k:.2f} (нейтрально)"

    return signals, details


# Функции для отображения графиков индикаторов с использованием Plotly
def plot_price_chart(data):
    """
    Функция для построения графика свечей (OHLC).
    """
    fig = go.Figure()

    # Добавляем график свечей
    fig.add_trace(go.Candlestick(
        x=data['timestamp'],
        open=data['open'],
        high=data['high'],
        low=data['low'],
        close=data['close'],
        name="Цена"
    ))

    # Настройки осей
    fig.update_layout(
        title="График цен",
        xaxis_title="Время",
        yaxis_title="Цена",
        xaxis_rangeslider_visible=False,
        template="plotly_dark"
    )
    st.plotly_chart(fig)


def plot_sma_chart(data):
    st.write("#### SMA (50)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data['timestamp'], y=data['close'], mode='lines', name='Цена закрытия', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=data['timestamp'], y=data['SMA50'], mode='lines', name='SMA (50)', line=dict(color='red')))
    fig.update_layout(title="SMA 50", xaxis_title="Время", yaxis_title="Цена (USD)", template="plotly_dark")
    st.plotly_chart(fig)


def plot_bollinger_chart(data):
    st.write("#### Bollinger Bands")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data['timestamp'], y=data['close'], mode='lines', name='Цена закрытия', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=data['timestamp'], y=data['BB_Upper'], mode='lines', name='Верхняя полоса Боллинджера', line=dict(color='green', dash='dash')))
    fig.add_trace(go.Scatter(x=data['timestamp'], y=data['BB_Lower'], mode='lines', name='Нижняя полоса Боллинджера', line=dict(color='red', dash='dash')))
    fig.update_layout(title="Bollinger Bands", xaxis_title="Время", yaxis_title="Цена (USD)", template="plotly_dark")
    st.plotly_chart(fig)


def plot_stochastic_chart(data):
    st.write("#### Stochastic Oscillator")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data['timestamp'], y=data['Stochastic_K'], mode='lines', name='%K', line=dict(color='purple')))
    fig.add_trace(go.Scatter(x=data['timestamp'], y=data['Stochastic_D'], mode='lines', name='%D', line=dict(color='orange', dash='dash')))
    fig.update_layout(title="Stochastic Oscillator", xaxis_title="Время", yaxis_title="Стохастик", template="plotly_dark")
    st.plotly_chart(fig)


def plot_macd_chart(data):
    st.write("#### MACD")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data['timestamp'], y=data['MACD'], mode='lines', name='MACD', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=data['timestamp'], y=data['Signal Line'], mode='lines', name='Сигнальная линия', line=dict(color='red')))
    fig.update_layout(title="MACD", xaxis_title="Время", yaxis_title="MACD", template="plotly_dark")
    st.plotly_chart(fig)


# Главная функция для отображения всего анализа
def main():
    st.title("Криптовалютный анализ")

    # Боковая панель для управления параметрами
    st.sidebar.header("Настройки")

    # Выбор криптовалютной пары
    symbol = st.sidebar.selectbox(
        "Выберите пару",
        ['BTC/USD', 'ETH/USD', 'SOL/USD', 'ADA/USD', 'DOGE/USD']
    )

    # Выбор временного интервала
    timeframe = st.sidebar.selectbox(
        "Выберите временной интервал",
        ['1m', '5m', '15m', '1h', '1d']
    )

    # Выбор количества дней для загрузки данных
    days = st.sidebar.slider(
        "Количество дней для загрузки данных",
        min_value=1, max_value=30, value=1
    )

    # Выбор отображаемых индикаторов
    show_sma = st.sidebar.checkbox("Показать SMA", value=True)
    show_bollinger = st.sidebar.checkbox("Показать Bollinger Bands", value=True)
    show_stochastic = st.sidebar.checkbox("Показать Stochastic", value=True)
    show_macd = st.sidebar.checkbox("Показать MACD", value=True)

    # Интервал автообновления
    refresh_interval = st.sidebar.number_input(
        "Интервал автообновления (в секундах)",
        min_value=10, max_value=3600, value=60
    )
    st_autorefresh(interval=refresh_interval * 1000, limit=None, key="auto_refresh")

    # Заголовок выбранной пары
    st.subheader(f"Анализ пары: {symbol}")

    # Получение данных
    with st.spinner("Загружаются данные..."):
        data = fetch_kraken_data(symbol, timeframe, days)

    if data is not None:
        calculate_indicators(data)

        # Общий график цен
        plot_price_chart(data)

        # Разделить экран на 4 части для индикаторов
        st.write("### Индикаторы")
        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)

        # Графики индикаторов
        with col1:
            if show_sma:
                plot_sma_chart(data)

        with col2:
            if show_bollinger:
                plot_bollinger_chart(data)

        with col3:
            if show_stochastic:
                plot_stochastic_chart(data)

        with col4:
            if show_macd:
                plot_macd_chart(data)

        # Текущая информация
        st.write("### Текущая информация")
        st.write(f"Последнее обновление: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"Цена закрытия: {data['close'].iloc[-1]:.2f} USD")

        # Торговые сигналы
        signals, details = generate_signals(data)
        st.write("### Торговые сигналы")
        for signal in signals:
            st.write(f"- {signal}")

        # Детали индикаторов
        st.write("### Детали индикаторов")
        for key, value in details.items():
            st.write(f"- {key}: {value}")


if __name__ == "__main__":
    main()
