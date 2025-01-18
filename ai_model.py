import numpy as np
from sklearn.linear_model import LinearRegression

# Функция подготовки данных для модели
def prepare_training_data(data, window=60):
    """
    Подготавливает данные для обучения модели.
    data: DataFrame с историей цен.
    window: размер окна временного ряда (в минутах).
    """
    X, y = [], []
    for i in range(len(data) - window):
        X.append(data['close'].iloc[i:i + window].values)
        y.append(data['close'].iloc[i + window])
    return np.array(X), np.array(y)

# Функция для предсказания цены
def predict_price(data, window=60):
    """
    Выполняет прогноз цены на следующую минуту на основе последних данных.
    data: DataFrame с историей цен.
    window: размер окна временного ряда.
    """
    if len(data) < window:
        raise ValueError("Недостаточно данных для предсказания.")

    # Подготовка данных для обучения
    X, y = prepare_training_data(data, window)

    # Создаем и обучаем модель
    model = LinearRegression()
    model.fit(X, y)

    # Прогноз на следующую минуту
    last_window = data['close'].iloc[-window:].values.reshape(1, -1)
    predicted_price = model.predict(last_window)[0]

    # Определение направления изменения цены
    current_price = data['close'].iloc[-1]
    direction = "рост" if predicted_price > current_price else "падение"

    return predicted_price, direction
