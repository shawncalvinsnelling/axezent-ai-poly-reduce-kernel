# Axezent AI Poly-Reduce Kernel

**Axezent AI PRK** is an open-source finite reduction-receipt checker for computer science, mathematics, and engineering verification workflows.

The launch pack checks one classical reduction:

```text
3SAT → CLIQUE
```

The core principle is simple:

```text
No claim without a receipt.
```

An external solver or human author may construct a reduction instance. Axezent AI PRK does not blindly trust that construction. It requires a finite receipt and checks whether the submitted graph, parameter, witness, and local reduction rules match the declared 3SAT-to-CLIQUE specification.

```text
Claimed reduction
        ↓
finite receipt
        ↓
deterministic checker
        ↓
ACCEPT / REJECT / INCOMPLETE
        ↓
audit-ready result
```

## Truth Boundary

Axezent AI PRK does **not** claim to resolve P vs NP, prove global solver correctness, optimize every reduction, or automate all of complexity theory.

It verifies a narrower and stronger claim:

> Given a submitted finite 3SAT-to-CLIQUE receipt, the checker verifies whether the receipt obeys the declared deterministic reduction rules.

This is frontier computer mathematics and engineering built around finite receipts, reproducible examples, and strict claim boundaries.

## Quick Start

Run the passing demo:

```bash
python prk_checker.py verify passing_3sat_to_clique_receipt.json
```

Expected result:

```text
ACCEPT
```

Run failing demos:

```bash
python prk_checker.py verify failing_bad_edge_receipt.json
python prk_checker.py verify failing_bad_k_receipt.json
python prk_checker.py verify failing_bad_assignment_receipt.json
```

Expected result:

```text
REJECT
```

Run Python tests:

```bash
python -m pytest test_checker.py
```

Run Rust scaffold tests:

```bash
cargo test
cargo run
```

## What It Checks

For the launch 3SAT-to-CLIQUE reduction, PRK verifies:

- the 3SAT formula is well-formed
- every clause has exactly three literals
- one graph node exists for every literal occurrence
- graph edges match the textbook rule:
  - connect nodes from different clauses
  - do not connect complementary literals
- the CLIQUE parameter `k` equals the number of clauses
- the submitted assignment satisfies the formula
- the submitted clique has size `k`
- the submitted clique contains one true literal from each clause
- every clique pair is connected by a graph edge

## Included Files

```text
prk_checker.py                              Python reference checker
test_checker.py                             Python tests
passing_3sat_to_clique_receipt.json         passing example receipt
failing_bad_edge_receipt.json               failing missing-edge example
failing_bad_k_receipt.json                  failing parameter example
failing_bad_assignment_receipt.json         failing assignment example
axezent_ai_prk_receipt_v1.schema.json       JSON receipt schema
Cargo.toml, lib.rs, main.rs                 Rust runtime scaffold
GITHUB_WORKFLOW_MAIN.yml                    visible backup workflow
```

## Browser Upload Edition

This package is intentionally flat at the repository root so GitHub browser upload does not lose folder structure.

The intended workflow file is:

```text
.github/workflows/main.yml
```

If your operating system hides `.github`, create that file manually in GitHub and paste the contents of `GITHUB_WORKFLOW_MAIN.yml`.

## Donations

Optional donations support open-source development and maintenance.

Cash App:

```text
$Axezent
```

Donations are voluntary support. They do not create equity, tokens, investment rights, ownership rights, or guaranteed support obligations.

## Commercial / Enterprise Direction

The open-source kernel provides the public verification standard.

Commercial layers can include:

- signed reduction certificates
- private audit vaults
- hosted verification dashboards
- custom reduction packs
- educational tooling for complexity theory
- high-throughput streaming integrations
- enterprise proof-artifact storage

Contact: axezentai@Gmail.com

## License

MIT License. See `LICENSE`.
