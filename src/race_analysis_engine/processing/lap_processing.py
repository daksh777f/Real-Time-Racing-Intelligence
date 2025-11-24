import os
import argparse
from pathlib import Path
import numpy as np
import pandas as pd


SIGNALS = ['speed', 'accx_can', 'accy_can', 'ath', 'pbrake_f', 'pbrake_r', 'Steering_Angle', 'nmot', 'gear']


def load_telemetry(path):
    df = pd.read_csv(path)
    # normalize timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True, errors='coerce')
    df = df.dropna(subset=['timestamp'])
    return df


def resample_lap(df, signals=SIGNALS):
    # df must have 'timestamp' as datetime and be for one vehicle+lap
    # since data is complete, just select and sort, no imputation needed
    df = df.set_index('timestamp').sort_index()
    # keep only signals
    keep = [c for c in signals if c in df.columns]
    if not keep:
        return None
    sub = df[keep].copy()  # copy to avoid SettingWithCopyWarning
    # ensure numeric types
    for c in sub.columns:
        sub[c] = pd.to_numeric(sub[c], errors='coerce')
    return sub


def compute_lap_metrics(lap_df, lap_start, lap_end, lap_time_source=None):
    # lap_df is resampled time-indexed dataframe
    out = {}
    out['start_time'] = lap_start
    out['end_time'] = lap_end
    out['n_samples'] = len(lap_df)
    if lap_time_source is not None:
        out['lap_time_seconds'] = float(lap_time_source)
    else:
        out['lap_time_seconds'] = (pd.to_datetime(lap_end) - pd.to_datetime(lap_start)).total_seconds()

    if 'speed' in lap_df.columns:
        out['max_speed'] = float(lap_df['speed'].max()) if lap_df['speed'].notna().any() else np.nan
        out['mean_speed'] = float(lap_df['speed'].mean()) if lap_df['speed'].notna().any() else np.nan
        out['min_speed'] = float(lap_df['speed'].min()) if lap_df['speed'].notna().any() else np.nan
    else:
        out['max_speed'] = out['mean_speed'] = out['min_speed'] = np.nan

    # peak lateral/longitudinal G
    out['peak_lat_G'] = float(lap_df['accy_can'].abs().max()) if 'accy_can' in lap_df.columns else np.nan
    out['peak_long_G'] = float(lap_df['accx_can'].abs().max()) if 'accx_can' in lap_df.columns else np.nan

    # throttle smoothness = mean absolute delta
    if 'ath' in lap_df.columns:
        out['throttle_smoothness'] = float(lap_df['ath'].diff().abs().mean())
    else:
        out['throttle_smoothness'] = np.nan

    # steering variance
    out['steering_variance'] = float(lap_df['Steering_Angle'].var()) if 'Steering_Angle' in lap_df.columns else np.nan

    # brake spikes
    if 'pbrake_f' in lap_df.columns:
        db = lap_df['pbrake_f'].diff().abs()
        out['brake_spikes'] = int((db > 0.2).sum())
    else:
        out['brake_spikes'] = 0

    # gear changes
    if 'gear' in lap_df.columns:
        g = lap_df['gear'].ffill().bfill().fillna(-1)
        out['gear_changes'] = int((g != g.shift()).sum())
    else:
        out['gear_changes'] = 0

    return out


def main(telemetry_path, laps_out='laps', limit=None):
    Path(laps_out).mkdir(exist_ok=True)

    print('Loading telemetry:', telemetry_path)
    tele = load_telemetry(telemetry_path)
    # ensure lap column exists
    if 'lap' not in tele.columns:
        raise SystemExit('telemetry_clean.csv must contain `lap` column')

    groups = tele[['vehicle_id', 'lap']].drop_duplicates().sort_values(['vehicle_id', 'lap'])
    total_groups = len(groups)
    print(f'Found {total_groups} (vehicle,lap) groups')

    per_lap = []
    processed = 0
    for _, row in groups.iterrows():
        if limit is not None and processed >= limit:
            break
        vid = row['vehicle_id']
        lapnum = int(row['lap'])
        g = tele[(tele['vehicle_id'] == vid) & (tele['lap'] == lapnum)]
        if g.empty:
            continue
        lap_start = g['timestamp'].min()
        lap_end = g['timestamp'].max()
        # skip obviously broken laps
        if (pd.to_datetime(lap_end) - pd.to_datetime(lap_start)).total_seconds() < 1.0:
            # too short
            print(f'Skipping short lap {vid} lap {lapnum}')
            processed += 1
            continue

        lap_resampled = resample_lap(g, SIGNALS)
        if lap_resampled is None or len(lap_resampled) < 5:
            print(f'Skipping lap with insufficient data {vid} lap {lapnum}')
            processed += 1
            continue

        metrics = compute_lap_metrics(lap_resampled, lap_start, lap_end)
        metrics.update({'vehicle_id': vid, 'lap': lapnum})
        per_lap.append(metrics)

        # save lap parquet
        outfn = Path(laps_out) / f"{vid}_lap_{lapnum}.parquet"
        lap_resampled.to_parquet(outfn)

        processed += 1
        if processed % 10 == 0:
            print(f'Processed {processed}/{total_groups} laps')

    per_lap_df = pd.DataFrame(per_lap)
    per_lap_df.to_csv('per_lap_metrics.csv', index=False)
    print('Wrote per_lap_metrics.csv', per_lap_df.shape)

    # aggregate per-driver
    if not per_lap_df.empty:
        agg = {
            'lap_time_seconds': ['mean', 'min', 'std'],
            'max_speed': 'mean',
            'peak_lat_G': 'mean',
            'peak_long_G': 'mean',
            'throttle_smoothness': 'mean',
            'steering_variance': 'mean',
            'brake_spikes': 'sum',
            'gear_changes': 'sum'
        }
        per_driver = per_lap_df.groupby('vehicle_id').agg(agg)
        # flatten columns
        per_driver.columns = ['_'.join(c).strip() if isinstance(c, tuple) else c for c in per_driver.columns.values]
        per_driver = per_driver.reset_index()
        per_driver.to_csv('per_driver_metrics.csv', index=False)
        print('Wrote per_driver_metrics.csv', per_driver.shape)
    else:
        print('No per-lap metrics to aggregate')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--telemetry', default='telemetry_clean.csv')
    p.add_argument('--limit', type=int, default=None, help='Process only first N laps')
    p.add_argument('--outdir', default='laps')
    args = p.parse_args()
    main(args.telemetry, laps_out=args.outdir, limit=args.limit)
