from __future__ import annotations

import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    port = sys.argv[1] if len(sys.argv) > 1 else "8001"
    cmd = ["uv", "run", "chainlit", "run", "chainlit_app.py", "--host", "127.0.0.1", "--port", port]
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        deadline = time.time() + 20
        status = None
        body_snippet = ""
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=2) as resp:
                    status = resp.status
                    body_snippet = resp.read(200).decode("utf-8", errors="replace")
                    break
            except Exception:
                time.sleep(1)
        print(f"status={status}")
        print(f"body_snippet={body_snippet!r}")
        return 0 if status == 200 else 1
    finally:
        proc.kill()
        try:
            out, _ = proc.communicate(timeout=5)
        except Exception:
            out = ""
        print("=== chainlit output ===")
        print(out[-3000:])


if __name__ == "__main__":
    raise SystemExit(main())
