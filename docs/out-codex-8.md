Implemented the v0.5 backend contract: role-scoped patients, transfers, district series, and stock routes; bilingual `name_hi` values; and daily stock history shared with forecast censoring. The seed still has phc-1 out of metformin and exactly one feasible donor, phc-2. Regenerated [api-examples.md](/Users/aditya/dev/refill-loop/docs/api-examples.md) with the requested command.

Ruff: `All checks passed!`  
Full pytest: `82 passed, 1 skipped, 1 warning in 58.58s`

The `play_ramesh.py` flow passed against the final app in-process. A live-server run was blocked because the sandbox does not permit binding a local port. No frontend files were changed; nothing was committed, pushed, or deployed.