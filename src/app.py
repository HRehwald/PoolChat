# aquatics-assistant/src/app.py
"""
CLI entrypoint for Aquatics Services Assistant (prototype).

Run:
  python -m src.app
or (from repo root)
  python src/app.py
"""

from __future__ import annotations

import json
from pathlib import Path

from src.intents import classify_intent, extract_entities, Intent
from src.retrieval import retrieve_answer
from src.guardrails import apply_guardrails
from src.logger import log_interaction


REPO_ROOT = Path(__file__).resolve().parents[1]
KB_DIR = REPO_ROOT / "kb"

WEB_CHUNKS_PATH = KB_DIR / "web_chunks.json"
LOCAL_KB_PATH = KB_DIR / "local_kb.json"


def load_json(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def print_help():
    print(
        "\nCommands:\n"
        "  /help          Show this help\n"
        "  /topics        Show supported topics\n"
        "  /quit          Exit\n"
    )


def print_topics():
    print(
        "\nSupported topics:\n"
        "- Hours / schedules (lap swim, teen lap swim, recreation swim)\n"
        "- Fees / passes\n"
        "- Rules & policies (circle swim, age limits, diapers, lifejackets, glass)\n"
        "- Swim lessons (registration, refund policy overview, levels)\n"
        "- Facility info (address, phone, amenities, lockers)\n"
        "- Contact & escalation\n"
    )


def main():
    web_chunks = load_json(WEB_CHUNKS_PATH)  # list[dict]
    local_kb = load_json(LOCAL_KB_PATH)      # dict

    print("Aquatics Services Assistant (prototype)")
    print("Type /help for commands.\n")

    while True:
        q = input("Ask a question> ").strip()
        if not q:
            continue

        if q.lower() in ("/quit", "quit", "exit"):
            print("Goodbye.")
            return
        if q.lower() == "/help":
            print_help()
            continue
        if q.lower() == "/topics":
            print_topics()
            continue

        intent, intent_conf = classify_intent(q)
        entities = extract_entities(q)
        activity = entities[0].value if entities else "unknown"

        # Retrieve best candidate answer (may come from web or local KB)
        candidate = retrieve_answer(
            question=q,
            intent=intent,
            activity=activity,
            web_chunks=web_chunks,
            local_kb=local_kb,
        )

        # Apply guardrails (don’t guess, sensitive topics, low confidence -> escalate)
        final = apply_guardrails(
            question=q,
            intent=intent,
            intent_conf=intent_conf,
            candidate=candidate,
            local_kb=local_kb,
        )

        # Print response
        print("\n" + final["answer"])
        if final.get("source"):
            print(f"\nSource: {final['source']}")
        if final.get("escalation"):
            print(f"\nEscalation: {final['escalation']}")
        print()

        # Log interaction (JSONL)
        log_interaction(
            question=q,
            intent=intent,
            intent_conf=intent_conf,
            activity=activity,
            result=final,
        )


if __name__ == "__main__":
    main()
