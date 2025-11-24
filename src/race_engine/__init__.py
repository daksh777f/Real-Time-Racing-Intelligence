"""
Race Analysis Engine - Complete system for analyzing motorsports races
with Analysis Engine, Sector Analysis, and What-If simulation.
"""

from .analysis_engine import (
    build_race_facts,
    Event,
    DriverRaceSummary,
    RaceFacts,
    load_results,
    load_class_results,
    load_sector_file,
    load_weather,
    load_best10,
)

from .sector_analysis import (
    build_sector_analysis,
)

from .classification_insights import (
    build_classification_insights,
    time_str_to_seconds,
)

from .what_if import (
    simulate_no_events,
    build_what_if_payload,
    filter_events_for_removal,
)

__all__ = [
    "build_race_facts",
    "Event",
    "DriverRaceSummary",
    "RaceFacts",
    "load_results",
    "load_class_results",
    "load_sector_file",
    "load_weather",
    "load_best10",
    "build_sector_analysis",
    "build_classification_insights",
    "time_str_to_seconds",
    "simulate_no_events",
    "build_what_if_payload",
    "filter_events_for_removal",
]
