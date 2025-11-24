"""
Classification Insights - race results, class standings, best lap analysis
"""

from typing import Tuple, Dict, Any
import pandas as pd
import numpy as np


def time_str_to_seconds(t: str) -> float:
    """
    Convert time string like '2:10.345' or '01:32.678' to seconds.
    
    Args:
        t: Time string in various formats
        
    Returns:
        Time in seconds as float
    """
    if isinstance(t, (int, float)):
        return float(t)
    
    t = str(t).strip()
    if ":" not in t:
        # Already a number
        return float(t.replace(",", "."))
    
    parts = t.replace(",", ".").split(":")
    if len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    elif len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    else:
        # Fallback: try to parse the last part
        return float(parts[-1])


def build_classification_insights(
    results_df: pd.DataFrame,
    class_results_df: pd.DataFrame,
    best10_df: pd.DataFrame,
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    """
    Extract classification insights from results and best lap data.
    
    Args:
        results_df: Main results DataFrame with POSITION, VEHICLE, FL_TIME, GAP_FIRST, etc.
        class_results_df: Optional class results
        best10_df: Optional best 10 laps by driver (99_Best 10 Laps)
        
    Returns:
        classification_summary: dict with overall race winner, fastest lap
        per_driver_class: dict mapping vehicle_id -> insights including peak pace, position, class, etc.
    """
    
    res = results_df.copy()
    res.columns = [c.strip().upper() for c in res.columns]

    best10 = best10_df.copy() if not best10_df.empty else pd.DataFrame()
    if not best10.empty:
        best10.columns = [c.strip().upper() for c in best10.columns]

    # map NUMBER -> VEHICLE
    num_to_vehicle = {}
    if "NUMBER" in res.columns and "VEHICLE" in res.columns:
        num_to_vehicle = {row["NUMBER"]: row["VEHICLE"] for _, row in res.iterrows()}

    # ---------- Overall summary ----------
    classification_summary = {}
    
    if not res.empty:
        if "POSITION" in res.columns:
            winner = res.sort_values("POSITION").iloc[0]
            classification_summary["winner_vehicle"] = str(winner.get("VEHICLE", "unknown"))
        
        if "FL_TIME" in res.columns:
            # find fastest lap (might be string or float)
            fl_col = res["FL_TIME"]
            fl_col_numeric = pd.to_numeric(fl_col, errors="coerce")
            if fl_col_numeric.notna().any():
                fastest_idx = fl_col_numeric.idxmin()
                fastest = res.loc[fastest_idx]
                classification_summary["fastest_lap_vehicle"] = str(fastest.get("VEHICLE", "unknown"))
                classification_summary["fastest_lap_time_str"] = str(fastest.get("FL_TIME", "unknown"))
                try:
                    classification_summary["fastest_lap_time_seconds"] = float(fl_col_numeric.min())
                except (ValueError, TypeError):
                    pass

    # ---------- Per-driver classification insights ----------
    per_driver_class: Dict[str, Dict[str, Any]] = {}

    # Extract best laps data
    if not best10.empty:
        for _, row in best10.iterrows():
            num = row.get("NUMBER")
            if num is None:
                continue
            vid = num_to_vehicle.get(num) if num_to_vehicle else None
            if vid is None:
                vid = str(num)

            best_laps = []
            for i in range(1, 11):
                col = f"BESTLAP_{i}"
                if col in row.index and pd.notna(row[col]):
                    try:
                        lap_time = time_str_to_seconds(row[col])
                        best_laps.append(lap_time)
                    except (ValueError, TypeError):
                        pass

            if best_laps:
                best_laps_sorted = sorted(best_laps)
                peak_pace = float(np.mean(best_laps_sorted[:3])) if len(best_laps_sorted) >= 3 else float(np.mean(best_laps))
            else:
                peak_pace = None

            per_driver_class.setdefault(str(vid), {})
            per_driver_class[str(vid)]["peak_pace_best3_seconds"] = peak_pace
            per_driver_class[str(vid)]["num_best_laps_recorded"] = len(best_laps)

    # Add position and result info
    if not res.empty:
        for _, row in res.iterrows():
            vid = str(row.get("VEHICLE", "unknown"))
            per_driver_class.setdefault(vid, {})
            
            try:
                if "POSITION" in row and pd.notna(row["POSITION"]):
                    per_driver_class[vid]["position"] = int(row["POSITION"])
            except (ValueError, TypeError):
                pass
            
            try:
                if "LAPS" in row and pd.notna(row["LAPS"]):
                    per_driver_class[vid]["laps_completed"] = int(row["LAPS"])
            except (ValueError, TypeError):
                pass
            
            if "GAP_FIRST" in row and pd.notna(row["GAP_FIRST"]):
                per_driver_class[vid]["gap_to_first_str"] = str(row["GAP_FIRST"])
            
            if "STATUS" in row and pd.notna(row["STATUS"]):
                per_driver_class[vid]["status"] = str(row["STATUS"])
            
            if "CLASS" in row and pd.notna(row["CLASS"]):
                per_driver_class[vid]["class"] = str(row["CLASS"])
            
            if "GROUP" in row and pd.notna(row["GROUP"]):
                per_driver_class[vid]["group"] = str(row["GROUP"])
            
            if "FL_TIME" in row and pd.notna(row["FL_TIME"]):
                try:
                    fl_seconds = time_str_to_seconds(row["FL_TIME"])
                    per_driver_class[vid]["fastest_lap_seconds"] = fl_seconds
                except (ValueError, TypeError):
                    pass

    return classification_summary, per_driver_class


def compute_pace_consistency(best_laps: list) -> Dict[str, float]:
    """
    Compute consistency metrics from best lap times.
    
    Args:
        best_laps: List of lap times in seconds
        
    Returns:
        Dictionary with mean, std, min, max, cv (coefficient of variation)
    """
    if not best_laps:
        return {}
    
    best_laps_clean = [t for t in best_laps if isinstance(t, (int, float)) and t > 0]
    if not best_laps_clean:
        return {}
    
    arr = np.array(best_laps_clean)
    return {
        "mean_lap_time": float(arr.mean()),
        "std_dev": float(arr.std()),
        "min_lap_time": float(arr.min()),
        "max_lap_time": float(arr.max()),
        "coefficient_of_variation": float(arr.std() / arr.mean()) if arr.mean() > 0 else 0.0,
    }
