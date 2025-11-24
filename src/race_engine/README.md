# Race Analysis Engine

Complete motorsports race analysis system with three core components:

1. **Analysis Engine** - Merges all race data into enriched JSON
2. **Sector Analysis** - Deep S1/S2/S3 strengths and fatigue detection
3. **What-If Simulator** - Recompute outcomes under different scenarios

## Architecture

```
src/race_engine/
├── __init__.py                    # Public API
├── analysis_engine.py             # Core merger of all race data
├── sector_analysis.py             # Sector performance analysis
├── classification_insights.py     # Results and pace analysis
├── what_if.py                     # Scenario simulation
└── integration_example.py         # End-to-end example
```

## Quick Start

### Basic Usage: Build Enriched Race Facts

```python
from race_engine import build_race_facts, load_results, load_sector_file
import pandas as pd

# Load data files
telemetry_clean = pd.read_csv("data/processed/telemetry_clean.csv")
per_lap_metrics = pd.read_csv("data/processed/per_lap_metrics.csv")
per_driver_metrics = pd.read_csv("data/processed/per_driver_metrics.csv")
event_detection = pd.read_csv("data/processed/event_detection.csv")
lap_times = per_lap_metrics[["vehicle_id", "lap", "lap_time_seconds"]]

results_df = load_results("data/raw/results/03_Results_*.csv")
sector_df = load_sector_file("data/raw/sectors/23_Analysis*.csv")

# Build enriched JSON
race_facts = build_race_facts(
    race_name="Road America R1",
    track_name="Road America",
    telemetry_clean=telemetry_clean,
    per_lap_metrics=per_lap_metrics,
    per_driver_metrics=per_driver_metrics,
    event_detection=event_detection,
    lap_times=lap_times,
    results_df=results_df,
    sector_df=sector_df,
)

import json
with open("race_facts.json", "w") as f:
    json.dump(race_facts, f, indent=2)
```

### Sector Analysis

Each driver gets detailed sector insights:

```python
from race_engine import build_sector_analysis

sector_summary, per_driver_sector = build_sector_analysis(sector_df, results_df)

# Access insights for a driver
driver_insights = per_driver_sector["GR86-026-72"]
print(driver_insights)
# Output:
# {
#     "sector_means": {"S1": 35.2, "S2": 42.1, "S3": 38.9},
#     "sector_losses_vs_best": {"S1_loss_vs_best": 1.2, "S2_loss_vs_best": 2.3, "S3_loss_vs_best": 0.8},
#     "strongest_sector": "S3",
#     "weakest_sector": "S2",
#     "fatigue_indicator_percent": 2.5,  # positive = degrading through race
#     "sector_consistency": {"S1": 0.45, "S2": 0.62, "S3": 0.51}
# }
```

### What-If Scenarios

#### Scenario 1: Remove All Incidents for a Driver

```python
from race_engine import simulate_no_events, filter_events_for_removal, build_what_if_payload

# Filter events for a specific driver
driver_events = filter_events_for_removal(
    event_detection,
    vehicle_id="GR86-026-72"
)

# Simulate without those events
adjusted = simulate_no_events(lap_times, event_detection, driver_events, results_df)

# Build LLM payload
payload = build_what_if_payload(
    "GR86-026-72",
    "Remove all incidents for this driver",
    original_results=pd.DataFrame([
        # ... original race results
    ]),
    adjusted_results=adjusted
)

print(json.dumps(payload, indent=2))
# Output:
# {
#     "scenario": "Remove all incidents for this driver",
#     "driver_id": "GR86-026-72",
#     "original_time_seconds": 1234.5,
#     "adjusted_time_seconds": 1210.3,
#     "time_gain_seconds": 24.2,
#     "time_gain_percent": 1.96,
#     "original_position": 7,
#     "adjusted_position": 5,
#     "position_change": 2,
#     "result_improvement": "improved"
# }
```

#### Scenario 2: Remove Only Race Turning Points

```python
from race_engine import simulate_event_removal_by_role

# Simulate removing only events marked as turning points
results = simulate_event_removal_by_role(
    lap_times,
    event_detection,
    results_df,
    role="race_turning_point"
)

# results = {
#     "GR86-026-72": {...payload...},
#     "GR86-002-2": {...payload...},
#     ...
# }
```

#### Scenario 3: Compare Multiple Scenarios

```python
from race_engine import compare_scenarios

# Build several adjusted result sets
no_understeer = simulate_no_events(
    lap_times,
    event_detection,
    filter_events_for_removal(event_detection, event_type="understeer"),
    results_df
)

no_lockups = simulate_no_events(
    lap_times,
    event_detection,
    filter_events_for_removal(event_detection, event_type="lockup"),
    results_df
)

# Compare them
comparison = compare_scenarios(
    {
        "No Understeer": no_understeer,
        "No Lockups": no_lockups,
    },
    driver_id="GR86-026-72"
)

print(json.dumps(comparison, indent=2))
# Output:
# {
#     "driver_id": "GR86-026-72",
#     "scenarios": {
#         "No Understeer": {
#             "total_time": 1210.3,
#             "position": 5,
#             "time_gain": 24.2
#         },
#         "No Lockups": {
#             "total_time": 1215.8,
#             "position": 6,
#             "time_gain": 18.7
#         }
#     }
# }
```

## Enriched race_facts JSON Structure

