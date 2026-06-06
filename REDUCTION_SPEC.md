# 3SAT to CLIQUE Reduction Spec

For a 3CNF formula with `m` clauses, the standard reduction constructs a graph:

- one node for each literal occurrence in each clause
- an edge between two nodes if:
  - they come from different clauses, and
  - their literals are not complementary
- the target CLIQUE parameter is `k = m`

A satisfying assignment choosing one true literal from each clause maps to a clique of size `m`.

Axezent AI PRK v1 checks a finite receipt for this exact construction.
