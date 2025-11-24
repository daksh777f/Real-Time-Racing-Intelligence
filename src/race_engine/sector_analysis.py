"""
Sector Analysis System - deep S1/S2/S3 strengths, losses, and fatigue
"""

from typing import Tuple, Dict, Any
import pandas as pd
import numpy as np


def build_sector_analysis(
    sector_df: pd.DataFrame,
    results_df: pd.DataFrame,
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    """
    Analyze sector performance (S1/S2/S3) for all drivers.
    
    Expects sector_df columns (from 23_AnalysisEnduranceWithSections):
        NUMBER, LAP_NUMBER, S1, S2, S3, TOP_SPEED, PIT_TIME, ...
    
    Returns:
        sector_summary: dict with overall best times per sector
        per_driver_sector: mapping vehicle_id -> insights dict with:
            - sector_means (S1, S2, S3 average times)
            - sector_losses_vs_best (delta to sector best)
            - strongest_sector (where driver excels)
            - weakest_sector (where driver struggles)
            - fatigue_indicator (S3 vs S1 trend)
            - consistency (variance per sector)
    """
    if sector_df.empty:
        return {}, {}

    df = sector_df.copy()
    df.columns = [c.strip().upper() for c in df.columns]

    # link NUMBER -> VEHICLE from results
    res = results_df.copy()
    res.columns = [c.strip().upper() for c in res.columns]
    
    num_to_vehicle = {}
    if "NUMBER" in res.columns and "VEHICLE" in res.columns:
        num_to_vehicle = {row["NUMBER"]: row["VEHICLE"] for _, row in res.iterrows()}
    
    if "NUMBER" in df.columns and num_to_vehicle:
        df["VEHICLE"] = df["NUMBER"].map(num_to_vehicle)
    elif "VEHICLE" not in df.columns:
        # fallback: use NUMBER as vehicle ID
        df["VEHICLE"] = df.get("NUMBER", "unknown")

    # convert sector times to numeric
    for s in ["S1", "S2", "S3"]:
        if s in df.columns:
            df[s] = pd.to_numeric(df[s], errors="coerce")

    # keep only valid records
    df = df.dropna(subset=["VEHICLE"])
    valid_sectors = [s for s in ["S1", "S2", "S3"] if s in df.columns]
    if valid_sectors:
        df = df.dropna(subset=valid_sectors)

    if df.empty:
        return {}, {}

    # ---------- Sector statistics ----------
    grp = df.groupby("VEHICLE")
    
    sector_stats = {}
    for s in valid_sectors:
        sector_stats[f"mean_{s}"] = grp[s].mean()
        sector_stats[f"std_{s}"] = grp[s].std()
        sector_stats[f"min_{s}"] = grp[s].min()
        sector_stats[f"max_{s}"] = grp[s].max()

    # global best per sector
    sector_summary = {}
    best_vehicles = {}
    for s in valid_sectors:
        if s in df.columns:
            best_idx = df[s].idxmin()
            best_row = df.loc[best_idx]
            best_time_val = best_row[s]
            if isinstance(best_time_val, (pd.Series)):
                best_time = float(best_time_val.iloc[0])
            else:
                best_time = float(best_time_val)
            best_vehicle = str(best_row["VEHICLE"])
            sector_summary[f"best_{s}"] = {
                "vehicle": best_vehicle,
                "time": best_time
            }
            best_vehicles[s] = best_time

    # ---------- Per-driver insights ----------
    per_driver_sector: Dict[str, Dict[str, Any]] = {}
    
    for vehicle_id in grp.groups.keys():
        vehicle_id = str(vehicle_id)
        sector_means = {}
        sector_losses = {}
        sector_consistency = {}
        
        for s in valid_sectors:
            if s in sector_stats:
                mean_s = float(sector_stats[f"mean_{s}"].get(vehicle_id, 0))
                std_s = float(sector_stats[f"std_{s}"].get(vehicle_id, 0))
                min_s = float(sector_stats[f"min_{s}"].get(vehicle_id, mean_s))
                
                sector_means[s] = mean_s
                sector_consistency[s] = std_s
                
                # loss vs best
                loss = mean_s - best_vehicles.get(s, mean_s)
                sector_losses[f"{s}_loss_vs_best"] = loss

        # identify strongest and weakest
        if sector_means:
            strongest = min(sector_means.keys(), key=lambda k: sector_means[k])  # type: ignore
            weakest = max(sector_means.keys(), key=lambda k: sector_means[k])  # type: ignore
            
            # fatigue indicator: compare first half vs second half of race
            # (rough proxy: check if later laps in S3 are slower)
            s1_times = df[df["VEHICLE"] == vehicle_id]["S1"].dropna()
            s3_times = df[df["VEHICLE"] == vehicle_id]["S3"].dropna()
            
            fatigue_indicator = 0.0
            if len(s1_times) > 0 and len(s3_times) > 0:
                # negative = getting better, positive = getting worse
                fatigue_indicator = float((s3_times.mean() - s1_times.mean()) / s1_times.mean() * 100)
        else:
            strongest = "N/A"
            weakest = "N/A"
            fatigue_indicator = 0.0

        per_driver_sector[vehicle_id] = {
            "sector_means": sector_means,
            "sector_losses_vs_best": sector_losses,
            "sector_consistency": sector_consistency,
            "strongest_sector": strongest,
            "weakest_sector": weakest,
            "fatigue_indicator_percent": fatigue_indicator,  # +ve = degrading
        }

    return sector_summary, per_driver_sector


def compute_sector_pace_profile(sector_df: pd.DataFrame, vehicle_id: str) -> Dict[str, Any]:
    """
    For a specific vehicle, compute detailed pace profile across all sectors.
    Useful for identifying corner strengths vs weaknesses.
    """
    if sector_df.empty:
        return {}
    
    df = sector_df.copy()
    df.columns = [c.strip().upper() for c in df.columns]
    
    drv_data = df[df["VEHICLE"] == vehicle_id].copy() if "VEHICLE" in df.columns else pd.DataFrame()
    
    if drv_data.empty:
        return {}
    
    profile = {}
    for s in ["S1", "S2", "S3"]:
        if s in drv_data.columns:
            times = pd.to_numeric(drv_data[s], errors="coerce").dropna()
            if not times.empty:
                profile[s] = {
                    "mean": float(times.mean()),
                    "min": float(times.min()),
                    "max": float(times.max()),
                    "std": float(times.std()),
                    "num_samples": len(times),
                }
    
    if "TOP_SPEED" in drv_data.columns:
        top_speeds = pd.to_numeric(drv_data["TOP_SPEED"], errors="coerce").dropna()
        if not top_speeds.empty:
            profile["top_speed"] = {
                "mean": float(top_speeds.mean()),
                "max": float(top_speeds.max()),
                "min": float(top_speeds.min()),
            }
    
    return profile
