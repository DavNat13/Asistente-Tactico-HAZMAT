"""Clasificación de complejidad (bajo/medio/alto) contra el set de evaluación."""

import json
from pathlib import Path

import pytest

from src.agent.router import classify

CASES = json.loads(
    (Path(__file__).parents[1] / "evals" / "hazmat_evals.json").read_text(
        encoding="utf-8"
    )
)["cases"]


@pytest.mark.parametrize(
    "case",
    [c for c in CASES if c["level"] in ("low", "medium", "high")],
    ids=lambda c: c["id"],
)
def test_eval_cases_level(case):
    assert classify(case["question"]).complexity == case["level"]


def test_entities():
    r = classify("¿Qué guía corresponde al UN 1203 y al ID 1017?")
    assert r.un_numbers == ["1203", "1017"]
    assert classify("Guía 128: ¿qué agente uso?").guides == ["128"]


def test_out_of_range_numbers_are_not_un():
    assert classify("código 9999 y 0042").un_numbers == []


def test_thanks_intent():
    r = classify("muchas gracias")
    assert r.complexity == "low" and r.intent == "gracias"
