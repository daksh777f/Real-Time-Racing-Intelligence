import os
import uuid
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from typing import Optional


def _show_or_save(fig, filename: Optional[str] = None, save_dir: str = "plots", show: bool = False):
    """
    Save the figure to `save_dir` as PNG by default. If `show=True`, also attempt to display it.
    """
    os.makedirs(save_dir, exist_ok=True)
    if filename is None:
        filename = f"plot_{uuid.uuid4().hex[:8]}.png"
    path = os.path.join(save_dir, filename)
    fig.savefig(path, bbox_inches="tight")
    print(f"Saved plot to {path}")
    plt.close(fig)
    if show:
        try:
            plt.show()
        except Exception:
            # Backend may be non-interactive; ignore show errors.
            pass


def plot_race_timeline_heatmap(lap_times: pd.DataFrame,
                               event_detection: Optional[pd.DataFrame] = None,
                               title: str = "Race Timeline Heatmap (Lap Time Δ vs Mean)",
                               show: bool = False,
                               outdir: str = "plots",
                               filename: Optional[str] = None):
    """
    lap_times: columns = ['vehicle_id', 'lap', 'lap_time_seconds']
    event_detection: optional, columns = ['vehicle_id', 'lap', 'event_type', 'severity']
    """

    # Ensure correct dtypes
    lt = lap_times.copy()
    lt["lap"] = lt["lap"].astype(int)
    lt = lt.sort_values(["vehicle_id", "lap"])

    # Pivot: rows = driver, cols = lap
    lap_pivot = lt.pivot_table(
        index="vehicle_id",
        columns="lap",
        values="lap_time_seconds",
        aggfunc="mean"
    )

    # Compute delta vs each driver's mean race pace
    lap_delta = lap_pivot.sub(lap_pivot.mean(axis=1), axis=0)

    fig, ax = plt.subplots(figsize=(14, 8))

    im = ax.imshow(
        lap_delta.values,
        aspect="auto",
        cmap="coolwarm",
        interpolation="nearest"
    )

    # Y: drivers
    ax.set_yticks(np.arange(lap_delta.shape[0]))
    ax.set_yticklabels(lap_delta.index)

    # X: laps
    ax.set_xticks(np.arange(lap_delta.shape[1]))
    ax.set_xticklabels(lap_delta.columns)
    plt.setp(ax.get_xticklabels(), rotation=90, ha="center")

    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Lap time delta vs driver mean (s)")

    ax.set_title(title)

    # Overlay events if provided
    if event_detection is not None and len(event_detection) > 0:
        ev = event_detection.copy()
        ev["lap"] = ev["lap"].astype(int)

        # map driver → row index
        driver_to_row = {drv: i for i, drv in enumerate(lap_delta.index)}
        lap_to_col = {lap: j for j, lap in enumerate(lap_delta.columns)}

        for _, e in ev.iterrows():
            drv = e["vehicle_id"]
            lap = e["lap"]
            if drv not in driver_to_row or lap not in lap_to_col:
                continue

            y = driver_to_row[drv]
            x = lap_to_col[lap]

            etype = e.get("event_type", "event")
            severity = float(e.get("severity", 0.5) or 0.5)

            # Choose marker per event_type
            if etype == "lockup":
                marker = "s"
            elif etype == "understeer":
                marker = "^"
            elif etype == "near_spin":
                marker = "X"
            else:
                marker = "o"

            ax.scatter(
                x,
                y,
                marker=marker,
                s=40 + 120 * severity,  # bubble size
                edgecolors="k",
                facecolors="none",
                linewidths=0.7,
                alpha=0.9,
            )

    plt.tight_layout()
    fname = filename or "heatmap.png"
    _show_or_save(fig, filename=fname, save_dir=outdir, show=show)


def plot_time_lost_per_driver(event_detection: pd.DataFrame,
                              title: str = "Total Time Lost per Driver (Incidents)",
                              show: bool = False,
                              outdir: str = "plots",
                              filename: Optional[str] = None):

    if event_detection.empty:
        print("No events to plot.")
        return

    ev = event_detection.copy()
    if "time_loss_estimate" in ev.columns:
        tl_col = "time_loss_estimate"
    elif "time_loss" in ev.columns:
        tl_col = "time_loss"
    else:
        raise ValueError("event_detection must have 'time_loss_estimate' or 'time_loss' column.")

    loss_per_driver = (
        ev.groupby("vehicle_id")[tl_col]
        .sum()
        .sort_values(ascending=False)
    )

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(loss_per_driver.index.tolist(), loss_per_driver.to_numpy())
    ax.set_ylabel("Total time lost to incidents (s)")
    ax.set_xlabel("Driver (vehicle_id)")
    ax.set_title(title)
    plt.xticks(rotation=90)
    plt.tight_layout()
    fname = filename or "time_lost.png"
    _show_or_save(fig, filename=fname, save_dir=outdir, show=show)


