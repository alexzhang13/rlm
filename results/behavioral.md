# Behavioral analysis (Phase 8b)

## Adoption rates

| Arm | Uses term | Term hits | del | repl blocks | llm_q | rlm_q | batched | trace len | n |
|---|---|---|---|---|---|---|---|---|---|
| rlm_a0 | 0.00 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 137 | 6 |
| rlm_a1 | 0.00 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 256 | 6 |
| rlm_a3 | 0.00 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 139 | 6 |
| rlm_a4 | 0.00 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 294 | 6 |
| rlm_a6 | 0.00 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 4 | 6 |

## Cluster separation

- Within-arm mean pairwise distance: 0.095 (n=75)
- Between-arm mean pairwise distance: 0.089 (n=360)
- Ratio (between/within): 0.94   (>1.5 → arms behaviorally distinct)
