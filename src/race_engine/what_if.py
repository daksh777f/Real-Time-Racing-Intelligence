"""
What-If Simulator - recompute race outcomes under different scenarios
"""

from typing import Optional, Dict, Any
import pandas as pd
import numpy as np


def simulate_no_events(
    lap_times: pd.DataFrame,
    event_detection: pd.DataFrame,
    events_to_remove: Optional[pd.DataFrame] = None,
    results_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Simulate race with events removed/modified.
    
    Returns DataFrame with:
        vehicle_id, real_total_time, total_event_loss, adj_total_time, 
        real_position, adj_position, position_gain_loss
        
    Args:
        lap_times: DataFrame with vehicle_id, lap, lap_time_seconds
        event_detection: DataFrame with vehicle_id, time_loss_estimate (or time_loss)
        events_to_remove: Optional filter - only remove these events
        results_df: Optional original race results for position mapping
        
    Returns:
        DataFrame with original and adjusted race standings
    """
    lt = lap_times.copy()
    
    # Compute real total times
    if "vehicle_id" in lt.columns and "lap_time_seconds" in lt.columns:
        totals = lt.groupby("vehicle_id")["lap_time_seconds"].sum().rename("real_total_time")
    else:
        return pd.DataFrame()

    # Compute event losses
    ev = event_detection.copy() if not event_detection.empty else pd.DataFrame()
    
    if not ev.empty and events_to_remove is not None:
        # keep only events we want to remove
        if "event_id" in events_to_remove.columns:
            ev = ev.merge(
                events_to_remove[["event_id"]],
                on="event_id",
                how="inner",
            )
        else:
            # fallback: merge on vehicle_id + event_type or similar
            ev = ev.merge(
                events_to_remove,
                on=list(set(ev.columns) & set(events_to_remove.columns)),
                how="inner",
            )

    if not ev.empty and "vehicle_id" in ev.columns:
        if "time_loss_estimate" in ev.columns:
            tl = ev.groupby("vehicle_id")["time_loss_estimate"].sum()
        elif "time_loss" in ev.columns:
            tl = ev.groupby("vehicle_id")["time_loss"].sum()
        else:
            tl = pd.Series(dtype=float)
        tl = tl.rename("total_event_loss")
    else:
        tl = pd.Series(dtype=float)

    # Merge into one DataFrame
    df = totals.to_frame().join(tl, how="left").fillna({"total_event_loss": 0.0})
    df["adj_total_time"] = df["real_total_time"] - df["total_event_loss"]

    # Compute adjusted positions (lower time = better rank)
    df = df.sort_values("adj_total_time").reset_index()
    df["adj_position"] = np.arange(1, len(df) + 1)

    # Add real positions from results if provided
    if results_df is not None and not results_df.empty:
        res = results_df.copy()
        res.columns = [c.strip().upper() for c in res.columns]
        
        if "VEHICLE" in res.columns and "POSITION" in res.columns:
            pos_map = {row["VEHICLE"]: row["POSITION"] for _, row in res.iterrows()}
            df["real_position"] = df["vehicle_id"].map(pos_map)
        else:
            df["real_position"] = np.nan
    else:
        # Assume order in lap_times is finishing order
        df["real_position"] = np.nan

    # Compute position change
    df["position_change"] = df["real_position"] - df["adj_position"]  # positive = improved

    return df


def filter_events_for_removal(
    event_detection: pd.DataFrame,
    vehicle_id: Optional[str] = None,
    event_type: Optional[str] = None,
    role: Optional[str] = None,
) -> pd.DataFrame:
    """
    Filter events to identify which ones to remove in what-if scenarios.
    
    Args:
        event_detection: Full events DataFrame
        vehicle_id: Filter by specific vehicle (e.g., "GR86-026-72")
        event_type: Filter by event type (e.g., "understeer", "lockup")
        role: Filter by role (e.g., "race_turning_point", "major_mistake")
        
    Returns:
        Filtered DataFrame ready for simulate_no_events
    """
    df = event_detection.copy()
    
    if vehicle_id is not None and "vehicle_id" in df.columns:
        df = df[df["vehicle_id"] == vehicle_id]
    
    if event_type is not None and "event_type" in df.columns:
        df = df[df["event_type"] == event_type]
    
    if role is not None and "role" in df.columns:
        df = df[df["role"] == role]
    
    return df


def build_what_if_payload(
    driver_id: str,
    scenario_label: str,
    original_results: pd.DataFrame,
    adjusted_results: pd.DataFrame,
) -> Dict[str, Any]:
    """
    Build a structured payload for LLM what-if analysis.
    
    Args:
        driver_id: Vehicle ID to analyze
        scenario_label: Description of the what-if scenario
        original_results: Results from simulate_no_events with original times
        adjusted_results: Results from simulate_no_events with events removed
        
    Returns:
        Dictionary ready for JSON/LLM prompt
        
    Raises:
        ValueError: If driver_id not found in results
    """
    orig = original_results.set_index("vehicle_id")
    adj = adjusted_results.set_index("vehicle_id")

    if driver_id not in orig.index:
        raise ValueError(f"driver_id {driver_id} not found in original results")
    if driver_id not in adj.index:
        raise ValueError(f"driver_id {driver_id} not found in adjusted results")

    o = orig.loc[driver_id]
    a = adj.loc[driver_id]

    gain = o["real_total_time"] - a["adj_total_time"]
    
    try:
        orig_pos = int(o.get("real_position", a.get("adj_position", 0)))
    except (ValueError, TypeError):
        orig_pos = int(o.get("adj_position", 0))
    
    try:
        adj_pos = int(a["adj_position"])
    except (ValueError, TypeError):
        adj_pos = 0
    
    pos_change = orig_pos - adj_pos if orig_pos > 0 and adj_pos > 0 else None

    return {
        "scenario": scenario_label,
        "driver_id": driver_id,
        "original_time_seconds": float(o["real_total_time"]),
        "adjusted_time_seconds": float(a["adj_total_time"]),
        "time_gain_seconds": float(gain),
        "time_gain_percent": float((gain / o["real_total_time"] * 100)) if o["real_total_time"] > 0 else 0.0,
        "original_position": orig_pos,
        "adjusted_position": adj_pos,
        "position_change": pos_change,
        "result_improvement": "improved" if pos_change and pos_change > 0 else ("unchanged" if pos_change == 0 else "declined"),
    }


def simulate_event_removal_by_role(
    lap_times: pd.DataFrame,
    event_detection: pd.DataFrame,
    results_df: pd.DataFrame,
    role: str,
) -> Dict[str, Any]:
    """
    Simulate removing all events with a specific role (e.g., all turning points).
    
    Args:
        lap_times: Lap times DataFrame
        event_detection: Events DataFrame
        results_df: Original results
        role: Role to filter (e.g., "race_turning_point")
        
    Returns:
        Dictionary with vehicle_id -> what-if payload for each affected driver
    """
    events_to_remove = filter_events_for_removal(event_detection, role=role)
    
    if events_to_remove.empty:
        return {}
    
    adjusted = simulate_no_events(lap_times, event_detection, events_to_remove, results_df)
    
    result = {}
    affected_vehicles = events_to_remove["vehicle_id"].unique()
    
    for vid in affected_vehicles:
        try:
            payload = build_what_if_payload(
                str(vid),
                f"Remove all {role} events",
                pd.DataFrame([
                    {
                        "vehicle_id": vid,
                        "real_total_time": float(lap_times[lap_times["vehicle_id"] == vid]["lap_time_seconds"].sum()),
                        "adj_position": 0,
                    }
                ]),
                adjusted[adjusted["vehicle_id"] == vid],
            )
            result[str(vid)] = payload
        except Exception:
            continue
    
    return result


def compare_scenarios(
    scenarios: Dict[str, pd.DataFrame],
    driver_id: str,
) -> Dict[str, Any]:
    """
    Compare multiple what-if scenarios for a single driver.
    
    Args:
        scenarios: Dict mapping scenario_name -> adjusted_results DataFrame
        driver_id: Driver to compare across scenarios
        
    Returns:
        Comparative analysis dictionary
    """
    comparison = {}
    
    for scenario_name, results_df in scenarios.items():
        try:
            row = results_df[results_df["vehicle_id"] == driver_id].iloc[0]
            comparison[scenario_name] = {
                "total_time": float(row.get("adj_total_time", 0)),
                "position": int(row.get("adj_position", 0)),
                "time_gain": float(row.get("total_event_loss", 0)),
            }
        except (IndexError, KeyError, ValueError):
            continue
    
    return {
        "driver_id": driver_id,
        "scenarios": comparison,
    }
