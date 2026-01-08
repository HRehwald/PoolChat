# aquatics-assistant/tests/run_tests.py
from __future__ import annotations

import json
from pathlib import Path

from src.intents import classify_intent, extract_entities
from src.retrieval import retrieve_answer
from src.guardrails import apply_guardrails


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main():
    repo_root = Path(__file__).resolve().parents[1]
    web_chunks = load_json(repo_root / "kb" / "web_chunks.json")
    local_kb = load_json(repo_root / "kb" / "local_kb.json")
    tests = load_json(repo_root / "tests" / "test_queries.json")

    passed = 0
    for i, t in enumerate(tests, start=1):
        q = t["question"]
        expected = t["expected_outcome"]

        intent, intent_conf = classify_intent(q)
        entities = extract_entities(q)

        cand = retrieve_answer(q, intent, entities, web_chunks, local_kb)
        final = apply_guardrails(q, intent, intent_conf, cand, local_kb)

        ok = final["decision"] == expected
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {i:02d} expected={expected} got={final['decision']} :: {q} : {cand}")

        if ok:
            passed += 1

    print(f"\n{passed}/{len(tests)} tests passed.")


if __name__ == "__main__":
    main()
