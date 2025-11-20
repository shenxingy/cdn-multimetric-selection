#import pandas and preview mlab_ndt_us_30days_20251111_004612.csv
import pandas as pd
df = pd.read_csv('mlab_ndt_us_30days_20251111_004612.csv')
print(df.head())

#preview the first 5 rows of the dataframe
print(df.head()) #this is the same as print(df.head())

#preview the last 5 rows of the dataframe
print(df.tail())

#preview the columns of the dataframe
print(df.columns)