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
    If the following identifiers are present, de-duplicate by their combination
    and use the latest ORIGIN_AT_UTC per unique id before aggregating:
      - service_version_and_roundtrip_identfiers
      - origin_service_version_and_master
      - destination_service_version_and_master
    """
    agg: Dict[Tuple[str, datetime.date], int] = defaultdict(int)
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Normalize header keys for presence checks (case-sensitive as per provided sample)
    id_keys = [
        "service_version_and_roundtrip_identfiers",
        "origin_service_version_and_master",
        "destination_service_version_and_master",
    ]
    has_ids = all(k in rows[0] for k in id_keys) if rows else False

    def parse_dt(ts: str) -> datetime | None:
        try:
            try:
                return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return None

    if has_ids:
        # Deduplicate by unique id → keep row with latest origin departure timestamp
        latest_by_uid = {}
        for r in rows:
            uid = (
                (r.get(id_keys[0]) or "").strip(),
                (r.get(id_keys[1]) or "").strip(),
                (r.get(id_keys[2]) or "").strip(),
            )
            ts = (r.get("ORIGIN_AT_UTC") or "").strip()
            dt = parse_dt(ts)
            if not dt:
                continue
            prev = latest_by_uid.get(uid)
            if (prev is None) or (dt > prev[0]):
                latest_by_uid[uid] = (dt, r)

        rows_iter = (rec for (_dt, rec) in latest_by_uid.values())
    else:
        # Fallback: use all rows
        rows_iter = iter(rows)

    for r in rows_iter:
        origin = (r.get("ORIGIN") or "").strip()
        dest = (r.get("DESTINATION") or "").strip()
        ts = (r.get("ORIGIN_AT_UTC") or "").strip()
        teu_raw = r.get("OFFERED_CAPACITY_TEU") or "0"
        if not origin or not dest or not ts:
            continue
        dt = parse_dt(ts)
        if not dt:
            continue
        try:
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
    if not csv_path.exists():
        raise SystemExit(f"CSV not found at {csv_path}. Provide --csv PATH or place sailing_level_raw.csv in repo root.")
    agg = aggregate(csv_path)
    load_data(agg, truncate=args.truncate)
    print(f"Loaded {len(agg)} weekly rows from {csv_path}")


if __name__ == "__main__":
    main()
