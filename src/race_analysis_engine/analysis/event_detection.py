import json
from pathlib import Path
import numpy as np
import pandas as pd

RACE_FOLDER = Path(__file__).parent
TELEMETRY_CSV = RACE_FOLDER / 'telemetry_clean.csv'
PER_LAP_CSV = RACE_FOLDER / 'per_lap_metrics.csv'
LAPS_DIR = RACE_FOLDER / 'laps'
OUT_CSV = RACE_FOLDER / 'event_detection.csv'

def detect_lap_level_events(per_lap):
    # compute rolling means for previous 3 laps per vehicle
    per_lap = per_lap.sort_values(['vehicle_id', 'lap']).copy()
    per_lap[['rm_lap_time', 'rm_latG', 'rm_longG']] = per_lap.groupby('vehicle_id')[['lap_time_seconds','peak_lat_G','peak_long_G']].apply(lambda g: g.shift(1).rolling(3, min_periods=1).mean()).reset_index(level=0, drop=True)

    events = []
    # Pace collapse
    for _, row in per_lap.iterrows():
        vid = row['vehicle_id']
        lap = int(row['lap'])
        ts = pd.to_datetime(row['end_time']) if 'end_time' in row else pd.to_datetime(row['start_time'])
        if pd.notna(row['rm_lap_time']):
            if (row['lap_time_seconds'] > 1.015 * row['rm_lap_time']) and (row['peak_lat_G'] < row['rm_latG'] - 0.2) and (row['peak_long_G'] < row['rm_longG'] - 0.15):
                ev = {
                    'event_id': f"{vid}_L{lap}_T{ts.strftime('%Y%m%dT%H%M%S%f')}",
                    'vehicle_id': vid,
                    'lap': lap,
                    'timestamp': ts.isoformat(),
                    'event_type': 'pace_collapse',
                    'severity_score': 0.7,
                    'time_loss_estimate': float(max(0.5, (row['lap_time_seconds'] - row['rm_lap_time'])/1.0)),
                    'steering_correction_deg': np.nan,
                    'brake_spike': False,
                    'speed_loss': np.nan,
                    'latG_spike': np.nan,
                    'rpm_drop': np.nan,
                    'description': 'Lap time notably slower than previous 3-lap mean with reduced cornering/long G.'
                }
                events.append(ev)

    # Degradation: compute linear slope per driver
    for vid, g in per_lap.groupby('vehicle_id'):
        if len(g) < 3:
            continue
        x = g['lap'].astype(float).values
        y = g['lap_time_seconds'].values
        try:
            slope = np.polyfit(x, y, 1)[0]
        except Exception:
            slope = np.nan
        lat_slope = np.nan
        try:
            lat_slope = np.polyfit(x, g['peak_lat_G'].values, 1)[0]
        except Exception:
            lat_slope = np.nan
        if pd.notna(slope) and pd.notna(lat_slope) and (slope > 0.1) and (lat_slope < -0.01):
            last_row = g.iloc[-1]
            ts = pd.to_datetime(last_row['end_time']) if 'end_time' in last_row else pd.to_datetime(last_row['start_time'])
            ev = {
                'event_id': f"{vid}_degradation_L{int(last_row['lap'])}_T{ts.strftime('%Y%m%dT%H%M%S%f')}",
                'vehicle_id': vid,
                'lap': int(last_row['lap']),
                'timestamp': ts.isoformat(),
                'event_type': 'degradation_phase',
                'severity_score': min(1.0, float((slope/0.5))),
                'time_loss_estimate': float(np.nanmean(g['lap_time_seconds'].diff().fillna(0).clip(lower=0).tail(3))),
                'steering_correction_deg': np.nan,
                'brake_spike': False,
                'speed_loss': np.nan,
                'latG_spike': np.nan,
                'rpm_drop': np.nan,
                'description': 'Slow steady increase in lap times with falling lateral capability.'
            }
            events.append(ev)

    return events


