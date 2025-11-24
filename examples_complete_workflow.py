"""
Complete Workflow Example - Integration of All Analysis Systems

Demonstrates end-to-end integration of:
    1. Analysis Engine - Build enriched race_facts JSON
    2. Sector Analysis - Deep performance insights by track section
    3. What-If Simulator - Scenario analysis and counterfactuals

Usage:
    python examples_complete_workflow.py [data_dir] [output_dir]
    
Example:
    python examples_complete_workflow.py data/processed data/output
    
Output:
    - race_facts.json
    - sector_analysis.json
    - what_if_scenarios.json
    - analysis_report.txt
"""

import json
import sys
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from race_engine import (
    build_race_facts,
    load_results,
    load_class_results,
    load_sector_file,
    load_weather,
    load_best10,
)
from race_engine.what_if import (
    simulate_no_events,
    filter_events_for_removal,
    build_what_if_payload,
    simulate_event_removal_by_role,
    compare_scenarios,
)


def demo_analysis_engine(data_path: Path) -> dict:
    """
    System 1: Analysis Engine - Merge all data into enriched JSON
    """
    print("\n" + "="*70)
    print("SYSTEM 1: ANALYSIS ENGINE")
    print("="*70)

    print("\n1.1 Loading data files...")
    
    telemetry = pd.read_csv(data_path / "telemetry_clean.csv")
    per_lap = pd.read_csv(data_path / "per_lap_metrics.csv")
    per_driver = pd.read_csv(data_path / "per_driver_metrics.csv")
    events = pd.read_csv(data_path / "event_detection.csv")
    
    # Derive lap times
    lap_times = per_lap[["vehicle_id", "lap", "lap_time_seconds"]].copy()
    lap_times = lap_times.dropna(subset=["lap_time_seconds"])
    
    print(f"   Telemetry: {len(telemetry)} rows")
    print(f"   Per-lap metrics: {len(per_lap)} rows")
    print(f"   Per-driver metrics: {len(per_driver)} rows")
    print(f"   Events detected: {len(events)} rows")
    print(f"   Lap times: {len(lap_times)} rows")

    # Load optional files
    print("\n1.2 Loading optional classification files...")
    results_df = pd.DataFrame()
    sector_df = pd.DataFrame()
    
    results_files = list(data_path.glob("*03*Results*.CSV"))
    if results_files:
        try:
            results_df = load_results(str(results_files[0]))
            print(f"   Results: {len(results_df)} drivers")
        except Exception as e:
            print(f"   Results: Failed ({e})")

    sector_files = list(data_path.glob("*23*Analysis*.CSV"))
    if sector_files:
        try:
            sector_df = load_sector_file(str(sector_files[0]))
            print(f"   Sector file: {len(sector_df)} records")
        except Exception as e:
            print(f"   Sector file: Failed ({e})")

    # Build enriched race facts
    print("\n1.3 Building enriched race_facts...")
    race_facts = build_race_facts(
        race_name="Road America R1",
        track_name="Road America",
        telemetry_clean=telemetry,
        per_lap_metrics=per_lap,
        per_driver_metrics=per_driver,
        event_detection=events,
        lap_times=lap_times,
        results_df=results_df,
        sector_df=sector_df,
    )

    print(f"   ✓ Built race_facts:")
    print(f"     - {len(race_facts['drivers'])} drivers")
    print(f"     - {len(race_facts['race_key_events'])} race-level events")
    print(f"     - {sum(len(d['driver_key_events']) for d in race_facts['drivers'])} driver events")
    print(f"     - {len(race_facts['lap_times'])} lap time records")
    
    return race_facts


def demo_sector_analysis(race_facts: dict) -> None:
    """
    System 2: Sector Analysis - Deep S1/S2/S3 insights
    """
    print("\n" + "="*70)
    print("SYSTEM 2: SECTOR ANALYSIS")
    print("="*70)

    print("\n2.1 Sector insights for all drivers:")
    
    drivers_with_sectors = [d for d in race_facts['drivers'] if d.get('sector_insights')]
    
    if drivers_with_sectors:
        print(f"\n   Found {len(drivers_with_sectors)} drivers with sector data\n")
        
        for i, driver in enumerate(drivers_with_sectors[:5]):  # Show top 5
            print(f"   {i+1}. {driver['vehicle_id']}")
            sector = driver.get('sector_insights', {})
            
            if sector.get('sector_means'):
                means = sector['sector_means']
                print(f"      Sector times: S1={means.get('S1', 'N/A'):.2f}s, "
                      f"S2={means.get('S2', 'N/A'):.2f}s, S3={means.get('S3', 'N/A'):.2f}s")
            
            print(f"      Strongest: {sector.get('strongest_sector', 'N/A')}")
            print(f"      Weakest: {sector.get('weakest_sector', 'N/A')}")
            
            fatigue = sector.get('fatigue_indicator_percent', 0)
            status = "degrading" if fatigue > 0 else "improving"
            print(f"      Fatigue indicator: {fatigue:+.1f}% ({status})\n")
    else:
        print("   (No sector data available in this race_facts)")


