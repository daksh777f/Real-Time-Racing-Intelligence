"""
Core Analysis Engine - merges all race data into enriched race_facts JSON
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import json


# ---------- Dataclasses for structure ----------

@dataclass
class Event:
    """Represents a significant race event (incident, advantage, etc.)"""
    event_type: str
    lap: int
    timestamp: str
    vehicle_id: str
    severity: float
    time_loss: float
    metrics: Dict[str, float]
    description: str
    role: Optional[str] = None   # e.g. "race_turning_point", "major_mistake"
    event_id: Optional[str] = None


@dataclass
class DriverRaceSummary:
    """Complete race summary for a single driver"""
    vehicle_id: str
    vehicle_number: Optional[str]
    start_pos: Optional[int]
    finish_pos: Optional[int]
    driver_metrics: Dict[str, float]
    driver_style_tags: List[str]
    driver_key_events: List[Event]
    sector_insights: Dict[str, Any]  # filled by sector_analysis
    classification_insights: Dict[str, Any]  # class, gaps, best_lap


@dataclass
class RaceFacts:
    """Complete enriched race analysis"""
    race: Dict[str, Any]
    drivers: List[DriverRaceSummary]
    race_key_events: List[Event]
    lap_times: List[Dict[str, Any]]
    weather_summary: Dict[str, Any]
    sector_summary: Dict[str, Any]
    classification_summary: Dict[str, Any]
    what_if_base: Dict[str, Any]  # total times, event losses etc


# ---------- Load helpers for various CSV formats ----------

def load_results(results_path: str) -> pd.DataFrame:
    """Load results CSV (03_Provisional Results or Official)"""
    try:
        df = pd.read_csv(results_path, sep=";")
    except Exception:
        df = pd.read_csv(results_path)
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def load_class_results(path: str) -> pd.DataFrame:
    """Load class results CSV (05_Results by Class)"""
    try:
        df = pd.read_csv(path, sep=";")
    except Exception:
        df = pd.read_csv(path)
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def load_sector_file(path: str) -> pd.DataFrame:
    """Load sector analysis CSV (23_AnalysisEnduranceWithSections)"""
    try:
        df = pd.read_csv(path, sep=";")
    except Exception:
        df = pd.read_csv(path)
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def load_weather(path: str) -> pd.DataFrame:
    """Load weather CSV (26_Weather)"""
    try:
        df = pd.read_csv(path, sep=";")
    except Exception:
        df = pd.read_csv(path)
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def load_best10(path: str) -> pd.DataFrame:
    """Load best 10 laps CSV (99_Best 10 Laps By Driver)"""
    try:
        df = pd.read_csv(path, sep=";")
    except Exception:
        df = pd.read_csv(path)
    df.columns = [c.strip().upper() for c in df.columns]
    return df


# ---------- Helper functions ----------

def infer_style_tags(row: pd.Series) -> List[str]:
    """Infer driver style tags from metrics"""
    tags = []
    if row.get("steering_variance_mean", 0) > 1000:
        tags.append("erratic_steering")
    elif row.get("steering_variance_mean", 0) < 600:
        tags.append("smooth_steering")
    if row.get("brake_spikes_sum", 0) > 5000:
        tags.append("aggressive_braking")
    if row.get("throttle_smoothness_mean", 2) < 1.2:
        tags.append("smooth_throttle")
    if row.get("lap_time_std", 0) > 70:
        tags.append("inconsistent_pace")
    return tags


# ---------- Core: build enriched race_facts ----------

def build_race_facts(
    race_name: str,
    track_name: str,
    telemetry_clean: pd.DataFrame,
    per_lap_metrics: pd.DataFrame,
    per_driver_metrics: pd.DataFrame,
    event_detection: pd.DataFrame,
    lap_times: pd.DataFrame,
    results_df: pd.DataFrame,
    class_results_df: Optional[pd.DataFrame] = None,
    sector_df: Optional[pd.DataFrame] = None,
    weather_df: Optional[pd.DataFrame] = None,
    best10_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """
    Main engine that merges everything and returns an enriched race_facts dict.
    
    Args:
        race_name: Name of race event
        track_name: Track name
        telemetry_clean: Cleaned telemetry DataFrame
        per_lap_metrics: Per-lap aggregated metrics
        per_driver_metrics: Per-driver aggregated metrics
        event_detection: Detected events and incidents
        lap_times: Individual lap times
        results_df: Official race results
        class_results_df: Optional class/group results
        sector_df: Optional sector analysis (S1/S2/S3 times)
        weather_df: Optional weather data
        best10_df: Optional best 10 laps data
        
    Returns:
        Dictionary ready for JSON serialization
    """

    # Initialize optional DataFrames as empty if None
    if class_results_df is None:
        class_results_df = pd.DataFrame()
    if sector_df is None:
        sector_df = pd.DataFrame()
    if weather_df is None:
        weather_df = pd.DataFrame()
    if best10_df is None:
        best10_df = pd.DataFrame()

    # ---------- basic race header ----------
    total_laps = int(lap_times["lap"].max()) if "lap" in lap_times.columns else 8
    race_info = {
        "event_name": race_name,
        "track": track_name,
        "total_laps": total_laps,
    }

    # ---------- weather summary ----------
    weather_summary = {}
    if not weather_df.empty:
        try:
            weather_summary = {
                "air_temp_mean": float(weather_df["AIR_TEMP"].mean()) if "AIR_TEMP" in weather_df.columns else None,
                "track_temp_mean": float(weather_df["TRACK_TEMP"].mean()) if "TRACK_TEMP" in weather_df.columns else None,
                "humidity_mean": float(weather_df["HUMIDITY"].mean()) if "HUMIDITY" in weather_df.columns else None,
                "rain_flag": bool((weather_df.get("RAIN", 0) > 0).any()),
                "wind_speed_mean": float(weather_df["WIND_SPEED"].mean()) if "WIND_SPEED" in weather_df.columns else None,
            }
        except Exception:
            weather_summary = {}

    # ---------- classification summary ----------
    res = results_df.copy()
    res.columns = [c.strip().upper() for c in res.columns]
    
    classification_summary = {
        "num_starters": int(res["NUMBER"].nunique()) if "NUMBER" in res.columns else 0,
        "winner_vehicle": res.sort_values("POSITION").iloc[0]["VEHICLE"] if "VEHICLE" in res.columns and len(res) > 0 else None,
    }

    # map for quick lookup
    results_by_vehicle = {}
    if "VEHICLE" in res.columns:
        results_by_vehicle = {row["VEHICLE"]: row for _, row in res.iterrows()}

    # ---------- build race_key_events ----------
    race_key_events: List[Event] = []
    if not event_detection.empty:
        if "role" in event_detection.columns:
            key_events_df = event_detection[event_detection["role"].notna()].head(20)
        else:
            key_events_df = event_detection.nlargest(10, "severity") if "severity" in event_detection.columns else event_detection.head(10)

        for _, ev in key_events_df.iterrows():
            try:
                race_key_events.append(
                    Event(
                        event_type=str(ev.get("event_type", "unknown")),
                        lap=int(ev.get("lap", 0)),
                        timestamp=str(ev.get("timestamp", "")),
                        vehicle_id=str(ev.get("vehicle_id", "")),
                        severity=float(ev.get("severity", 0.0)),
                        time_loss=float(ev.get("time_loss", ev.get("time_loss_estimate", 0.0))),
                        metrics={
                            "steering_correction_deg": float(ev.get("steering_correction_deg", 0.0)),
                            "latG_spike": float(ev.get("latG_spike", 0.0)),
                            "speed_loss_kph": float(ev.get("speed_loss", 0.0)),
                        },
                        description=str(ev.get("description", "")),
                        role=ev.get("role"),
                        event_id=ev.get("event_id"),
                    )
                )
            except Exception:
                continue

    # ---------- per-driver structures ----------
    drivers: List[DriverRaceSummary] = []

    # merge driver metrics and results only if results available
    if not res.empty and "VEHICLE" in res.columns:
        merged_drivers = per_driver_metrics.merge(
            res,
            left_on="vehicle_id",
            right_on="VEHICLE",
            how="left",
            suffixes=("", "_RES"),
        )
    else:
        # No results, use driver metrics alone
        merged_drivers = per_driver_metrics.copy()

    for _, row in merged_drivers.iterrows():
        vid = str(row.get("vehicle_id", ""))
        vehicle_number = row.get("NUMBER", None)
        start_pos = None
        finish_pos = None
        
        try:
            if "POSITION" in row and pd.notna(row["POSITION"]):
                finish_pos = int(row["POSITION"])
        except Exception:
            pass

        # driver metrics as dict
        dm_cols = [
            "lap_time_mean",
            "lap_time_best",
            "lap_time_std",
            "max_speed_mean",
            "peak_lat_G_mean",
            "peak_long_G_mean",
            "throttle_smoothness_mean",
            "steering_variance_mean",
            "brake_spikes_sum",
            "gear_changes_sum",
        ]
        driver_metrics = {}
        for c in dm_cols:
            if c in row and pd.notna(row[c]):
                try:
                    driver_metrics[c] = float(row[c])
                except (ValueError, TypeError):
                    pass

        # style tags
        style_tags = row.get("driver_style_tags", None)
        if style_tags is None or (isinstance(style_tags, float) and np.isnan(style_tags)):
            style_tags = infer_style_tags(row)
        elif isinstance(style_tags, str):
            style_tags = [s.strip() for s in style_tags.split(",")]
        elif not isinstance(style_tags, list):
            style_tags = []

        # driver key events
        drv_events: List[Event] = []
        if not event_detection.empty and "vehicle_id" in event_detection.columns:
            drv_events_df = event_detection[event_detection["vehicle_id"] == vid]
            for _, ev in drv_events_df.iterrows():
                try:
                    drv_events.append(
                        Event(
                            event_type=str(ev.get("event_type", "unknown")),
                            lap=int(ev.get("lap", 0)),
                            timestamp=str(ev.get("timestamp", "")),
                            vehicle_id=vid,
                            severity=float(ev.get("severity", 0.0)),
                            time_loss=float(ev.get("time_loss", ev.get("time_loss_estimate", 0.0))),
                            metrics={
                                "steering_correction_deg": float(ev.get("steering_correction_deg", 0.0)),
                                "latG_spike": float(ev.get("latG_spike", 0.0)),
                                "speed_loss_kph": float(ev.get("speed_loss", 0.0)),
                            },
                            description=str(ev.get("description", "")),
                            role=ev.get("role"),
                            event_id=ev.get("event_id"),
                        )
                    )
                except Exception:
                    continue

        drivers.append(
            DriverRaceSummary(
                vehicle_id=vid,
                vehicle_number=vehicle_number,
                start_pos=start_pos,
                finish_pos=finish_pos,
                driver_metrics=driver_metrics,
                driver_style_tags=style_tags,
                driver_key_events=drv_events,
                sector_insights={},
                classification_insights={},
            )
        )

    # ---------- lap_times as list ----------
    lap_times_list = []
    if "vehicle_id" in lap_times.columns and "lap" in lap_times.columns:
        lap_times_list = (
            lap_times[["vehicle_id", "lap", "lap_time_seconds"]]
            .sort_values(["vehicle_id", "lap"])
            .to_dict(orient="records")
        )

    # ---------- what_if_base ----------
    what_if_base = {
        "total_time_seconds": {},
        "total_event_loss_seconds": {},
    }
    
    try:
        if lap_times_list:
            lt_df = pd.DataFrame(lap_times_list)
            total_time = lt_df.groupby("vehicle_id")["lap_time_seconds"].sum()
            what_if_base["total_time_seconds"] = total_time.to_dict()
        
        if not event_detection.empty:
            if "time_loss_estimate" in event_detection.columns:
                event_loss = event_detection.groupby("vehicle_id")["time_loss_estimate"].sum()
            elif "time_loss" in event_detection.columns:
                event_loss = event_detection.groupby("vehicle_id")["time_loss"].sum()
            else:
                event_loss = pd.Series()
            
            if not event_loss.empty:
                what_if_base["total_event_loss_seconds"] = event_loss.to_dict()
    except Exception:
        pass

    # ---------- sector + classification enrichment ----------
    # Lazy import to avoid circular imports
    from .sector_analysis import build_sector_analysis
    from .classification_insights import build_classification_insights

    sector_summary = {}
    per_driver_sector = {}
    if not sector_df.empty:
        sector_summary, per_driver_sector = build_sector_analysis(sector_df, res)

    classification_summary_extended = {}
    per_driver_class = {}
    if not best10_df.empty or not class_results_df.empty:
        classification_summary_extended, per_driver_class = build_classification_insights(
            res, class_results_df, best10_df
        )
        classification_summary.update(classification_summary_extended)

    # inject into driver objects
    for d in drivers:
        if d.vehicle_id in per_driver_sector:
            d.sector_insights = per_driver_sector[d.vehicle_id]
        if d.vehicle_id in per_driver_class:
            d.classification_insights = per_driver_class[d.vehicle_id]

    # ---------- Final serialization ----------
    return {
        "race": race_info,
        "drivers": [
            {
                **{
                    k: v
                    for k, v in asdict(d).items()
                    if k not in ["driver_key_events"]
                },
                "driver_key_events": [asdict(e) for e in d.driver_key_events],
            }
            for d in drivers
        ],
        "race_key_events": [asdict(e) for e in race_key_events],
        "lap_times": lap_times_list,
        "weather_summary": weather_summary,
        "sector_summary": sector_summary,
        "classification_summary": classification_summary,
        "what_if_base": what_if_base,
    }