def plot_best_vs_worst_lap_speed(telemetry_clean: pd.DataFrame,
                                 lap_times: pd.DataFrame,
                                 driver_id: str,
                                 formation_cutoff: float = 400.0,
                                 show: bool = False,
                                 outdir: str = "plots",
                                 filename: Optional[str] = None):

    # Filter laps for driver
    drv_laps = lap_times[lap_times["vehicle_id"] == driver_id].copy()
    if drv_laps.empty:
        print(f"No lap_times for driver {driver_id}")
        return

    # Filter out absurdly long formation laps
    race_laps = drv_laps[drv_laps["lap_time_seconds"] < formation_cutoff]
    if len(race_laps) < 2:
        print(f"Not enough race laps for driver {driver_id} after filtering formation laps.")
        return

    best_lap = race_laps.loc[race_laps["lap_time_seconds"].idxmin(), "lap"]
    worst_lap = race_laps.loc[race_laps["lap_time_seconds"].idxmax(), "lap"]

    print(f"Driver {driver_id} – best lap: {best_lap}, worst lap: {worst_lap}")

    # Slice telemetry
    tc = telemetry_clean.copy()
    tc = tc[tc["vehicle_id"] == driver_id].copy()
    tc["timestamp"] = pd.to_datetime(tc["timestamp"])

    best_df = tc[tc["lap"] == best_lap].sort_values("timestamp")
    worst_df = tc[tc["lap"] == worst_lap].sort_values("timestamp")

    if best_df.empty or worst_df.empty:
        print("Missing telemetry for best or worst lap.")
        return

    # Relative time in lap
    best_t = (best_df["timestamp"] - best_df["timestamp"].iloc[0]).dt.total_seconds()
    worst_t = (worst_df["timestamp"] - worst_df["timestamp"].iloc[0]).dt.total_seconds()

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(best_t.to_numpy(), best_df["speed"].to_numpy(), label=f"Best lap {int(best_lap)}")
    ax.plot(worst_t.to_numpy(), worst_df["speed"].to_numpy(), label=f"Worst lap {int(worst_lap)}", alpha=0.7)

    ax.set_xlabel("Time in lap (s)")
    ax.set_ylabel("Speed (km/h)")
    ax.set_title(f"Speed Profile – Best vs Worst Lap for {driver_id}")
    ax.legend()
    plt.tight_layout()
    fname = filename or f"speed_profile_{driver_id}.png"
    _show_or_save(fig, filename=fname, save_dir=outdir, show=show)


def _print_usage_examples(script_name: str):
    print("Usage examples:")
    print(f"  python {script_name} --action heatmap --lap_times per_lap_metrics.csv --events event_detection.csv")
    print(f"  python {script_name} --action time_lost --events event_detection.csv")
    print(f"  python {script_name} --action best_worst --driver GR86-026-72 --telemetry telemetry_clean.csv --lap_times per_lap_metrics.csv")


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Visualization utilities for race data")
    parser.add_argument("--telemetry", dest="telemetry", default="telemetry_clean.csv",
                        help="Path to telemetry CSV (default: telemetry_clean.csv)")
    parser.add_argument("--lap_times", dest="lap_times", default="per_lap_metrics.csv",
                        help="Path to per-lap CSV with columns ['vehicle_id','lap','lap_time_seconds']")
    parser.add_argument("--events", dest="events", default="event_detection.csv",
                        help="Path to event_detection CSV")
    parser.add_argument("--driver", dest="driver", default=None,
                        help="Driver vehicle_id for best_vs_worst plot")
    parser.add_argument("--action", dest="action", choices=["heatmap", "time_lost", "best_worst", "all"],
                        default="heatmap", help="Which plot to run (or 'all' to run all available)")
    parser.add_argument("--outdir", dest="outdir", default="plots",
                        help="Directory to save PNG plots (default: ./plots)")
    parser.add_argument("--show", dest="show", action="store_true",
                        help="Also attempt to show plots interactively (default: save only)")

    args = parser.parse_args()

    # Load required files depending on action
    lap_df = None
    ev_df = None
    tel_df = None

    if args.action in ("heatmap", "best_worst"):
        if not os.path.exists(args.lap_times):
            print(f"Missing lap_times file: {args.lap_times}")
            _print_usage_examples(os.path.basename(__file__))
            raise SystemExit(1)
        lap_df = pd.read_csv(args.lap_times)

    if args.action in ("time_lost",):
        if not os.path.exists(args.events):
            print(f"Missing events file: {args.events}")
            _print_usage_examples(os.path.basename(__file__))
            raise SystemExit(1)
        ev_df = pd.read_csv(args.events)

    if args.action == "best_worst":
        if args.driver is None:
            print("'best_worst' action requires --driver <vehicle_id>")
            _print_usage_examples(os.path.basename(__file__))
            raise SystemExit(1)
        if not os.path.exists(args.telemetry):
            print(f"Missing telemetry file: {args.telemetry}")
            _print_usage_examples(os.path.basename(__file__))
            raise SystemExit(1)
        tel_df = pd.read_csv(args.telemetry)

    # Dispatch
    if args.action == "heatmap":
        assert lap_df is not None, "lap_times must be loaded for heatmap"
        plot_race_timeline_heatmap(lap_df, event_detection=ev_df, show=args.show, outdir=args.outdir,
                                   filename=f"heatmap.png")
    elif args.action == "time_lost":
        assert ev_df is not None, "events must be loaded for time_lost"
        plot_time_lost_per_driver(ev_df, show=args.show, outdir=args.outdir, filename=f"time_lost.png")
    elif args.action == "best_worst":
        assert tel_df is not None and lap_df is not None, "telemetry and lap_times must be loaded for best_worst"
        plot_best_vs_worst_lap_speed(tel_df, lap_df, driver_id=args.driver, show=args.show, outdir=args.outdir,
                                     filename=f"speed_profile_{args.driver}.png")
    elif args.action == "all":
        # heatmap
        if lap_df is not None:
            plot_race_timeline_heatmap(lap_df, event_detection=ev_df, show=args.show, outdir=args.outdir,
                                       filename=f"heatmap.png")
        # time lost
        if ev_df is not None:
            plot_time_lost_per_driver(ev_df, show=args.show, outdir=args.outdir, filename=f"time_lost.png")
        # best vs worst: optional, only if driver provided
        if args.driver is not None and tel_df is not None and lap_df is not None:
            plot_best_vs_worst_lap_speed(tel_df, lap_df, driver_id=args.driver, show=args.show, outdir=args.outdir,
                                         filename=f"speed_profile_{args.driver}.png")