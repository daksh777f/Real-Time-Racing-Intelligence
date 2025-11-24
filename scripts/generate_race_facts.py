import json
from pathlib import Path
import pandas as pd
import numpy as np

RACE_FOLDER = Path(__file__).parent
PER_LAP_CSV = RACE_FOLDER / 'per_lap_metrics.csv'
PER_DRIVER_CSV = RACE_FOLDER / 'per_driver_metrics.csv'
EVENTS_CSV = RACE_FOLDER / 'event_detection.csv'
OUT_DIR = RACE_FOLDER


def load_inputs():
    per_lap = pd.read_csv(PER_LAP_CSV, parse_dates=['start_time','end_time'])
    per_driver = pd.read_csv(PER_DRIVER_CSV)
    events = pd.read_csv(EVENTS_CSV)
    telemetry = pd.read_csv(RACE_FOLDER / 'telemetry_clean.csv', parse_dates=['timestamp'])
    return per_lap, per_driver, events, telemetry


def tag_drivers(per_driver, per_lap):
    # compute population thresholds
    pd_copy = per_driver.copy()
    # ensure numeric
    for c in ['brake_spikes_sum','steering_variance_mean','lap_time_std','throttle_smoothness_mean']:
        if c in pd_copy.columns:
            pd_copy[c] = pd.to_numeric(pd_copy[c], errors='coerce')
        else:
            pd_copy[c] = np.nan

    q75_brake = pd_copy['brake_spikes_sum'].quantile(0.75)
    q25_steer = pd_copy['steering_variance_mean'].quantile(0.25)
    q75_steer = pd_copy['steering_variance_mean'].quantile(0.75)
    q75_lapstd = pd_copy['lap_time_std'].quantile(0.75)

    tags = {}
    for _, r in pd_copy.iterrows():
        vid = r['vehicle_id']
        t = []
        if pd.notna(r['brake_spikes_sum']) and r['brake_spikes_sum'] > q75_brake:
            t.append('aggressive_braking')
        if pd.notna(r['steering_variance_mean']) and r['steering_variance_mean'] < q25_steer:
            t.append('smooth_steering')
        if pd.notna(r['steering_variance_mean']) and r['steering_variance_mean'] > q75_steer:
            t.append('erratic_steering')
        if pd.notna(r['lap_time_std']) and r['lap_time_std'] > q75_lapstd:
            t.append('inconsistent_laps')
        # late_race_fade: compare mean of last 3 laps vs first 3 laps for this vehicle
        drv_laps = per_lap[per_lap['vehicle_id'] == vid].sort_values('lap')
        if len(drv_laps) >= 6:
            first_mean = drv_laps.head(3)['lap_time_seconds'].mean()
            last_mean = drv_laps.tail(3)['lap_time_seconds'].mean()
            if (last_mean - first_mean) > 0.5:
                t.append('late_race_fade')
        tags[vid] = t
    return tags


def event_to_object(ev_row):
    # transform a row from event_detection into LLM-friendly object
    metrics = {}
    for k in ['steering_correction_deg','latG_spike','speed_loss','rpm_drop']:
        if k in ev_row and pd.notna(ev_row[k]):
            # rename speed_loss -> speed_loss_kph
            if k == 'speed_loss':
                metrics['speed_loss_kph'] = float(ev_row[k])
            else:
                metrics[k] = float(ev_row[k])
    return {
        'event_type': ev_row.get('event_type'),
        'lap': int(ev_row.get('lap')) if pd.notna(ev_row.get('lap')) else None,
        'timestamp': ev_row.get('timestamp'),
        'vehicle_id': ev_row.get('vehicle_id'),
        'severity': float(ev_row.get('severity_score')) if pd.notna(ev_row.get('severity_score')) else None,
        'time_loss': float(ev_row.get('time_loss_estimate')) if pd.notna(ev_row.get('time_loss_estimate')) else None,
        'metrics': metrics,
        'description': ev_row.get('description')
    }


