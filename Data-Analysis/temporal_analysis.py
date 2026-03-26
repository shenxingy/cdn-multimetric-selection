"""
Temporal Feature Analysis for M-Lab Data
=========================================
Extracts time-based patterns to show when RTT alone is insufficient.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_absolute_error
import warnings
warnings.filterwarnings('ignore')

# Load M-Lab data — path resolved relative to repo root
data_path = Path(__file__).resolve().parents[1] / "notebooks" / "data" / "raw" / "mlab_ndt_us_30days_20251111_004612.csv"
print(f"Loading M-Lab data from {data_path}...")
df = pd.read_csv(data_path, parse_dates=['date'])
print(f"✓ Loaded {len(df):,} measurements")

# Clean data
df = df.dropna(subset=['download_mbps', 'min_rtt_ms', 'packet_loss_rate'])
df = df[df['min_rtt_ms'] > 0]
df = df[df['download_mbps'] >= 0]
print(f"✓ After cleaning: {len(df):,} measurements")

# Extract temporal features
print("\n" + "="*80)
print("EXTRACTING TEMPORAL FEATURES")
print("="*80)

df['hour'] = df['date'].dt.hour
df['day_of_week'] = df['date'].dt.dayofweek
df['day_of_month'] = df['date'].dt.day
df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
df['is_peak_hours'] = df['hour'].isin([18, 19, 20, 21, 22]).astype(int)  # Evening 6pm-11pm
df['is_business_hours'] = df['hour'].isin(range(9, 18)).astype(int)  # 9am-6pm
df['time_of_day'] = pd.cut(df['hour'], bins=[0, 6, 12, 18, 24], labels=['night', 'morning', 'afternoon', 'evening'])

# Create cyclical encoding for hour (captures circular nature of time)
df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)

# Create engineered features
df['inv_rtt'] = 1.0 / df['min_rtt_ms']
df['log_download'] = np.log1p(df['download_mbps'])

print(f"✓ Extracted temporal features:")
print(f"  - hour (0-23)")
print(f"  - day_of_week (0=Monday, 6=Sunday)")
print(f"  - is_weekend (binary)")
print(f"  - is_peak_hours (6pm-11pm, binary)")
print(f"  - is_business_hours (9am-6pm, binary)")
print(f"  - hour_sin, hour_cos (cyclical encoding)")

# Analyze temporal patterns
print("\n" + "="*80)
print("TEMPORAL PATTERN ANALYSIS")
print("="*80)

# Group by hour
hourly_stats = df.groupby('hour').agg({
    'download_mbps': ['mean', 'std', 'count'],
    'min_rtt_ms': ['mean', 'std'],
    'packet_loss_rate': ['mean']
}).round(2)

print("\nThroughput by Hour of Day:")
print("-" * 80)
for hour in range(24):
    if hour in hourly_stats.index:
        throughput = hourly_stats.loc[hour, ('download_mbps', 'mean')]
        rtt = hourly_stats.loc[hour, ('min_rtt_ms', 'mean')]
        count = int(hourly_stats.loc[hour, ('download_mbps', 'count')])
        time_label = "PEAK" if hour in [18, 19, 20, 21, 22] else "     "
        print(f"  {hour:02d}:00 {time_label} | Throughput: {throughput:6.1f} Mbps | RTT: {rtt:6.1f} ms | n={count:,}")

# Peak vs Off-peak comparison
peak_throughput = df[df['is_peak_hours'] == 1]['download_mbps'].mean()
offpeak_throughput = df[df['is_peak_hours'] == 0]['download_mbps'].mean()
peak_rtt = df[df['is_peak_hours'] == 1]['min_rtt_ms'].mean()
offpeak_rtt = df[df['is_peak_hours'] == 0]['min_rtt_ms'].mean()

print(f"\n{'='*80}")
print("PEAK vs OFF-PEAK ANALYSIS")
print("="*80)
print(f"Peak Hours (6pm-11pm):")
print(f"  - Throughput: {peak_throughput:.1f} Mbps")
print(f"  - RTT: {peak_rtt:.1f} ms")
print(f"\nOff-Peak Hours:")
print(f"  - Throughput: {offpeak_throughput:.1f} Mbps")
print(f"  - RTT: {offpeak_rtt:.1f} ms")
print(f"\nPeak vs Off-Peak Difference:")
print(f"  - Throughput: {((peak_throughput - offpeak_throughput) / offpeak_throughput * 100):+.1f}%")
print(f"  - RTT: {((peak_rtt - offpeak_rtt) / offpeak_rtt * 100):+.1f}%")

# Weekend vs Weekday
weekend_throughput = df[df['is_weekend'] == 1]['download_mbps'].mean()
weekday_throughput = df[df['is_weekend'] == 0]['download_mbps'].mean()

print(f"\nWeekend vs Weekday:")
print(f"  - Weekend throughput: {weekend_throughput:.1f} Mbps")
print(f"  - Weekday throughput: {weekday_throughput:.1f} Mbps")
print(f"  - Difference: {((weekend_throughput - weekday_throughput) / weekday_throughput * 100):+.1f}%")

# Model comparison: RTT-only vs RTT+Temporal
print("\n" + "="*80)
print("MODEL COMPARISON: RTT-ONLY vs RTT+TEMPORAL")
print("="*80)

# Prepare data
X_rtt_only = df[['inv_rtt', 'packet_loss_rate']]
X_with_temporal = df[['inv_rtt', 'packet_loss_rate', 'hour_sin', 'hour_cos', 
                       'is_weekend', 'is_peak_hours', 'is_business_hours']]
y = df['log_download']

# Split data
X_rtt_train, X_rtt_test, y_train, y_test = train_test_split(
    X_rtt_only, y, test_size=0.2, random_state=42
)
X_temp_train, X_temp_test, _, _ = train_test_split(
    X_with_temporal, y, test_size=0.2, random_state=42
)

# Train RTT-only model
scaler_rtt = StandardScaler()
X_rtt_train_scaled = scaler_rtt.fit_transform(X_rtt_train)
X_rtt_test_scaled = scaler_rtt.transform(X_rtt_test)

model_rtt = Ridge(alpha=1.0)
model_rtt.fit(X_rtt_train_scaled, y_train)
y_pred_rtt = model_rtt.predict(X_rtt_test_scaled)

r2_rtt = r2_score(y_test, y_pred_rtt)
mae_rtt = mean_absolute_error(y_test, y_pred_rtt)

# Train RTT+Temporal model
scaler_temp = StandardScaler()
X_temp_train_scaled = scaler_temp.fit_transform(X_temp_train)
X_temp_test_scaled = scaler_temp.transform(X_temp_test)

model_temp = Ridge(alpha=1.0)
model_temp.fit(X_temp_train_scaled, y_train)
y_pred_temp = model_temp.predict(X_temp_test_scaled)

r2_temp = r2_score(y_test, y_pred_temp)
mae_temp = mean_absolute_error(y_test, y_pred_temp)

print(f"\nRTT-Only Model (inv_rtt + packet_loss):")
print(f"  - R² Score: {r2_rtt:.4f} ({r2_rtt*100:.2f}%)")
print(f"  - MAE: {mae_rtt:.4f}")

print(f"\nRTT+Temporal Model (+ hour_sin, hour_cos, is_weekend, is_peak, is_business):")
print(f"  - R² Score: {r2_temp:.4f} ({r2_temp*100:.2f}%)")
print(f"  - MAE: {mae_temp:.4f}")

improvement = ((r2_temp - r2_rtt) / r2_rtt * 100) if r2_rtt > 0 else 0
print(f"\nImprovement: {improvement:+.1f}%")
print(f"R² increase: {(r2_temp - r2_rtt)*100:+.2f} percentage points")

# Feature importance for temporal model
feature_names = ['inv_rtt', 'packet_loss_rate', 'hour_sin', 'hour_cos', 
                 'is_weekend', 'is_peak_hours', 'is_business_hours']
feature_importance = pd.DataFrame({
    'feature': feature_names,
    'coefficient': model_temp.coef_
}).sort_values('coefficient', key=abs, ascending=False)

print(f"\nFeature Importance (Temporal Model):")
print("-" * 80)
for _, row in feature_importance.iterrows():
    print(f"  {row['feature']:20s}: {row['coefficient']:+.4f}")

# Analyze cases where temporal features matter most
print("\n" + "="*80)
print("WHEN DO TEMPORAL FEATURES MATTER?")
print("="*80)

# Calculate prediction errors
df_test = X_temp_test.copy()
df_test['y_true'] = y_test.values
df_test['y_pred_rtt'] = y_pred_rtt
df_test['y_pred_temporal'] = y_pred_temp
df_test['error_rtt'] = np.abs(df_test['y_true'] - df_test['y_pred_rtt'])
df_test['error_temporal'] = np.abs(df_test['y_true'] - df_test['y_pred_temporal'])
df_test['improvement'] = df_test['error_rtt'] - df_test['error_temporal']

# Find cases where temporal model helps most
top_improvements = df_test.nlargest(100, 'improvement')
print(f"\nTop 100 cases where temporal features help:")
print(f"  - Peak hours: {(top_improvements['is_peak_hours'] == 1).sum()}% are during peak (6pm-11pm)")
print(f"  - Weekends: {(top_improvements['is_weekend'] == 1).sum()}% are on weekends")
print(f"  - Business hours: {(top_improvements['is_business_hours'] == 1).sum()}% are during business hours")

# Summary statistics
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"\n✓ Temporal patterns detected in M-Lab data:")
print(f"  - Peak hours show {abs((peak_throughput - offpeak_throughput) / offpeak_throughput * 100):.1f}% throughput difference")
print(f"  - Adding temporal features improves R² by {improvement:+.1f}%")
print(f"  - Temporal model is most helpful during peak/business hours")

if improvement > 5:
    print(f"\n🎯 SIGNIFICANT FINDING: Temporal features provide meaningful improvement!")
    print(f"   This shows RTT alone misses time-based congestion patterns.")
elif improvement > 0:
    print(f"\n⚠️  MODEST FINDING: Temporal features provide small improvement ({improvement:.1f}%)")
    print(f"   Time patterns exist but explain little additional variance.")
else:
    print(f"\n✗ NO IMPROVEMENT: Temporal features don't help in this dataset.")
    print(f"  RTT already captures most time-varying effects.")

print("\n" + "="*80)
