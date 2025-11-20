"""Calculate R² for RTT-only model."""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

# Load data
df = pd.read_csv('./mlab_ndt_us_30days_20251111_004612.csv')

# Feature engineering
df['inv_rtt'] = 1000.0 / df['min_rtt_ms']
df['log_download'] = np.log10(df['download_mbps'])

# Remove invalid values
df = df[np.isfinite(df['inv_rtt']) & np.isfinite(df['log_download'])]

# Only use inv_rtt as feature
X = df[['inv_rtt']].values
y = df['log_download'].values

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = LinearRegression()
model.fit(X_train, y_train)

# Evaluate
y_pred_train = model.predict(X_train)
y_pred_test = model.predict(X_test)

r2_train = r2_score(y_train, y_pred_train)
r2_test = r2_score(y_test, y_pred_test)
rmse_test = np.sqrt(mean_squared_error(y_test, y_pred_test))
mae_test = mean_absolute_error(y_test, y_pred_test)

print('='*70)
print('只使用 RTT (inverse RTT) 的线性回归结果:')
print('='*70)
print(f'特征: inv_rtt (1000 / MinRTT)')
print(f'样本数 (训练): {len(X_train)}')
print(f'样本数 (测试): {len(X_test)}')
print(f'')
print(f'R² (训练集): {r2_train:.6f}')
print(f'R² (测试集):  {r2_test:.6f}')
print(f'RMSE (测试集): {rmse_test:.6f}')
print(f'MAE (测试集):  {mae_test:.6f}')
print(f'')
print(f'模型系数: {model.coef_[0]:.6f}')
print(f'截距: {model.intercept_:.6f}')
print('='*70)

# Compare with Model A (which uses inv_rtt + packet_loss_rate)
print('\n对比 Model A (inv_rtt + packet_loss_rate): R² = 0.066140')
print(f'只用 RTT 的 R²: {r2_test:.6f}')
print(f'差异: {(0.066140 - r2_test):.6f}')

