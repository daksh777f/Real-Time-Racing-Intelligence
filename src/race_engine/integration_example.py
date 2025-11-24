"""
Integration example - Load all data and build enriched race_facts JSON
"""

import json
from pathlib import Path
import pandas as pd
from race_engine import (
    build_race_facts,
    load_results,
    load_class_results,
    load_sector_file,
    load_weather,
    load_best10,
)


def build_enriched_race_facts_from_files(
    data_dir: str,
    output_dir: str,
    race_name: str = "Road America R1",
    track_name: str = "Road America",
) -> str:
    """
    Load all race data files and build enriched JSON.
    
    Args:
        data_dir: Directory containing processed CSV files
        output_dir: Directory to save output JSON
        race_name: Name of race event
        track_name: Name of track
        
    Returns:
        Path to generated JSON file
    """
    data_path = Path(data_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Loading data from {data_dir}...")

    # Load core processed files
    try:
        telemetry_clean = pd.read_csv(data_path / "telemetry_clean.csv")
        print(f"  ✓ telemetry_clean: {len(telemetry_clean)} rows")
    except FileNotFoundError:
        print("  ✗ telemetry_clean.csv not found")
        telemetry_clean = pd.DataFrame()

    try:
        per_lap_metrics = pd.read_csv(data_path / "per_lap_metrics.csv")
        print(f"  ✓ per_lap_metrics: {len(per_lap_metrics)} rows")
    except FileNotFoundError:
        print("  ✗ per_lap_metrics.csv not found")
        per_lap_metrics = pd.DataFrame()

    try:
        per_driver_metrics = pd.read_csv(data_path / "per_driver_metrics.csv")
        print(f"  ✓ per_driver_metrics: {len(per_driver_metrics)} rows")
    except FileNotFoundError:
        print("  ✗ per_driver_metrics.csv not found")
        per_driver_metrics = pd.DataFrame()

    try:
        event_detection = pd.read_csv(data_path / "event_detection.csv")
        print(f"  ✓ event_detection: {len(event_detection)} rows")
    except FileNotFoundError:
        print("  ✗ event_detection.csv not found")
        event_detection = pd.DataFrame()

    # Derive lap_times from per_lap_metrics if available
    if not per_lap_metrics.empty:
        try:
            lap_times = per_lap_metrics[["vehicle_id", "lap", "lap_time_seconds"]].copy()
            lap_times = lap_times.dropna(subset=["lap_time_seconds"])
            print(f"  ✓ lap_times (derived): {len(lap_times)} rows")
        except Exception:
            lap_times = pd.DataFrame()
    else:
        lap_times = pd.DataFrame()

    # Load results/classification files
    results_df = pd.DataFrame()
    class_results_df = pd.DataFrame()
    sector_df = pd.DataFrame()
    weather_df = pd.DataFrame()
    best10_df = pd.DataFrame()

    # Find and load results file (03_*)
    results_files = list(data_path.glob("*03*Provisional*Results*.CSV")) + \
                    list(data_path.glob("*03*Results*Official*.CSV"))
    if results_files:
        try:
            results_df = load_results(str(results_files[0]))
            print(f"  ✓ results: {len(results_df)} rows")
        except Exception as e:
            print(f"  ✗ results failed: {e}")

    # Find and load class results (05_*)
    class_files = list(data_path.glob("*05*Results*Class*.CSV"))
    if class_files:
        try:
            class_results_df = load_class_results(str(class_files[0]))
            print(f"  ✓ class_results: {len(class_results_df)} rows")
        except Exception as e:
            print(f"  ✗ class_results failed: {e}")

    # Find and load sector file (23_*)
    sector_files = list(data_path.glob("*23*AnalysisEnduranceWithSections*.CSV"))
    if sector_files:
        try:
            sector_df = load_sector_file(str(sector_files[0]))
            print(f"  ✓ sector_file: {len(sector_df)} rows")
        except Exception as e:
            print(f"  ✗ sector_file failed: {e}")

    # Find and load weather (26_*)
    weather_files = list(data_path.glob("*26*Weather*.CSV"))
    if weather_files:
        try:
            weather_df = load_weather(str(weather_files[0]))
            print(f"  ✓ weather: {len(weather_df)} rows")
        except Exception as e:
            print(f"  ✗ weather failed: {e}")

    # Find and load best 10 laps (99_*)
    best10_files = list(data_path.glob("*99*Best*10*.CSV"))
    if best10_files:
        try:
            best10_df = load_best10(str(best10_files[0]))
            print(f"  ✓ best10_laps: {len(best10_df)} rows")
        except Exception as e:
            print(f"  ✗ best10_laps failed: {e}")

    print("\nBuilding enriched race_facts...")
    race_facts = build_race_facts(
        race_name=race_name,
        track_name=track_name,
        telemetry_clean=telemetry_clean,
        per_lap_metrics=per_lap_metrics,
        per_driver_metrics=per_driver_metrics,
        event_detection=event_detection,
        lap_times=lap_times,
        results_df=results_df,
        class_results_df=class_results_df,
        sector_df=sector_df,
        weather_df=weather_df,
        best10_df=best10_df,
    )

    # Save to JSON
    output_file = output_path / f"race_facts_{track_name.replace(' ', '_')}_enriched.json"
    with open(output_file, "w") as f:
        json.dump(race_facts, f, indent=2)
    
    print(f"\n✓ Saved to {output_file}")
    print(f"  Drivers: {len(race_facts['drivers'])}")
    print(f"  Race events: {len(race_facts['race_key_events'])}")
    print(f"  Lap records: {len(race_facts['lap_times'])}")

    return str(output_file)


if __name__ == "__main__":
    # Example: build from your processed data directory
    data_dir = "data/processed"
    output_dir = "data/output"
    
    json_file = build_enriched_race_facts_from_files(
        data_dir=data_dir,
        output_dir=output_dir,
    )
    print(f"\nEnriched race_facts ready: {json_file}")
