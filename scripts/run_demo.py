#!/usr/bin/env python3
"""Run the complete synthetic-data pipeline for the public dashboard demo."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def run(script: str) -> None:
    print(f"\n==> {script}")
    subprocess.run([sys.executable, str(SCRIPTS / script)], check=True)


def main() -> None:
    run("generate_demo_data.py")
    run("transform_data.py")
    run("validate_data.py")
    print("\nDemo data pipeline completed successfully.")


if __name__ == "__main__":
    main()