def detect_telemetry_events(per_lap):
    events = []
    # Iterate per lap and load corresponding parquet file
    for _, row in per_lap.iterrows():
        vid = row['vehicle_id']
        lap = int(row['lap'])
        fname = f"{vid}_lag_{lap}.parquet"
        # Try known patterns
        fpath = LAPS_DIR / f"{vid}_lap_{lap}.parquet"
        if not fpath.exists():
            fpath = LAPS_DIR / f"{vid}_lap{lap}.parquet"
            if not fpath.exists():
                fpath = LAPS_DIR / fname
                if not fpath.exists():
                    continue
        df = pd.read_parquet(fpath)
        # Ensure columns exist
        for col in ['speed','Steering_Angle','accy_can','pbrake_f','pbrake_r','nmot','gear']:
            if col not in df.columns:
                df[col] = np.nan

        # Work on numeric arrays
        df = df.sort_index()
        # compute shifts
        for k in (1,2,3):
            df[f'speed_m{k}'] = df['speed'].shift(k)
            df[f'steer_m{k}'] = df['Steering_Angle'].shift(k)
            df[f'accy_m{k}'] = df['accy_can'].shift(k)
            df[f'pbr_m{k}'] = df['pbrake_f'].shift(k)
            df[f'nmot_m{k}'] = df['nmot'].shift(k)
            df[f'gear_m{k}'] = df['gear'].shift(k)

        # apply rules row-wise
        for idx in df.index[3:]:
            row_t = df.loc[idx]
            # safe access with fillna
            try:
                cond_lock = False
                if pd.notna(row_t['pbrake_f']) and pd.notna(row_t['pbr_m2']):
                    if (row_t['pbrake_f'] - row_t['pbr_m2'] > 10):
                        spd3 = row_t['speed_m3']
                        spd0 = row_t['speed']
                        accy3 = row_t['accy_m3']
                        accy0 = row_t['accy_can']
                        if pd.notna(spd3) and pd.notna(spd0) and pd.notna(accy3) and pd.notna(accy0):
                            if (spd3 - spd0 > 6) and (accy3 - accy0 > 0.3):
                                cond_lock = True
                if cond_lock:
                    speed_loss = float((row_t['speed_m3'] - row_t['speed'])) if pd.notna(row_t['speed_m3']) and pd.notna(row_t['speed']) else np.nan
                    lat_spike = float((row_t['accy_m3'] - row_t['accy_can'])) if pd.notna(row_t['accy_m3']) and pd.notna(row_t['accy_can']) else np.nan
                    steer_corr = float(abs(row_t['Steering_Angle'] - row_t['steer_m2'])) if pd.notna(row_t['Steering_Angle']) and pd.notna(row_t['steer_m2']) else np.nan
                    ev = {
                        'event_id': f"{vid}_L{lap}_T{idx.strftime('%Y%m%dT%H%M%S%f')}",
                        'vehicle_id': vid,
                        'lap': lap,
                        'timestamp': idx.isoformat(),
                        'event_type': 'lockup',
                        'severity_score': min(1.0, np.nanmean([abs(row_t['pbrake_f'] - row_t['pbr_m2'])/50, (speed_loss or 0)/10, (lat_spike or 0)/2])),
                        'time_loss_estimate': float((speed_loss/9.0) if pd.notna(speed_loss) else np.nan),
                        'steering_correction_deg': steer_corr,
                        'brake_spike': True,
                        'speed_loss': speed_loss,
                        'latG_spike': lat_spike,
                        'rpm_drop': np.nan,
                        'description': 'Large front brake spike with notable speed and lateral G drop.'
                    }
                    events.append(ev)
                    continue

            except Exception:
                pass

            # Near spin
            try:
                cond_spin = False
                if pd.notna(row_t['Steering_Angle']) and pd.notna(row_t['steer_m2']):
                    if abs(row_t['Steering_Angle'] - row_t['steer_m2']) > 20:
                        if pd.notna(row_t['accy_can']) and pd.notna(row_t['accy_m3']) and pd.notna(row_t['speed_m3']) and pd.notna(row_t['speed']):
                            if (row_t['accy_can'] - row_t['accy_m3'] > 1.5) and (row_t['speed_m3'] - row_t['speed'] > 4):
                                cond_spin = True
                if cond_spin:
                    speed_loss = float((row_t['speed_m3'] - row_t['speed']))
                    lat_spike = float((row_t['accy_can'] - row_t['accy_m3']))
                    steer_corr = float(abs(row_t['Steering_Angle'] - row_t['steer_m2']))
                    ev = {
                        'event_id': f"{vid}_L{lap}_T{idx.strftime('%Y%m%dT%H%M%S%f')}",
                        'vehicle_id': vid,
                        'lap': lap,
                        'timestamp': idx.isoformat(),
                        'event_type': 'near_spin',
                        'severity_score': min(1.0, (steer_corr/40 + lat_spike/3 + speed_loss/10)/3),
                        'time_loss_estimate': float(speed_loss/9.0),
                        'steering_correction_deg': steer_corr,
                        'brake_spike': False,
                        'speed_loss': speed_loss,
                        'latG_spike': lat_spike,
                        'rpm_drop': np.nan,
                        'description': 'Rapid large steering input with lateral G increase and speed drop.'
                    }
                    events.append(ev)
                    continue
            except Exception:
                pass

            # Understeer
            try:
                cond_under = False
                if pd.notna(row_t['Steering_Angle']) and pd.notna(row_t['steer_m3']):
                    if (row_t['Steering_Angle'] - row_t['steer_m3'] > 8):
                        if pd.notna(row_t['accy_can']) and pd.notna(row_t['accy_m3']):
                            if abs(row_t['accy_can'] - row_t['accy_m3']) < 0.2 and (row_t['speed_m3'] - row_t['speed'] > 3):
                                cond_under = True
                if cond_under:
                    speed_loss = float((row_t['speed_m3'] - row_t['speed']))
                    steer_corr = float(abs(row_t['Steering_Angle'] - row_t['steer_m3']))
                    ev = {
                        'event_id': f"{vid}_L{lap}_T{idx.strftime('%Y%m%dT%H%M%S%f')}",
                        'vehicle_id': vid,
                        'lap': lap,
                        'timestamp': idx.isoformat(),
                        'event_type': 'understeer',
                        'severity_score': min(1.0, (steer_corr/20 + (speed_loss or 0)/10)/2),
                        'time_loss_estimate': float(speed_loss/9.0) if pd.notna(speed_loss) else np.nan,
                        'steering_correction_deg': steer_corr,
                        'brake_spike': False,
                        'speed_loss': speed_loss,
                        'latG_spike': float(abs(row_t['accy_can'] - row_t['accy_m3'])) if pd.notna(row_t['accy_can']) and pd.notna(row_t['accy_m3']) else np.nan,
                        'rpm_drop': np.nan,
                        'description': 'Steering increased but lateral G did not respond — likely understeer.'
                    }
                    events.append(ev)
                    continue
            except Exception:
                pass

            # Missed shift
            try:
                if pd.notna(row_t['gear']) and pd.notna(row_t['gear_m1']) and (row_t['gear'] != row_t['gear_m1']):
                    if pd.notna(row_t['nmot_m1']) and pd.notna(row_t['nmot']) and (row_t['nmot_m1'] - row_t['nmot'] > 1200) and pd.notna(row_t['speed']) and pd.notna(row_t['speed_m1']) and (abs(row_t['speed'] - row_t['speed_m1']) < 1.5):
                        rpm_drop = float(row_t['nmot_m1'] - row_t['nmot'])
                        ev = {
                            'event_id': f"{vid}_L{lap}_T{idx.strftime('%Y%m%dT%H%M%S%f')}",
                            'vehicle_id': vid,
                            'lap': lap,
                            'timestamp': idx.isoformat(),
                            'event_type': 'missed_shift',
                            'severity_score': min(1.0, rpm_drop/4000),
                            'time_loss_estimate': 0.5,
                            'steering_correction_deg': np.nan,
                            'brake_spike': False,
                            'speed_loss': float(abs(row_t['speed'] - row_t['speed_m1'])),
                            'latG_spike': np.nan,
                            'rpm_drop': rpm_drop,
                            'description': 'Gear change with large RPM drop and minimal speed change — likely missed shift.'
                        }
                        events.append(ev)
                        continue
            except Exception:
                pass

    return events


def main():
    per_lap = pd.read_csv(PER_LAP_CSV, parse_dates=['start_time','end_time'])
    lap_events = detect_lap_level_events(per_lap)
    tele_events = detect_telemetry_events(per_lap)

    all_events = lap_events + tele_events
    if not all_events:
        print('No events detected')
        return

    df = pd.DataFrame(all_events)
    # add key_metrics_json column
    df['key_metrics_json'] = df.apply(lambda r: json.dumps({
        'steering_correction_deg': r.get('steering_correction_deg'),
        'latG_spike': r.get('latG_spike'),
        'speed_loss_kph': r.get('speed_loss'),
        'rpm_drop': r.get('rpm_drop'),
        'brake_spike': bool(r.get('brake_spike'))
    }), axis=1)

    # select columns
    out_cols = ['event_id','vehicle_id','lap','timestamp','event_type','severity_score','time_loss_estimate','steering_correction_deg','brake_spike','speed_loss','latG_spike','rpm_drop','description','key_metrics_json']
    df = df[out_cols]
    df.to_csv(OUT_CSV, index=False)
    print('Wrote', OUT_CSV, 'with', len(df), 'events')


if __name__ == '__main__':
    main()
