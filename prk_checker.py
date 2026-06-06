#!/usr/bin/env python3
"""Axezent AI Poly-Reduce Kernel (PRK).

Finite reduction-receipt checker for the launch pack:
3SAT -> CLIQUE.

Truth boundary:
This checker verifies submitted finite reduction receipts under a declared
rule set. It does not prove P vs NP, optimize all reductions, or certify
global solver correctness.
"""
from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

SCHEMA_ID = "AXEZENT-AI-PRK-RECEIPT-v1"
TRUTH_LABEL = "FINITE_REDUCTION_RECEIPT_CHECK"
REDUCTION_NAME = "3SAT_TO_CLIQUE"
IDENT_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")


@dataclass(frozen=True)
class VerificationReport:
    result: str
    errors: Tuple[str, ...]
    warnings: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result": self.result,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


def load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def parse_literal(literal: str) -> Tuple[str, bool]:
    """Return (variable, is_negated). Accepts x, !x, ~x, or ¬x."""
    if not isinstance(literal, str) or not literal:
        raise ValueError(f"literal must be a nonempty string: {literal!r}")
    negated = literal[0] in {"!", "~", "¬"}
    variable = literal[1:] if negated else literal
    if not IDENT_RE.match(variable):
        raise ValueError(f"invalid variable name in literal: {literal!r}")
    return variable, negated


def literal_is_complement(a: str, b: str) -> bool:
    va, na = parse_literal(a)
    vb, nb = parse_literal(b)
    return va == vb and na != nb


def literal_truth(literal: str, assignment: Mapping[str, bool]) -> bool:
    variable, negated = parse_literal(literal)
    value = bool(assignment[variable])
    return (not value) if negated else value


def edge_key(a: str, b: str) -> Tuple[str, str]:
    if a == b:
        raise ValueError("self-loop edge is not allowed")
    return tuple(sorted((a, b)))


def expected_nodes(formula: Mapping[str, Any]) -> List[Dict[str, Any]]:
    clauses = formula["clauses"]
    nodes: List[Dict[str, Any]] = []
    for ci, clause in enumerate(clauses, start=1):
        for li, literal in enumerate(clause, start=1):
            nodes.append({
                "id": f"c{ci}_l{li}",
                "clause_index": ci,
                "literal": literal,
            })
    return nodes


def expected_edges(nodes: Sequence[Mapping[str, Any]]) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    for a, b in itertools.combinations(nodes, 2):
        if int(a["clause_index"]) == int(b["clause_index"]):
            continue
        if literal_is_complement(str(a["literal"]), str(b["literal"])):
            continue
        out.append(edge_key(str(a["id"]), str(b["id"])))
    return sorted(set(out))


def canonical_node_set(nodes: Iterable[Mapping[str, Any]]) -> set[Tuple[str, int, str]]:
    result: set[Tuple[str, int, str]] = set()
    for node in nodes:
        result.add((str(node["id"]), int(node["clause_index"]), str(node["literal"])))
    return result


def canonical_edge_set(edges: Iterable[Sequence[str]]) -> set[Tuple[str, str]]:
    result: set[Tuple[str, str]] = set()
    for edge in edges:
        if not isinstance(edge, Sequence) or isinstance(edge, str) or len(edge) != 2:
            raise ValueError(f"edge must be a two-element list: {edge!r}")
        result.add(edge_key(str(edge[0]), str(edge[1])))
    return result


def validate_formula(formula: Mapping[str, Any]) -> List[str]:
    errors: List[str] = []

    variables = formula.get("variables")
    clauses = formula.get("clauses")

    if not isinstance(variables, list) or not variables:
        return ["formula.variables must be a nonempty list"]
    if not isinstance(clauses, list) or not clauses:
        return ["formula.clauses must be a nonempty list"]

    if len(set(variables)) != len(variables):
        errors.append("formula.variables contains duplicates")

    for variable in variables:
        if not isinstance(variable, str) or not IDENT_RE.match(variable):
            errors.append(f"invalid variable name: {variable!r}")

    variable_set = set(variables)
    for ci, clause in enumerate(clauses, start=1):
        if not isinstance(clause, list):
            errors.append(f"clause {ci} must be a list")
            continue
        if len(clause) != 3:
            errors.append(f"clause {ci} must contain exactly 3 literals for 3SAT")
            continue
        for literal in clause:
            try:
                variable, _ = parse_literal(literal)
            except ValueError as exc:
                errors.append(str(exc))
                continue
            if variable not in variable_set:
                errors.append(f"literal {literal!r} uses variable not in formula.variables")
    return errors