def compute_pace_stability_index(per_lap_racing, vehicle_id):
    """Compute how stable/consistent a driver's pace is (low = consistent)."""
    drv_laps = per_lap_racing[per_lap_racing['vehicle_id'] == vehicle_id].sort_values('lap')
    if len(drv_laps) < 2:
        return 0.0
    pace_delta = drv_laps['lap_time_seconds'].diff().dropna()
    if len(pace_delta) < 1:
        return 0.0
    # rolling std of pace changes (3-lap window)
    stability = pace_delta.rolling(3, min_periods=1).std().mean()
    return float(stability) if pd.notna(stability) else 0.0


def compute_cornering_confidence_index(telemetry, vehicle_id):
    """CCI = mean(|accy_can|) / sqrt(steering_variance)."""
    drv_tele = telemetry[telemetry['vehicle_id'] == vehicle_id]
    if drv_tele.empty:
        return 0.0
    # ensure numeric
    drv_tele = drv_tele.copy()
    drv_tele['accy_can'] = pd.to_numeric(drv_tele['accy_can'], errors='coerce')
    drv_tele['Steering_Angle'] = pd.to_numeric(drv_tele['Steering_Angle'], errors='coerce')
    
    mean_lat = drv_tele['accy_can'].abs().mean()
    steer_var = drv_tele['Steering_Angle'].var()
    if pd.isna(mean_lat) or pd.isna(steer_var) or steer_var <= 0:
        return 0.0
    cci = mean_lat / np.sqrt(steer_var)
    return float(cci) if pd.notna(cci) else 0.0


def compute_race_pressure_index(telemetry, per_lap_racing, vehicle_id, total_laps):
    """RPI = (pressure_late - pressure_mid) / pressure_mid."""
    drv_tele = telemetry[telemetry['vehicle_id'] == vehicle_id].copy()
    if drv_tele.empty:
        return 0.0
    drv_tele['lap'] = pd.to_numeric(drv_tele['lap'], errors='coerce')
    drv_tele['pbrake_f'] = pd.to_numeric(drv_tele['pbrake_f'], errors='coerce')
    drv_tele['Steering_Angle'] = pd.to_numeric(drv_tele['Steering_Angle'], errors='coerce')
    drv_tele['ath'] = pd.to_numeric(drv_tele['ath'], errors='coerce')
    
    mid_cutoff = total_laps // 2
    mid = drv_tele[drv_tele['lap'] <= mid_cutoff]
    late = drv_tele[drv_tele['lap'] > mid_cutoff]
    
    def pressure_metric(grp):
        brake = grp['pbrake_f'].sum() if 'pbrake_f' in grp.columns else 0
        steer = grp['Steering_Angle'].var() if 'Steering_Angle' in grp.columns else 0
        throttle_jitter = grp['ath'].diff().abs().sum() if 'ath' in grp.columns else 0
        return float(brake + (steer * 0.5 if pd.notna(steer) else 0) + (throttle_jitter * 0.2 if pd.notna(throttle_jitter) else 0))
    
    pressure_mid = pressure_metric(mid)
    pressure_late = pressure_metric(late)
    
    if pressure_mid <= 0:
        return 0.0
    rpi = (pressure_late - pressure_mid) / pressure_mid
    return float(rpi) if pd.notna(rpi) else 0.0


