#!/usr/bin/env python3
"""Safely rebuild data/landing from the current schema and promote only a validated candidate.

The active landing directory is never written during generation. On success it is renamed
to a dated backup and the validated candidate is promoted. Backups are intentionally kept.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
LANDING = DATA_DIR / "landing"


def run(command: list[str], label: str) -> None:
    print(f"\n=== {label} ===", flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate, validate, back up, and safely promote realistic raw PixelFed landing data."
    )
    parser.add_argument("--scale", type=float, default=1.0, help="Row multiplier; use 0.03 for a smoke run")
    parser.add_argument("--seed", type=int, default=42, help="Reproducible synthetic seed")
    parser.add_argument(
        "--as-of",
        default=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        help="Fixed UTC cutoff, e.g. 2026-10-27T12:00:00Z",
    )
    args = parser.parse_args()
    if args.scale <= 0:
        parser.error("--scale must be greater than zero")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    candidate = DATA_DIR / f"landing_candidate_{stamp}"
    backup = DATA_DIR / f"landing_backup_{stamp}"
    if candidate.exists() or backup.exists():
        raise FileExistsError("Candidate or backup path already exists; rerun to use a new timestamp.")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    generator = ROOT / "src" / "generate_landing.py"
    validator = ROOT / "src" / "validate_landing.py"
    try:
        run(
            [
                sys.executable, str(generator),
                "--output-dir", str(candidate),
                "--scale", str(args.scale),
                "--seed", str(args.seed),
                "--as-of", args.as_of,
                "--raw-quality",
            ],
            "Generate candidate with coherent business entities and intentional raw-data issues",
        )
        run([sys.executable, str(validator), "--landing", str(candidate)], "Validate candidate schema and physical exports")

        report_path = candidate / "metadata" / "data_quality_report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if report.get("passed") is not True:
            raise RuntimeError("Generator quality contract did not pass; active landing data was not changed.")
        raw_quality = report.get("raw_quality", {})
        if raw_quality.get("enabled") is not True or raw_quality.get("total_injected_issues", 0) < 1:
            raise RuntimeError("Expected intentional raw-quality issues were not recorded; active landing data was not changed.")

        if LANDING.exists():
            LANDING.rename(backup)
            try:
                candidate.rename(LANDING)
            except Exception:
                if not LANDING.exists() and backup.exists():
                    backup.rename(LANDING)
                raise
            print(f"\nPrevious landing data preserved at: {backup}")
        else:
            candidate.rename(LANDING)

        print(f"Validated landing data promoted to: {LANDING}")
        print(f"Raw-quality report: {LANDING / 'metadata' / 'data_quality_report.json'}")
        print("Backup is retained. Do not delete it until Power BI refresh and reconciliation pass.")
        return 0
    except Exception:
        print("\nRefresh failed. Existing data/landing was not intentionally overwritten.", file=sys.stderr)
        if candidate.exists():
            print(f"Candidate retained for inspection: {candidate}", file=sys.stderr)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
