# Energy Consumption Forecasting - Jupyter Notebook Structure

# ----------------------
# 1. Imports & Setup
# ----------------------

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
import lightgbm as lgb

# ----------------------
# 2. Load & Reshape Data
# ----------------------
# Load datasets

import pandas as pd

load_df = pd.read_csv("load_data.csv")
print("Load Data Columns:", load_df.columns)

weather_df = pd.read_csv("weather_data.csv")
print("Weather Data Columns:", weather_df.columns)

# Melt load data
load_long = load_df.melt(id_vars=['zone_id', 'year', 'month', 'day'],
                         value_vars=[f'h{i}' for i in range(1, 25)],
                         var_name='hour', value_name='load')

load_long['hour'] = load_long['hour'].str.extract('h(\d+)').astype(int)
load_long['datetime'] = pd.to_datetime(load_long[['year', 'month', 'day']]) + pd.to_timedelta(load_long['hour'] - 1, unit='h')

# Melt weather data
weather_long = weather_df.melt(id_vars=['station_id', 'year', 'month', 'day'],
                               value_vars=[f'h{i}' for i in range(1, 25)],
                               var_name='hour', value_name='temperature')
weather_long['hour'] = weather_long['hour'].str.extract('h(\d+)').astype(int)
weather_long['datetime'] = pd.to_datetime(weather_long[['year', 'month', 'day']]) + pd.to_timedelta(weather_long['hour'] - 1, unit='h')

# Merge
merged_df = pd.merge(load_long, weather_long, on='datetime')
merged_df = merged_df[['datetime', 'load', 'temperature']].dropna()

# ----------------------
# 3. EDA & Visualization
# ----------------------
# Plot sample trends
sample = merged_df[(merged_df['datetime'] >= '2008-01-01') & (merged_df['datetime'] < '2008-02-01')]
sns.lineplot(data=sample, x='datetime', y='load', label='Load')
sns.lineplot(data=sample, x='datetime', y='temperature', label='Temp')
plt.title('Load & Temperature - Jan 2008')
plt.xticks(rotation=45)
plt.grid()
plt.show()

# Correlation
corr = merged_df[['load', 'temperature']].corr().iloc[0, 1]
print(f"Correlation: {corr:.2f}")

# Load by hour
merged_df['hour'] = merged_df['datetime'].dt.hour
sns.lineplot(data=merged_df, x='hour', y='load', estimator='mean')
plt.title('Avg Load by Hour')
plt.grid()
plt.show()

# ----------------------
# 4. Feature Engineering
# ----------------------
df = merged_df.copy()
df['dayofweek'] = df['datetime'].dt.dayofweek
df['hour'] = df['datetime'].dt.hour
df['month'] = df['datetime'].dt.month

# Lag features
df['load_lag_24'] = df['load'].shift(24)
df['temp_lag_24'] = df['temperature'].shift(24)

# Rolling features
df['load_roll_mean_24'] = df['load'].rolling(24).mean()
df['temp_roll_mean_24'] = df['temperature'].rolling(24).mean()

# Drop NA
df = df.dropna(inplace=True)

# ----------------------
# 5. Train-Test Split
# ----------------------

# Train-Test Split Fix with buffer
test_start = pd.to_datetime('2008-06-01')
test_end = pd.to_datetime('2008-06-08')
buffer_hours = 24

# Select range with buffer for lag features
full_test_df = df[(df['datetime'] >= test_start - pd.Timedelta(hours=buffer_hours)) &
                  (df['datetime'] < test_end)]

# Actual test set starts from 2008-06-01 after having 24-hour context
test_df = full_test_df.iloc[buffer_hours:]

# Train set: everything before the buffer
train_df = df[df['datetime'] < test_start - pd.Timedelta(hours=buffer_hours)]

# train_df = df[df['datetime'] < '2008-05-31']  # shift back
#test_df = df[(df['datetime'] >= '2008-06-01') & (df['datetime'] < '2008-06-08')]

features = ['temperature', 'hour', 'dayofweek', 'month', 'load_lag_24', 'temp_lag_24', 'load_roll_mean_24', 'temp_roll_mean_24']

X_train = train_df[features]
y_train = train_df['load']
X_test = test_df[features]
y_test = test_df['load']

print(X_test.shape)
print(X_test.head())

# ----------------------
# 6. Model Training
# ----------------------
model = lgb.LGBMRegressor(n_estimators=100, learning_rate=0.05)
model.fit(X_train, y_train)

# Predict
y_pred = model.predict(X_test)

# ----------------------
# 7. Evaluation
# ----------------------
mae = mean_absolute_error(y_test, y_pred)
rmse = mean_squared_error(y_test, y_pred, squared=False)
print(f"MAE: {mae:.2f}, RMSE: {rmse:.2f}")

# Plot actual vs predicted
plt.figure(figsize=(15, 5))
plt.plot(test_df['datetime'], y_test.values, label='Actual', linewidth=2)
plt.plot(test_df['datetime'], y_pred, label='Predicted', linestyle='--')
plt.title('7-Day Forecast: Actual vs Predicted Load')
plt.xticks(rotation=45)
plt.legend()
plt.grid()
plt.tight_layout()
plt.show()

# type: ignore # ----------------------
# 8. Report Summary
# ----------------------
# You can summarize in markdown:
# - Approach taken (EDA, features, model)
# - Key findings
# - Model performance
# - Limitations (e.g., limited features)
# - Potential improvements (holiday features, ensemble models)