def compose_race_facts(per_lap, per_driver, events, telemetry):
    # Basic race info
    track = 'Road America'
    event_name = 'Road America Race 1'
    total_laps = int(per_lap['lap'].max()) if 'lap' in per_lap.columns else 0

    # Mark formation/out-laps: lap_time_seconds > 400
    per_lap['is_formation'] = per_lap['lap_time_seconds'].apply(lambda x: x > 400 if pd.notna(x) else False)
    # Filter to real racing laps for metrics
    per_lap_racing = per_lap[~per_lap['is_formation']].copy()

    # driver entries
    tags_map = tag_drivers(per_driver, per_lap_racing)

    drivers = []
    # per_driver may contain vehicle_number, start_pos, finish_pos
    for _, r in per_driver.iterrows():
        vid = r['vehicle_id']
        driver_metrics = {}
        # copy expected metrics, default to 0
        metrics_keys = ['lap_time_mean','lap_time_best','lap_time_std','max_speed_mean','peak_lat_g_mean','peak_long_g_mean','throttle_smoothness_mean','steering_variance_mean','brake_spikes_sum','gear_changes_sum']
        for k in metrics_keys:
            # map column names differences if necessary
            col = k
            if k not in r.index and k.replace('_mean','_mean') in r.index:
                col = k
            driver_metrics[k] = float(r[col]) if (k in r.index and pd.notna(r[col])) else 0.0

        # Recompute lap_time_mean and lap_time_std excluding formation laps (>400s)
        drv_racing_laps = per_lap_racing[per_lap_racing['vehicle_id'] == vid]['lap_time_seconds']
        if len(drv_racing_laps) > 0:
            driver_metrics['lap_time_mean'] = float(drv_racing_laps.mean())
            driver_metrics['lap_time_std'] = float(drv_racing_laps.std()) if len(drv_racing_laps) > 1 else 0.0
            driver_metrics['lap_time_best'] = float(drv_racing_laps.min())

        # lap times for this driver can be included in lap_times array; driver entry needs driver_key_events
        drv_events = []
        if not events.empty:
            evs = events[events['vehicle_id'] == vid]
            for _, evr in evs.iterrows():
                drv_events.append(event_to_object(evr))

        drivers.append({
            'vehicle_id': vid,
            'vehicle_number': r.get('vehicle_number') if 'vehicle_number' in r.index else None,
            'start_pos': int(r['start_pos']) if 'start_pos' in r.index and pd.notna(r['start_pos']) else None,
            'finish_pos': int(r['finish_pos']) if 'finish_pos' in r.index and pd.notna(r['finish_pos']) else None,
            'driver_metrics': driver_metrics,
            'driver_style_tags': tags_map.get(vid, []),
            'driver_key_events': drv_events,
            'pace_stability_index': compute_pace_stability_index(per_lap_racing, vid),
            'cornering_confidence_index': compute_cornering_confidence_index(telemetry, vid),
            'race_pressure_index': compute_race_pressure_index(telemetry, per_lap_racing, vid, total_laps)
        })

    # race_key_events: top events by severity or time_loss
    race_key_events = []
    if not events.empty:
        # sort by severity then time_loss
        evs_sorted = events.sort_values(['severity_score','time_loss_estimate'], ascending=[False, False]).reset_index(drop=True)
        topn = evs_sorted.head(6)
        # mark top as turning point, next 1-3 as major_mistakes
        if len(topn) > 0:
            tp = event_to_object(topn.iloc[0])
            tp['role'] = 'race_turning_point'
            race_key_events.append(tp)
            for i in range(1, min(4, len(topn))):
                em = event_to_object(topn.iloc[i])
                em['role'] = 'major_mistake'
                race_key_events.append(em)

    # lap_times array
    lap_times = []
    for _, r in per_lap.iterrows():
        is_form = r.get('is_formation', False)
        lap_times.append({
            'vehicle_id': r.get('vehicle_id'),
            'lap': int(r.get('lap')) if pd.notna(r.get('lap')) else None,
            'lap_time_seconds': float(r.get('lap_time_seconds')) if pd.notna(r.get('lap_time_seconds')) else None,
            'lap_type': 'formation' if is_form else 'racing'
        })

    out = {
        'race': {
            'event_name': event_name,
            'track': track,
            'total_laps': total_laps
        },
        'drivers': drivers,
        'race_key_events': race_key_events,
        'lap_times': lap_times
    }
    return out


def main():
    per_lap, per_driver, events, telemetry = load_inputs()
    # basic normalization of events
    if not events.empty:
        # ensure numeric
        events['severity_score'] = pd.to_numeric(events.get('severity_score', pd.Series()), errors='coerce') if 'severity_score' in events.columns else np.nan
        events['time_loss_estimate'] = pd.to_numeric(events.get('time_loss_estimate', pd.Series()), errors='coerce') if 'time_loss_estimate' in events.columns else np.nan
    race_obj = compose_race_facts(per_lap, per_driver, events, telemetry)

    # determine output filename using earliest lap start date
    if not per_lap.empty and 'start_time' in per_lap.columns:
        dt = pd.to_datetime(per_lap['start_time'].min())
        date_str = dt.strftime('%Y-%m-%d')
    else:
        date_str = pd.Timestamp.now().strftime('%Y-%m-%d')

    fname = f"race_facts_RoadAmerica_R1_{date_str}.json"
    out_path = OUT_DIR / fname
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(race_obj, f, indent=2)
    print('Wrote', out_path)


if __name__ == '__main__':
    main()
