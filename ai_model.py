import numpy as np
from sklearn.linear_model import LinearRegression


def predict_price(data):

    if len(data) < 720:
        raise ValueError("Недостаточно данных для предсказания.")


    recent_data = data.tail(720)


    recent_data['BB_Mid'] = recent_data['close'].rolling(window=20).mean()
    recent_data['BB_Upper'] = recent_data['BB_Mid'] + 2 * recent_data['close'].rolling(window=20).std()
    recent_data['BB_Lower'] = recent_data['BB_Mid'] - 2 * recent_data['close'].rolling(window=20).std()

    features = ['BB_Mid', 'BB_Upper', 'BB_Lower']

    valid_data = recent_data.dropna()

    X = valid_data[features].values
    y = valid_data['close'].values


    model = LinearRegression()
    model.fit(X[:-1], y[1:])


    last_row = X[-1].reshape(1, -1)
    predicted_price = model.predict(last_row)[0]


    current_price = recent_data['close'].iloc[-1]
    direction = "рост" if predicted_price > current_price else "падение"

    return predicted_price, direction
