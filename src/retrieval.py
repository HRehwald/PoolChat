# src/retrieval.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
import re

# Maps web_chunks.json categories to boost keywords for scoring
BOOST = {
    # Web chunk categories
    "lap_swim": ["lap", "swim", "lane", "adult", "morning", "evening", "hours"],
    "teen_lap_swim": ["teen", "teenager", "youth", "guardian"],
    "fees": ["fee", "cost", "price", "pass", "resident", "non-resident", "$", "senior", "day pass"],
    "rules": ["rule", "allowed", "policy", "required", "circle", "swim test", "lifejacket", "diaper", "floaties"],
    "recreation_swim": ["recreation", "rec", "family", "child", "kid", "spectator", "season"],
}

def _tokenize(text: str) -> set[str]:
    # Simple tokenizer: words + numbers
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _score_overlap(query: str, text: str, extra_boost_terms: list[str] | None = None) -> float:
    q_tokens = _tokenize(query)
    t_tokens = _tokenize(text)
    if not t_tokens:
        return 0.0
    overlap = len(q_tokens & t_tokens)
    score = overlap / max(6, len(q_tokens))  # normalize by query length-ish

    if extra_boost_terms:
        q_lower = query.lower()
        for term in extra_boost_terms:
            if term and term.lower() in q_lower:
                score += 0.15

    return score


def _pick_best_web_chunk(question: str, web_chunks: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    best = None
    best_score = 0.0
    for ch in web_chunks:
        text = ch.get("text", "") or ""
        score = _score_overlap(question, text, BOOST.get(ch.get("category", ""), []))
        if score > best_score:
            best_score = score
            best = ch
    if best is None:
        return None
    best = dict(best)  # copy
    best["confidence"] = best_score
    return best


def _build_local_candidates(local_kb: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert local_kb.json entries into retrieval-friendly chunks.
    Expects local_kb with 'entries' array where each entry has:
      - id, intent, question, variations, answer, entities, keywords
    """
    chunks: List[Dict[str, Any]] = []

    entries = local_kb.get("entries", [])
    for entry in entries:
        # Build searchable text from question, variations, answer, and keywords
        text_parts = [entry.get("question", "")]
        text_parts.extend(entry.get("variations", []))
        text_parts.append(entry.get("answer", ""))
        text_parts.extend(entry.get("keywords", []))

        chunks.append({
            "id": entry.get("id", ""),
            "source": "staff_structured",
            "intent": entry.get("intent", ""),
            "entities": entry.get("entities", []),
            "answer": entry.get("answer", ""),
            "text": " ".join(text_parts),
        })

    return chunks


def _pick_best_local_chunk(question: str, local_kb: Dict[str, Any], activity: str) -> Optional[Dict[str, Any]]:
    local_chunks = _build_local_candidates(local_kb)
    best = None
    best_score = 0.0
    for ch in local_chunks:
        # Boost if the activity matches any entity in this entry
        boost = []
        entities = ch.get("entities", [])
        if activity != "unknown" and activity in entities:
            boost = [activity.replace("_", " ")]
        score = _score_overlap(question, ch.get("text", ""), boost)
        if score > best_score:
            best_score = score
            best = ch
    if best is None:
        return None
    best = dict(best)
    best["confidence"] = best_score
    return best


def retrieve_answer(
    question: str,
    intent,
    activity: str,
    web_chunks: List[Dict[str, Any]],
    local_kb: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Returns a candidate dict with:
      - answer
      - source
      - confidence
      - provenance fields
    """
    web_best = _pick_best_web_chunk(question, web_chunks)
    local_best = _pick_best_local_chunk(question, local_kb, activity)

    # Prefer website for "official-ish" topics when confidence is comparable.
    # These match intent values from local_kb.json
    prefer_website_intents = {
        "schedule_inquiry",      # Hours/schedules are best from website
        "policy_inquiry",        # Official rules/policies from website
        "eligibility_inquiry",   # Age requirements, swim tests from website
        "registration_inquiry",  # Registration info from website
    }
    website_preferred = getattr(intent, "value", str(intent)) in prefer_website_intents

    # Choose best by confidence, with a slight preference for website
    chosen = None
    if web_best and local_best:
        web_c = float(web_best.get("confidence", 0.0))
        loc_c = float(local_best.get("confidence", 0.0))
        if website_preferred and web_c >= (loc_c - 0.10):
            chosen = web_best
        else:
            chosen = web_best if web_c >= loc_c else local_best
    else:
        chosen = web_best or local_best

    if not chosen:
        return {
            "answer": "",
            "source": None,
            "confidence": 0.0,
            "provenance": None,
        }

    # Determine source label
    if chosen.get("source") == "website":
        src = f"Website: {chosen.get('title', 'curated content')}"
    else:
        src = "Staff notes (structured)"

    # Use dedicated 'answer' field for local_kb entries, otherwise use 'text'
    answer_text = chosen.get("answer") or chosen.get("text", "")

    return {
        "answer": answer_text.strip(),
        "source": src,
        "confidence": float(chosen.get("confidence", 0.0)),
        "provenance": chosen,
    }
