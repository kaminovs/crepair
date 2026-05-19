"""
scoring/logger.py

Structured result logger. Writes every result immediately —
never batch-save at the end, so partial runs are not lost.

Outputs:
  results/runs/YYYYMMDD_HHMMSS_<model>.jsonl   — full detail, one JSON per line
  results/leaderboard.csv                       — flat, appended on each run
"""

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

RESULTS_DIR = Path(__file__).parent.parent / "results"
RUNS_DIR    = RESULTS_DIR / "runs"
LEADERBOARD = RESULTS_DIR / "leaderboard.csv"

LEADERBOARD_FIELDS = [
    "timestamp", "run_id",
    "scenario_id", "scenario_type", "difficulty",
    "model", "condition",
    "D", "R", "V", "S", "C_repair",
    "cascade",
]


def _ensure_dirs():
    RESULTS_DIR.mkdir(exist_ok=True)
    RUNS_DIR.mkdir(exist_ok=True)


def _ensure_leaderboard():
    if not LEADERBOARD.exists():
        with open(LEADERBOARD, "w", newline="") as f:
            csv.DictWriter(f, fieldnames=LEADERBOARD_FIELDS).writeheader()


class RunLogger:
    """
    One logger instance per experiment run.
    Call .log(result) after each scenario. Call .close() when done.
    """

    def __init__(self, model: str, run_id: Optional[str] = None):
        _ensure_dirs()
        _ensure_leaderboard()

        self.model   = model
        self.run_id  = run_id or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.count   = 0
        self.errors  = 0

        jsonl_name   = f"{self.run_id}_{model}.jsonl"
        self._jsonl  = open(RUNS_DIR / jsonl_name, "a")
        self._csv    = open(LEADERBOARD, "a", newline="")
        self._writer = csv.DictWriter(self._csv, fieldnames=LEADERBOARD_FIELDS)

        print(f"[Logger] Run {self.run_id} | model={model} | log={jsonl_name}")

    def log(self, result) -> None:
        """
        Accepts a CRepairResult (or any object with .to_dict() / .to_row()).
        Writes immediately to both JSONL and leaderboard CSV.
        """
        ts = datetime.now(timezone.utc).isoformat()

        # Full detail → JSONL
        full = result.to_dict()
        full["timestamp"] = ts
        full["run_id"]    = self.run_id
        self._jsonl.write(json.dumps(full) + "\n")
        self._jsonl.flush()

        # Flat row → leaderboard CSV
        row = result.to_row()
        row["timestamp"] = ts
        row["run_id"]    = self.run_id
        row["difficulty"] = getattr(result, "difficulty", "")
        # ensure all fields present
        for f in LEADERBOARD_FIELDS:
            row.setdefault(f, "")
        self._writer.writerow({f: row[f] for f in LEADERBOARD_FIELDS})
        self._csv.flush()

        self.count += 1
        print(f"  [{self.count:02d}] {result.scenario_id:<12} "
              f"D={result.scores.D:.1f} R={result.scores.R:.1f} "
              f"V={result.scores.V:.1f} S={result.scores.S:.1f} "
              f"→ C_repair={result.c_repair:.3f}"
              + (" ⚠ CASCADE" if result.cascade_detected else ""))

    def log_error(self, scenario_id: str, condition: str, error: str) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        record = {
            "timestamp": ts, "run_id": self.run_id,
            "scenario_id": scenario_id, "model": self.model,
            "condition": condition, "error": error,
        }
        self._jsonl.write(json.dumps(record) + "\n")
        self._jsonl.flush()
        self.errors += 1
        print(f"  ERROR {scenario_id}/{condition}: {error}")

    def close(self) -> None:
        self._jsonl.close()
        self._csv.close()
        print(f"[Logger] Closed. {self.count} results, {self.errors} errors logged.")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
