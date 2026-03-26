# Quick data peek for mlab_ndt_us_30days_20251111_004612.csv
import pandas as pd

df = pd.read_csv('mlab_ndt_us_30days_20251111_004612.csv')

# Preview first and last rows
print(df.head())
print(df.tail())

# Show column names
print(df.columns)