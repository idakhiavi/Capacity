from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Tuple

from sqlalchemy import text

from app.config import get_engine, ensure_schema


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Aggregate sailing-level CSV into weekly corridor capacity")
    p.add_argument("--csv", required=False, default="sailing_level_raw.csv", help="Path to sailing_level_raw.csv")
    p.add_argument("--truncate", action="store_true", help="Delete all from weekly_capacity before loading")
    return p.parse_args()


def week_start(d: datetime) -> datetime.date:
    # Monday as start of the ISO week
    return (d - timedelta(days=d.weekday())).date()


def aggregate(csv_path: Path) -> Dict[Tuple[str, datetime.date], int]:
    """Aggregate per (corridor, week_start_date) using sailing-level rows.

    Expects columns: ORIGIN, DESTINATION, ORIGIN_AT_UTC, OFFERED_CAPACITY_TEU.
    """
    agg: Dict[Tuple[str, datetime.date], int] = defaultdict(int)
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            origin = (r.get("ORIGIN") or "").strip()
            dest = (r.get("DESTINATION") or "").strip()
            timestamp = r.get("ORIGIN_AT_UTC") or ""
            teu_raw = r.get("OFFERED_CAPACITY_TEU") or "0"
            if not origin or not dest or not timestamp:
                continue
            try:
                try:
                    dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
                except ValueError:
                    dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                teu = int(float(teu_raw))
            except Exception:
                continue
            corridor = f"{origin}-{dest}"
            agg[(corridor, week_start(dt))] += teu
    return agg


def load_data(agg: Dict[Tuple[str, datetime.date], int], truncate: bool = False) -> None:
    engine = get_engine()
    ensure_schema(engine)
    with engine.begin() as conn:
        if truncate:
            conn.execute(text("DELETE FROM weekly_capacity"))
        for (corridor, wk), teu in sorted(agg.items(), key=lambda x: (x[0][0], x[0][1])):
            res = conn.execute(
                text(
                    """
                    UPDATE weekly_capacity
                    SET offered_teu = :teu
                    WHERE corridor = :corridor AND week_start_date = :wk
                    """
                ),
                {"teu": teu, "corridor": corridor, "wk": wk},
            )
            if res.rowcount == 0:
                conn.execute(
                    text(
                        """
                        INSERT INTO weekly_capacity (corridor, week_start_date, offered_teu)
                        VALUES (:corridor, :wk, :teu)
                        """
                    ),
                    {"corridor": corridor, "wk": wk, "teu": teu},
                )


def main() -> None:
    args = parse_args()
    csv_path = Path(args.csv)
    agg = aggregate(csv_path)
    load_data(agg, truncate=args.truncate)
    print(f"Loaded {len(agg)} weekly rows from {csv_path}")


if __name__ == "__main__":
    main()

