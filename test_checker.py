from __future__ import annotations

import json
from pathlib import Path

import prk_checker

ROOT = Path(__file__).resolve().parent


def load_json(name: str):
    with (ROOT / name).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def test_passing_3sat_to_clique_receipt_accepts():
    receipt = load_json("passing_3sat_to_clique_receipt.json")
    report = prk_checker.verify_receipt(receipt)
    assert report.result == "ACCEPT"
    assert report.errors == ()


def test_bad_edge_receipt_rejects():
    receipt = load_json("failing_bad_edge_receipt.json")
    report = prk_checker.verify_receipt(receipt)
    assert report.result == "REJECT"
    assert any("missing expected edges" in err for err in report.errors)


def test_bad_k_receipt_rejects():
    receipt = load_json("failing_bad_k_receipt.json")
    report = prk_checker.verify_receipt(receipt)
    assert report.result == "REJECT"
    assert any("k must equal number of clauses" in err for err in report.errors)


def test_bad_assignment_receipt_rejects():
    receipt = load_json("failing_bad_assignment_receipt.json")
    report = prk_checker.verify_receipt(receipt)
    assert report.result == "REJECT"
    assert any("assignment does not satisfy clause" in err or "literal is false" in err for err in report.errors)
