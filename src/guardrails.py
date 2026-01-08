# aquatics-assistant/src/guardrails.py
from __future__ import annotations

import re
from typing import Any, Dict


SENSITIVE_PATTERNS = [
    r"\b(seizure|faint|pregnan|injur|blood|heart|asthma)\b",
    r"\b(sue|lawsuit|liabilit|legal advice)\b",
    r"\b(my account|my payment|credit card|refund status)\b",
]

LIVE_STATUS_PATTERNS = [
    r"\b(right now|currently|open now|closed now|status)\b"
]


def _matches_any(patterns: list[str], text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in patterns)


def apply_guardrails(
    question: str,
    intent,
    intent_conf: float,
    candidate: Dict[str, Any],
    local_kb: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Returns dict with:
      - answer (required)
      - source (optional)
      - escalation (optional)
      - decision: answered|escalated|refused
    """
    contacts = (local_kb or {}).get("facility", {})
    phone = contacts.get("phone")
    escalation_line = f"Please contact the front desk at {phone}." if phone else "Please contact the front desk."

    # 1) Sensitive topics: refuse + escalate
    if _matches_any(SENSITIVE_PATTERNS, question):
        return {
            "answer": "I can’t help with medical/legal/personal account questions. "
                      + escalation_line,
            "source": None,
            "escalation": escalation_line,
            "decision": "refused",
        }

    # 2) If we have no candidate answer, escalate (don’t guess)
    if not candidate.get("answer"):
        return {
            "answer": "I'm not confident I can answer that accurately. " + escalation_line,
            "source": None,
            "escalation": escalation_line,
            "decision": "escalated",
        }

    # 3) Low confidence retrieval or low intent confidence => escalate
    if candidate.get("confidence", 0.0) < 0.1 or intent_conf < 0.1:
        return {
            "answer": "I'm not fully confident in that answer. " + escalation_line,
            "source": candidate.get("source"),
            "escalation": escalation_line,
            "decision": "escalated",
        }

    # 4) Live status questions: provide info + escalate for confirmation
    if _matches_any(LIVE_STATUS_PATTERNS, question):
        return {
            "answer": candidate["answer"].strip() + "\n\nFor live status updates, " + escalation_line,
            "source": candidate.get("source"),
            "escalation": escalation_line,
            "decision": "escalated",
        }

    # Otherwise answer normally
    return {
        "answer": candidate["answer"].strip(),
        "source": candidate.get("source"),
        "escalation": None,
        "decision": "answered",
    }
