# aquatics-assistant/src/logger.py
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone


def log_interaction(question: str, intent, intent_conf: float, activity: str, result: dict) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    logs_dir = repo_root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "intent": getattr(intent, "value", str(intent)),
        "intent_conf": intent_conf,
        "activity": activity,
        "decision": result.get("decision"),
        "source": result.get("source"),
    }

    path = logs_dir / "interactions.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
