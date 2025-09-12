from __future__ import annotations

from datetime import date, timedelta
from typing import List, Tuple

from sqlalchemy import text
from sqlalchemy.engine import Engine


Row = Tuple[str, date, int, float]


class CapacityRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def get_capacity_with_rolling_avg(
        self, corridor: str, date_from: date, date_to: date
    ) -> List[Row]:
        """
        Return rows: (corridor, week_start_date, offered_teu, rolling_avg_4w)
        Includes up to 3 weeks before `date_from` to compute correct rolling average.
        """
        start_buffered = date_from - timedelta(days=21)

        sql = text(
            """
            SELECT
              corridor,
              week_start_date,
              offered_teu,
              AVG(offered_teu) OVER (
                PARTITION BY corridor
                ORDER BY week_start_date
                ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
              ) AS rolling_avg_4w
            FROM weekly_capacity
            WHERE corridor = :corridor
              AND week_start_date BETWEEN :start_buffered AND :date_to
            ORDER BY week_start_date ASC
            """
        )

        with self.engine.begin() as conn:
            result = conn.execute(
                sql,
                {
                    "corridor": corridor,
                    "start_buffered": start_buffered,
                    "date_to": date_to,
                },
            )
            rows: List[Row] = []
            for r in result.mappings():
                wk = r["week_start_date"]
                if isinstance(wk, str):
                    # SQLite may return DATE as TEXT; normalize to date
                    from datetime import date as _date

                    try:
                        wk = _date.fromisoformat(wk)
                    except Exception:
                        # Fallback: leave as-is; service will reject if unusable
                        pass
                rows.append(
                    (
                        r["corridor"],
                        wk,
                        int(r["offered_teu"]),
                        float(r["rolling_avg_4w"]),
                    )
                )
        return rows