def validate_assignment(formula: Mapping[str, Any], assignment: Mapping[str, Any]) -> List[str]:
    errors: List[str] = []
    variables = formula["variables"]

    for variable in variables:
        if variable not in assignment:
            errors.append(f"assignment missing variable {variable!r}")
        elif not isinstance(assignment[variable], bool):
            errors.append(f"assignment value for {variable!r} must be boolean")

    for variable in assignment:
        if variable not in variables:
            errors.append(f"assignment contains variable not in formula: {variable!r}")

    if errors:
        return errors

    for ci, clause in enumerate(formula["clauses"], start=1):
        if not any(literal_truth(lit, assignment) for lit in clause):
            errors.append(f"assignment does not satisfy clause {ci}")
    return errors


def verify_receipt(receipt: Mapping[str, Any]) -> VerificationReport:
    errors: List[str] = []
    warnings: List[str] = []

    required = ["schema", "truth_label", "reduction", "formula", "constructed_instance", "witness"]
    missing = [field for field in required if field not in receipt]
    if missing:
        return VerificationReport("INCOMPLETE", tuple(f"missing required field: {m}" for m in missing), tuple())

    if receipt.get("schema") != SCHEMA_ID:
        errors.append(f"schema must be {SCHEMA_ID}")
    if receipt.get("truth_label") != TRUTH_LABEL:
        errors.append(f"truth_label must be {TRUTH_LABEL}")

    reduction = receipt.get("reduction", {})
    if not isinstance(reduction, Mapping) or reduction.get("name") != REDUCTION_NAME:
        errors.append(f"reduction.name must be {REDUCTION_NAME}")

    formula = receipt.get("formula", {})
    if not isinstance(formula, Mapping):
        return VerificationReport("REJECT", ("formula must be an object",), tuple(warnings))

    errors.extend(validate_formula(formula))
    if errors:
        return VerificationReport("REJECT", tuple(errors), tuple(warnings))

    constructed = receipt.get("constructed_instance", {})
    if not isinstance(constructed, Mapping):
        return VerificationReport("REJECT", ("constructed_instance must be an object",), tuple(warnings))

    if constructed.get("type") != "CLIQUE":
        errors.append("constructed_instance.type must be CLIQUE")

    clauses = formula["clauses"]
    expected_k = len(clauses)
    if constructed.get("k") != expected_k:
        errors.append(f"constructed_instance.k must equal number of clauses ({expected_k})")

    expected_node_list = expected_nodes(formula)
    expected_node_ids = {node["id"] for node in expected_node_list}
    expected_node_set = canonical_node_set(expected_node_list)

    nodes = constructed.get("nodes")
    edges = constructed.get("edges")
    if not isinstance(nodes, list):
        return VerificationReport("INCOMPLETE", ("constructed_instance.nodes must be a list",), tuple(warnings))
    if not isinstance(edges, list):
        return VerificationReport("INCOMPLETE", ("constructed_instance.edges must be a list",), tuple(warnings))

    try:
        actual_node_set = canonical_node_set(nodes)
    except Exception as exc:
        return VerificationReport("REJECT", (f"invalid node list: {exc}",), tuple(warnings))

    if actual_node_set != expected_node_set:
        missing_nodes = sorted(expected_node_set - actual_node_set)
        extra_nodes = sorted(actual_node_set - expected_node_set)
        if missing_nodes:
            errors.append(f"constructed graph missing expected nodes: {missing_nodes}")
        if extra_nodes:
            errors.append(f"constructed graph has extra nodes: {extra_nodes}")

    try:
        actual_edge_set = canonical_edge_set(edges)
    except Exception as exc:
        return VerificationReport("REJECT", (f"invalid edge list: {exc}",), tuple(warnings))

    expected_edge_set = set(expected_edges(expected_node_list))
    if actual_edge_set != expected_edge_set:
        missing_edges = sorted(expected_edge_set - actual_edge_set)
        extra_edges = sorted(actual_edge_set - expected_edge_set)
        if missing_edges:
            errors.append(f"constructed graph missing expected edges: {missing_edges[:10]}")
        if extra_edges:
            errors.append(f"constructed graph has extra edges: {extra_edges[:10]}")

    for a, b in actual_edge_set:
        if a not in expected_node_ids or b not in expected_node_ids:
            errors.append(f"edge references unknown node: {(a, b)}")

    witness = receipt.get("witness", {})
    if not isinstance(witness, Mapping):
        return VerificationReport("INCOMPLETE", ("witness must be an object",), tuple(warnings))

    assignment = witness.get("assignment")
    clique = witness.get("clique")
    if not isinstance(assignment, Mapping):
        return VerificationReport("INCOMPLETE", ("witness.assignment must be an object",), tuple(warnings))
    if not isinstance(clique, list):
        return VerificationReport("INCOMPLETE", ("witness.clique must be a list",), tuple(warnings))

    errors.extend(validate_assignment(formula, assignment))

    k = constructed.get("k")
    if isinstance(k, int):
        if len(clique) != k:
            errors.append(f"witness.clique length must equal k ({k})")
    if len(set(clique)) != len(clique):
        errors.append("witness.clique contains duplicate nodes")

    id_to_node = {str(node["id"]): node for node in expected_node_list}
    clause_indices_seen: set[int] = set()
    for node_id in clique:
        if node_id not in id_to_node:
            errors.append(f"witness.clique references unknown node {node_id!r}")
            continue
        node = id_to_node[node_id]
        ci = int(node["clause_index"])
        if ci in clause_indices_seen:
            errors.append(f"witness.clique chooses more than one node from clause {ci}")
        clause_indices_seen.add(ci)
        try:
            if not literal_truth(str(node["literal"]), assignment):
                errors.append(f"clique node {node_id!r} literal is false under assignment")
        except KeyError:
            pass

    for a, b in itertools.combinations([str(x) for x in clique], 2):
        try:
            ek = edge_key(a, b)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if ek not in actual_edge_set:
            errors.append(f"witness.clique is missing graph edge {(a, b)}")

    artifact_hashes = receipt.get("artifact_hashes", {})
    if artifact_hashes:
        if not isinstance(artifact_hashes, Mapping):
            errors.append("artifact_hashes must be an object when provided")
        else:
            for name, value in artifact_hashes.items():
                if not isinstance(value, str) or not SHA256_RE.match(value):
                    errors.append(f"artifact_hashes.{name} must be a 64-character SHA-256 hex string")

    result = "ACCEPT" if not errors else "REJECT"
    return VerificationReport(result, tuple(errors), tuple(warnings))


def command_verify(args: argparse.Namespace) -> int:
    try:
        receipt = load_json(args.receipt)
    except Exception as exc:
        report = VerificationReport("INCOMPLETE", (f"could not load receipt: {exc}",), tuple())
    else:
        report = verify_receipt(receipt)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(report.result)
        for error in report.errors:
            print(f"ERROR: {error}")
        for warning in report.warnings:
            print(f"WARNING: {warning}")

    if report.result == "ACCEPT":
        return 0
    if report.result == "REJECT":
        return 1
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Axezent AI Poly-Reduce Kernel receipt checker")
    sub = parser.add_subparsers(dest="command", required=True)

    verify = sub.add_parser("verify", help="verify a finite reduction receipt")
    verify.add_argument("receipt", help="path to receipt JSON")
    verify.add_argument("--json", action="store_true", help="emit machine-readable JSON report")
    verify.set_defaults(func=command_verify)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
