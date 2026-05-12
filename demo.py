#!/usr/bin/env python3
"""Tiny LongMemEval-style benchmark for an Islo/Harbor demo.

This is intentionally small and deterministic. It is not an official
LongMemEval score; it is a 60-second smoke test that makes memory failures
easy to inspect.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


UNKNOWN = "not enough information"
OUT_DIR = Path("runs/latest")
SITE_ASSET_DIR = Path("site/assets")


@dataclass(frozen=True)
class Session:
    id: str
    at: str
    speaker: str
    text: str


@dataclass(frozen=True)
class Question:
    id: str
    ability: str
    prompt: str
    expected: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class Answer:
    value: str
    evidence_ids: tuple[str, ...]
    rationale: str


SESSIONS = [
    Session(
        "s1",
        "2026-04-02T09:00:00Z",
        "user",
        "Mira's study group meets Friday. She asked me to bring sea-salt pistachios.",
    ),
    Session(
        "s2",
        "2026-04-05T18:30:00Z",
        "user",
        "For the Portland trip, I first planned to fly from SFO because the morning train is easy.",
    ),
    Session(
        "s3",
        "2026-04-07T08:15:00Z",
        "assistant",
        "Reminder saved: Portland trip airport is SFO unless plans change.",
    ),
    Session(
        "s4",
        "2026-04-09T21:10:00Z",
        "user",
        "Update for Portland: use OAK instead of SFO. Construction near SFO makes OAK safer.",
    ),
    Session(
        "s5",
        "2026-04-11T12:00:00Z",
        "user",
        "Sam borrowed my small carry-on bag for the weekend.",
    ),
]


QUESTIONS = [
    Question(
        "q_direct",
        "direct memory lookup",
        "What snack should I buy for Mira's study group?",
        "sea-salt pistachios",
        ("s1",),
    ),
    Question(
        "q_update",
        "knowledge update",
        "For the Portland trip, which airport should I use now?",
        "OAK",
        ("s4",),
    ),
    Question(
        "q_abstain",
        "abstention",
        "What is Sam's jacket size?",
        UNKNOWN,
        (),
    ),
]


STOPWORDS = {
    "a",
    "an",
    "and",
    "for",
    "i",
    "is",
    "me",
    "my",
    "of",
    "s",
    "should",
    "the",
    "to",
    "what",
    "which",
}


def tokens(text: str) -> list[str]:
    return [word for word in re.findall(r"[a-z0-9]+", text.lower()) if word not in STOPWORDS]


def normalize(text: str) -> str:
    return " ".join(tokens(text))


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def lexical_score(question: Question, session: Session) -> int:
    q_terms = Counter(tokens(question.prompt))
    s_terms = Counter(tokens(session.text))
    return sum(min(q_terms[term], s_terms[term]) for term in q_terms)


def matching_sessions(question: Question) -> list[tuple[int, Session]]:
    scored = [(lexical_score(question, session), session) for session in SESSIONS]
    return [(score, session) for score, session in scored if score > 0]


def extract_from_session(question: Question, session: Session) -> str:
    text = session.text.lower()
    if "snack" in question.prompt.lower() and "pistachios" in text:
        return "sea-salt pistachios"
    if "airport" in question.prompt.lower():
        if "oak" in text:
            return "OAK"
        if "sfo" in text:
            return "SFO"
    return UNKNOWN


def no_memory(question: Question) -> Answer:
    return Answer(
        value=UNKNOWN,
        evidence_ids=(),
        rationale="No persisted chat history is available, so the strategy abstains.",
    )


def keyword_memory(question: Question) -> Answer:
    matches = matching_sessions(question)
    if not matches:
        return Answer(UNKNOWN, (), "No session shared keywords with the question.")

    # Simple retrievers often pick the first strong lexical hit, even if it is stale.
    score, session = sorted(matches, key=lambda item: (-item[0], parse_time(item[1].at)))[0]
    answer = extract_from_session(question, session)
    if answer == UNKNOWN:
        return Answer(
            UNKNOWN,
            (),
            f"Top keyword-overlap session {session.id} did not contain an answerable fact.",
        )
    return Answer(
        value=answer,
        evidence_ids=(session.id,),
        rationale=f"Picked top keyword-overlap session {session.id} with score {score}.",
    )


def update_aware_memory(question: Question) -> Answer:
    matches = matching_sessions(question)
    if not matches:
        return Answer(UNKNOWN, (), "No relevant memory found, so the strategy abstains.")

    if "airport" in question.prompt.lower() or "now" in question.prompt.lower():
        session = sorted(matches, key=lambda item: parse_time(item[1].at), reverse=True)[0][1]
        return Answer(
            value=extract_from_session(question, session),
            evidence_ids=(session.id,),
            rationale=f"Detected an update-style question and used newest matching session {session.id}.",
        )

    score, session = sorted(matches, key=lambda item: (-item[0], parse_time(item[1].at)))[0]
    answer = extract_from_session(question, session)
    if answer == UNKNOWN:
        return Answer(UNKNOWN, (), "Retrieved memory did not contain an answerable fact.")
    return Answer(
        value=answer,
        evidence_ids=(session.id,),
        rationale=f"Used top keyword-overlap session {session.id} with score {score}.",
    )


FRAMEWORKS: dict[str, Callable[[Question], Answer]] = {
    "no_memory": no_memory,
    "keyword_memory": keyword_memory,
    "update_aware_memory": update_aware_memory,
}


def is_correct(answer: Answer, question: Question) -> bool:
    if question.expected == UNKNOWN:
        return normalize(answer.value) == normalize(UNKNOWN)
    return normalize(answer.value) == normalize(question.expected)


def run_benchmark() -> dict:
    per_framework = []
    for name, framework in FRAMEWORKS.items():
        rows = []
        correct = 0
        for question in QUESTIONS:
            answer = framework(question)
            passed = is_correct(answer, question)
            correct += int(passed)
            rows.append(
                {
                    "question_id": question.id,
                    "ability": question.ability,
                    "question": question.prompt,
                    "expected": question.expected,
                    "answer": answer.value,
                    "passed": passed,
                    "evidence_ids": list(answer.evidence_ids),
                    "expected_evidence_ids": list(question.evidence_ids),
                    "rationale": answer.rationale,
                }
            )
        per_framework.append(
            {
                "name": name,
                "correct": correct,
                "total": len(QUESTIONS),
                "accuracy": round(correct / len(QUESTIONS), 3),
                "results": rows,
            }
        )

    leaderboard = sorted(per_framework, key=lambda row: (-row["correct"], row["name"]))
    return {
        "title": "Tiny LongMemEval-style benchmark on Islo",
        "disclaimer": "This is a miniature deterministic demo, not an official LongMemEval score.",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sessions": [session.__dict__ for session in SESSIONS],
        "questions": [question.__dict__ for question in QUESTIONS],
        "leaderboard": leaderboard,
    }


def write_results(payload: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SITE_ASSET_DIR.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, indent=2, sort_keys=True)
    (OUT_DIR / "results.json").write_text(encoded + "\n", encoding="utf-8")
    (SITE_ASSET_DIR / "results.json").write_text(encoded + "\n", encoding="utf-8")


def print_summary(payload: dict) -> None:
    print(payload["title"])
    print(payload["disclaimer"])
    print()
    print("Leaderboard")
    for row in payload["leaderboard"]:
        print(f"- {row['name']}: {row['correct']}/{row['total']} ({row['accuracy']:.0%})")
    print()
    print("Wrote runs/latest/results.json and site/assets/results.json")


def main() -> None:
    payload = run_benchmark()
    write_results(payload)
    print_summary(payload)


if __name__ == "__main__":
    main()
