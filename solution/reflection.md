# Reflection (≤1 page)

Fill this in before you submit.

**Which fault types were hardest to catch, and why?**

The hardest cases are subtle lineage and feature/embedding drift instances that remain
close to the calibrated clean-stream range. I use the matching toolkit check, combine
structural lineage checks with runtime checks, and compare drift measurements against
the published baselines.

**What would you change about your cost/coverage tradeoff, if you had another pass?**

The defense spends one appropriately scoped RPC per event and stays under budget. With
another pass I would learn robust clean ranges from observations within the run, then
use them for subtle faults while keeping conservative alerts to limit false positives.
