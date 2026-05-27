from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_core import Agent


def main() -> None:
    agent = Agent.from_env()
    tokens: list[str] = []
    calls = 0

    def on_token(token: str) -> None:
        nonlocal calls
        calls += 1
        if token:
            tokens.append(token)
            print(f"[token {calls}] {token!r}")

    prompt = "請用繁體中文簡短回答：什麼是串流輸出？限 50 字內。"
    reply = agent.chat(prompt, on_token=on_token)

    print("\n=== summary ===")
    print(f"callback_calls={calls}")
    print(f"token_fragments={len(tokens)}")
    print(f"joined_text={''.join(tokens)!r}")
    print(f"final_reply={reply!r}")
    print(f"match={''.join(tokens).strip() == reply.strip()}")


if __name__ == "__main__":
    main()
