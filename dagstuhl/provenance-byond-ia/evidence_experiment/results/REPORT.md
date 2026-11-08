# Controlled synthetic pilot results

120 graphs; 360 independent revision checks; seed 20261107.

| Method | Independence accuracy | Claim status accuracy | Abstention |
|---|---:|---:|---:|
| citation_count | 50.0% | 83.3% | 0.0% |
| untyped_ancestry | 66.7% | 100.0% | 16.7% |
| typed | 100.0% | 100.0% | 33.3% |
| without_types | 66.7% | 100.0% | 16.7% |
| without_coverage | 83.3% | 100.0% | 16.7% |

Revision equivalence and unrelated-claim preservation: True.

The oracle uses an independent path enumerator and a declared finite completion set. Perfect performance on this constructed suite is a semantic conformance result, not empirical evidence of real-world reliability.
The partial invalidation implementation still recomputes grounding globally. Timing results do not demonstrate an incremental speed-up.
Bootstrap intervals resample templates; repeated deterministic condition effects may produce degenerate intervals. Broader graph families and real annotation are needed.