```json
{
  "race": {
    "event_name": "Road America R1",
    "track": "Road America",
    "total_laps": 8
  },
  "drivers": [
    {
      "vehicle_id": "GR86-026-72",
      "vehicle_number": 26,
      "finish_pos": 5,
      "driver_metrics": {
        "lap_time_mean": 162.5,
        "lap_time_best": 159.2,
        "max_speed_mean": 191.3,
        "peak_lat_G_mean": 0.95,
        "steering_variance_mean": 643.2,
        "brake_spikes_sum": 5680.0
      },
      "driver_style_tags": ["aggressive_braking", "smooth_steering"],
      "driver_key_events": [
        {
          "event_type": "understeer",
          "lap": 4,
          "timestamp": "2025-08-15T00:09:40.087000+00:00",
          "severity": 1.0,
          "time_loss": 0.88,
          "metrics": {
            "steering_correction_deg": 30.2,
            "latG_spike": 0.095,
            "speed_loss_kph": 7.91
          }
        }
      ],
      "sector_insights": {
        "sector_means": {"S1": 35.2, "S2": 42.1, "S3": 38.9},
        "sector_losses_vs_best": {"S1_loss_vs_best": 1.2, "S2_loss_vs_best": 2.3, "S3_loss_vs_best": 0.8},
        "strongest_sector": "S3",
        "weakest_sector": "S2",
        "fatigue_indicator_percent": 2.5
      },
      "classification_insights": {
        "position": 5,
        "laps_completed": 8,
        "class": "GR86",
        "peak_pace_best3_seconds": 159.2,
        "status": "Finished"
      }
    }
  ],
  "race_key_events": [...],
  "lap_times": [...],
  "weather_summary": {
    "air_temp_mean": 25.3,
    "track_temp_mean": 42.1,
    "humidity_mean": 65.0,
    "rain_flag": false
  },
  "sector_summary": {
    "best_S1": {"vehicle": "GR86-004-78", "time": 34.1},
    "best_S2": {"vehicle": "GR86-002-2", "time": 39.9},
    "best_S3": {"vehicle": "GR86-021-86", "time": 38.2}
  },
  "classification_summary": {
    "num_starters": 27,
    "winner_vehicle": "GR86-004-78",
    "fastest_lap_vehicle": "GR86-002-2",
    "fastest_lap_time_seconds": 159.1
  },
  "what_if_base": {
    "total_time_seconds": {
      "GR86-026-72": 1234.5,
      "GR86-002-2": 1198.3,
      ...
    },
    "total_event_loss_seconds": {
      "GR86-026-72": 24.2,
      "GR86-002-2": 15.7,
      ...
    }
  }
}
```

## LLM Integration Patterns

### Post-Race Analysis
```python
# Send full race_facts to analysis LLM
analysis_prompt = f"""
Analyze this race using the enriched race_facts:

{json.dumps(race_facts, indent=2)}

Provide:
1. Race winners and top performers
2. Driver consistency analysis by sector
3. Incidents that shaped the race
4. Weather impact on driver performance
5. Strategic insights (pacing, fatigue, overtaking opportunities)
"""
```

### What-If Analysis
```python
# Send focused scenario to what-if LLM
whatif_prompt = f"""
You are the Race Strategy Scenario AI.

What-if Scenario:
{json.dumps(payload, indent=2)}

Explain:
1. How this changes the driver's race result
2. Psychological and strategic implications
3. Whether this driver had realistic potential for this position
4. Sector-level changes needed to achieve this scenario
"""
```

## Input Data Requirements

| File | Purpose | Key Columns |
|------|---------|-------------|
| `per_lap_metrics.csv` | Lap aggregates | vehicle_id, lap, lap_time_seconds |
| `per_driver_metrics.csv` | Driver aggregates | vehicle_id, lap_time_mean, max_speed_mean, etc. |
| `event_detection.csv` | Race incidents | vehicle_id, lap, event_type, time_loss_estimate |
| `telemetry_clean.csv` | Raw vehicle data | vehicle_id, lap, timestamp, speed, accel, etc. |
| `03_*Results*.csv` | Official results | NUMBER, VEHICLE, POSITION, FL_TIME, LAPS |
| `23_*Sections*.csv` | Sector times | NUMBER, LAP_NUMBER, S1, S2, S3 |
| `26_Weather*.csv` | Weather data | AIR_TEMP, TRACK_TEMP, HUMIDITY, RAIN |
| `99_Best10*.csv` | Best laps | NUMBER, BESTLAP_1...BESTLAP_10 |

## API Reference

### Core Functions

- `build_race_facts()` - Main integration function
- `build_sector_analysis()` - Sector insights
- `build_classification_insights()` - Results analysis
- `simulate_no_events()` - What-if simulation
- `filter_events_for_removal()` - Event filtering
- `build_what_if_payload()` - LLM-ready payload

### Data Classes

- `Event` - Single race incident
- `DriverRaceSummary` - Complete driver analysis
- `RaceFacts` - Complete race output

## Testing

```python
# Run integration example
python -m race_engine.integration_example

# Or programmatically
from race_engine.integration_example import build_enriched_race_facts_from_files
json_file = build_enriched_race_facts_from_files("data/processed", "data/output")
```

## Performance Notes

- Full race_facts JSON: ~2-5 MB for 20-30 drivers
- Sector analysis: O(n_drivers * n_laps)
- What-if simulation: O(n_drivers) - very fast
- Recommended: Compute once at race end, cache JSON, use for multiple LLM queries

## Future Enhancements

- [ ] Tire strategy simulation
- [ ] Fuel load analysis
- [ ] Live telemetry streaming
- [ ] Real-time incident detection
- [ ] Multi-race season analysis
- [ ] Driver comparison matrix