def demo_what_if_simulator(data_path: Path, race_facts: dict) -> None:
    """
    System 3: What-If Simulator - Scenario analysis
    """
    print("\n" + "="*70)
    print("SYSTEM 3: WHAT-IF SIMULATOR")
    print("="*70)

    # Reload data for what-if (need raw DataFrames)
    print("\n3.1 Loading data for what-if scenarios...")
    per_lap = pd.read_csv(data_path / "per_lap_metrics.csv")
    events = pd.read_csv(data_path / "event_detection.csv")
    lap_times = per_lap[["vehicle_id", "lap", "lap_time_seconds"]].copy()
    lap_times = lap_times.dropna(subset=["lap_time_seconds"])
    
    results_files = list(data_path.glob("*03*Results*.CSV"))
    results_df = pd.DataFrame()
    if results_files:
        try:
            results_df = load_results(str(results_files[0]))
        except Exception:
            pass

    # Scenario 1: Remove all events for a driver
    print("\n3.2 Scenario 1: Remove all incidents for a specific driver")
    
    # Pick a driver with events
    drivers_with_events = events['vehicle_id'].unique()
    if len(drivers_with_events) > 0:
        target_driver = str(drivers_with_events[0])
        print(f"     Target: {target_driver}")
        
        driver_events = filter_events_for_removal(events, vehicle_id=target_driver)
        print(f"     Events to remove: {len(driver_events)}")
        
        if len(driver_events) > 0:
            adjusted = simulate_no_events(lap_times, events, driver_events, results_df)
            print(f"     Adjusted standings: {len(adjusted)} drivers reranked")
            
            try:
                # Find this driver in adjusted results
                if target_driver in adjusted['vehicle_id'].values:
                    payload = build_what_if_payload(
                        target_driver,
                        f"Remove all incidents for {target_driver}",
                        # Create a simple original comparison
                        pd.DataFrame([
                            {
                                'vehicle_id': target_driver,
                                'real_total_time': lap_times[lap_times['vehicle_id'] == target_driver]['lap_time_seconds'].sum(),
                                'adj_position': 0,
                            }
                        ]),
                        adjusted,
                    )
                    
                    print(f"\n     What-if payload:")
                    print(f"       Original time: {payload['original_time_seconds']:.1f}s")
                    print(f"       Adjusted time: {payload['adjusted_time_seconds']:.1f}s")
                    print(f"       Time gain: {payload['time_gain_seconds']:.1f}s ({payload['time_gain_percent']:.2f}%)")
                    print(f"       Position change: {payload['position_change']} ({payload['result_improvement']})")
            except Exception as e:
                print(f"     (Could not build payload: {e})")

    # Scenario 2: Remove events by type
    print("\n3.3 Scenario 2: Remove all understeer events")
    
    understeer_events = filter_events_for_removal(events, event_type="understeer")
    print(f"     Total understeer events: {len(understeer_events)}")
    
    if len(understeer_events) > 0:
        adjusted_no_us = simulate_no_events(lap_times, events, understeer_events, results_df)
        
        affected_drivers = understeer_events['vehicle_id'].unique()[:3]
        print(f"\n     Affected drivers (showing first 3):")
        
        for driver in affected_drivers:
            try:
                if driver in adjusted_no_us['vehicle_id'].values:
                    row = adjusted_no_us[adjusted_no_us['vehicle_id'] == driver].iloc[0]
                    gain = row.get('total_event_loss', 0)
                    print(f"       {driver}: {gain:.2f}s potential gain")
            except Exception:
                pass

    # Scenario 3: Compare multiple scenarios
    print("\n3.4 Scenario 3: Compare multiple event removal scenarios")
    
    scenarios = {}
    event_types = ["understeer", "lockup"]
    
    for et in event_types:
        events_filter = filter_events_for_removal(events, event_type=et)
        if len(events_filter) > 0:
            scenarios[f"No {et}"] = simulate_no_events(lap_times, events, events_filter, results_df)
            print(f"     ✓ {et}: {len(events_filter)} events")

    if len(scenarios) >= 2 and len(drivers_with_events) > 0:
        driver = str(drivers_with_events[0])
        print(f"\n     Comparing scenarios for {driver}:")
        
        from race_engine.what_if import compare_scenarios
        try:
            comp = compare_scenarios(scenarios, driver)
            for scenario_name, metrics in comp.get('scenarios', {}).items():
                print(f"       {scenario_name}:")
                print(f"         Time: {metrics.get('total_time', 0):.1f}s")
                print(f"         Position: {metrics.get('position', 0)}")
        except Exception as e:
            print(f"       (Comparison failed: {e})")


def main():
    """Main demo runner"""
    if len(sys.argv) < 2:
        print("Usage: python demo_complete_system.py <data_dir> [output_dir]")
        print("\nExample:")
        print("  python demo_complete_system.py data/processed data/output")
        sys.exit(1)

    data_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/output")

    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*70)
    print("RACE ANALYSIS ENGINE - COMPLETE SYSTEM DEMO")
    print("="*70)
    print(f"Data directory: {data_dir}")
    print(f"Output directory: {output_dir}")

    # Run all three systems
    race_facts = demo_analysis_engine(data_dir)
    demo_sector_analysis(race_facts)
    demo_what_if_simulator(data_dir, race_facts)

    # Save outputs
    print("\n" + "="*70)
    print("SAVING OUTPUTS")
    print("="*70)

    output_file = output_dir / "race_facts_complete.json"
    with open(output_file, "w") as f:
        json.dump(race_facts, f, indent=2)
    print(f"\n✓ Saved complete race_facts: {output_file}")
    print(f"  Size: {output_file.stat().st_size / 1024:.1f} KB")

    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print("\nYou can now:")
    print("1. Load race_facts.json and send to LLM analysis")
    print("2. Use what-if payloads for scenario-based LLM queries")
    print("3. Integrate into your chatbot/agent system")


if __name__ == "__main__":
    main()
