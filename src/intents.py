# src/intents.py
from __future__ import annotations

from enum import Enum
from typing import List, Tuple


class Intent(str, Enum):
    SCHEDULE_INQUIRY = "schedule_inquiry"
    POLICY_INQUIRY = "policy_inquiry"
    ELIGIBILITY_INQUIRY = "eligibility_inquiry"
    AMENITY_INQUIRY = "amenity_inquiry"
    AMENITY_AVAILABILITY = "amenity_availability"
    CONTACT_INQUIRY = "contact_inquiry"
    LOCATION_INQUIRY = "location_inquiry"
    REGISTRATION_INQUIRY = "registration_inquiry"
    UNKNOWN = "unknown"


INTENT_KEYWORDS = {
    Intent.SCHEDULE_INQUIRY: [
        "hours", "open", "close", "schedule", "time", "when",
        "morning", "evening", "weekday", "weekend",
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
    ],
    Intent.POLICY_INQUIRY: [
        "rule", "rules", "policy", "allowed", "permitted", "can i", "am i allowed",
        "circle swim", "share", "refund", "cancel", "lifejacket", "glass", "floaties"
    ],
    Intent.ELIGIBILITY_INQUIRY: [
        "age", "requirement", "how old", "need to be", "eligible", "qualify",
        "swim test", "deep water", "can my"
    ],
    Intent.AMENITY_INQUIRY: [
        "temperature", "warm", "cold", "heated", "lanes", "how many",
        "features", "slide", "kids", "children", "shallow"
    ],
    Intent.AMENITY_AVAILABILITY: [
        "is there", "do you have", "are there", "available",
        "diving board", "locker", "storage"
    ],
    Intent.CONTACT_INQUIRY: [
        "phone", "call", "contact", "reach", "number", "email"
    ],
    Intent.LOCATION_INQUIRY: [
        "address", "location", "where", "directions", "how do i get"
    ],
    Intent.REGISTRATION_INQUIRY: [
        "register", "sign up", "enroll", "lesson", "class", "how do i join"
    ],
}


class Entity(str, Enum):
    FACILITY = "facility"
    POOL = "pool"
    LAP_SWIM = "lap_swim"
    TEEN_LAP_SWIM = "teen_lap_swim"
    REC_SWIM = "rec_swim"
    LESSONS = "lessons"
    SAFETY = "safety"
    AMENITY = "amenity"
    CHILDREN = "children"
    DEEP_WATER = "deep_water"
    EQUIPMENT = "equipment"
    PROHIBITED = "prohibited"
    REFUND = "refund"
    REGISTRATION = "registration"
    SCHEDULE = "schedule"
    AGE = "age"
    RULES = "rules"
    GUARDIAN = "guardian"
    UNKNOWN = "unknown"


ENTITY_KEYWORDS = {
    Entity.LAP_SWIM: ["lap", "lap swim", "adult lap", "lanes", "swim laps", "speed", "slow"],
    Entity.TEEN_LAP_SWIM: ["teen", "teenager", "13", "14", "15", "16", "17", "youth"],
    Entity.REC_SWIM: ["recreation", "rec swim", "open swim", "family swim", "families"],
    Entity.LESSONS: ["lesson", "lessons", "class", "classes", "learn", "swim lessons", "levels", "level"],
    Entity.SAFETY: ["safety", "lifejacket", "swim test", "deep end", "flotation"],
    Entity.AMENITY: ["locker", "diving board", "slide", "features", "beach entry"],
    Entity.CHILDREN: ["kids", "children", "child", "toddler", "shallow"],
    Entity.FACILITY: ["pool", "facility", "center", "rpac", "aquatics center"],
    Entity.REFUND: ["refund", "money back", "cancel", "cancellation"],
    Entity.DEEP_WATER: ["deep", "deep water", "deep end"],
    Entity.EQUIPMENT: ["lifejacket", "flotation", "floaties", "vest"],
    Entity.PROHIBITED: ["glass", "bottle", "not allowed", "prohibited", "allowed"],
    Entity.GUARDIAN: ["parent", "guardian", "accompany"],
    Entity.AGE: ["age", "old", "years old", "18", "adult"],
}


def classify_intent(question: str) -> Tuple[Intent, float]:
    """
    Keyword-based intent classifier.
    Returns (intent, confidence in [0,1]).
    """
    q = question.lower()

    best_intent = Intent.UNKNOWN
    best_score = 0

    for intent, kws in INTENT_KEYWORDS.items():
        score = sum(1 for kw in kws if kw in q)
        if score > best_score:
            best_score = score
            best_intent = intent

    if best_score == 0:
        return Intent.UNKNOWN, 0.2
    if best_score == 1:
        return best_intent, 0.6
    if best_score == 2:
        return best_intent, 0.75
    return best_intent, 0.9


def extract_entities(question: str) -> List[Entity]:
    """
    Returns list of matched entities from the question.
    """
    q = question.lower()
    matched = []
    for entity, kws in ENTITY_KEYWORDS.items():
        if any(kw in q for kw in kws):
            matched.append(entity)
    return matched if matched else [Entity.UNKNOWN]


def classify(question: str) -> dict:
    """
    Full classification returning intent, entities, and confidence.
    """
    intent, confidence = classify_intent(question)
    entities = extract_entities(question)
    return {
        "intent": intent.value,
        "entities": [e.value for e in entities],
        "confidence": confidence,
    }
