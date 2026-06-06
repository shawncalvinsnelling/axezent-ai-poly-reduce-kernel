# Threat Model

Axezent AI PRK assumes an untrusted author or solver may submit an incorrect reduction receipt.

The checker is designed to catch:

- malformed formulas
- missing graph nodes
- extra graph nodes
- missing graph edges
- extra graph edges
- incorrect `k`
- unsatisfied assignments
- invalid clique witnesses
- hash fields that do not look like SHA-256 values

Out of scope:

- proving global algorithmic optimality
- proving all reductions are complete
- verifying hidden reasoning
- replacing peer review
