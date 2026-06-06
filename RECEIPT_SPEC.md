# Axezent AI PRK Receipt v1

Schema name:

```text
AXEZENT-AI-PRK-RECEIPT-v1
```

Truth label:

```text
FINITE_REDUCTION_RECEIPT_CHECK
```

Launch reduction:

```text
3SAT_TO_CLIQUE
```

Required sections:

- `formula`
- `constructed_instance`
- `witness`
- `claim_boundary`
- `checker_expectation`

The checker compares the submitted graph against the graph reconstructed from the formula.
