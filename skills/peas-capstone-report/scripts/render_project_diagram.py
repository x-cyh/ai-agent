#!/usr/bin/env python3
"""Render report/project-architecture.mmd to PNG via npx @mermaid-js/mermaid-cli."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def render(mmd: Path, out: Path, scale: float = 1.0) -> int:
    if not mmd.is_file():
        print(f"ERROR: Mermaid file not found: {mmd}", file=sys.stderr)
        return 1

    out.parent.mkdir(parents=True, exist_ok=True)

    npx = shutil.which("npx")
    if not npx:
        print(
            "ERROR: npx not found. Install Node.js or see references/mermaid-to-png-guide.md",
            file=sys.stderr,
        )
        return 1

    cmd = [
        npx,
        "-y",
        "@mermaid-js/mermaid-cli",
        "-i",
        str(mmd),
        "-o",
        str(out),
        "-b",
        "white",
        "-s",
        str(scale),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "").strip()
        print(err or "mmdc failed", file=sys.stderr)
        return result.returncode

    if not out.is_file() or out.stat().st_size == 0:
        print(f"ERROR: PNG not created or empty: {out}", file=sys.stderr)
        return 1

    print(f"OK: {out}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mmd",
        type=Path,
        default=Path("report/project-architecture.mmd"),
        help="Input .mmd path",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("report/assets/project-architecture.png"),
        help="Output .png path",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Puppeteer scale factor (e.g. 3 for ~4K)",
    )
    args = parser.parse_args()
    return render(args.mmd, args.out, args.scale)


if __name__ == "__main__":
    raise SystemExit(main())
