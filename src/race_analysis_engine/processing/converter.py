import pandas as pd

# Read the data
df = pd.read_csv('R1_road_america_telemetry_data.csv')

# Convert timestamp to datetime (ISO 8601 format)
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Pivot from long to wide format
# telemetry_name becomes columns, telemetry_value becomes values
df_wide = df.pivot_table(
    index=['vehicle_id', 'lap', 'timestamp'],
    columns='telemetry_name',
    values='telemetry_value',
    aggfunc='first'
).reset_index()

# Select only the signals you need (if they exist)
signals_needed = ['speed', 'accx_can', 'accy_can', 'ath', 'pbrake_f', 'pbrake_r', 'Steering_Angle', 'nmot', 'gear']
available_signals = [col for col in signals_needed if col in df_wide.columns]
df_wide = df_wide[['vehicle_id', 'lap', 'timestamp'] + available_signals]

# Sort by vehicle_id, lap, timestamp
df_wide = df_wide.sort_values(['vehicle_id', 'lap', 'timestamp']).reset_index(drop=True)

# Display the result
print("Converted data shape:", df_wide.shape)
print("\nFirst few rows:")
print(df_wide.head())
print("\nColumns:", df_wide.columns.tolist())

# Save to CSV
df_wide.to_csv('telemetry_clean.csv', index=False)
print("\nSaved to telemetry_clean.csv")