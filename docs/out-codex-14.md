The overview now uses forecast components primed at startup and reset. Historical writes invalidate only the affected facility and drug forecast; each request reads current stock and cases to build the rows. Seed insertion uses one transaction.

| Local request | Before | After |
| --- | ---: | ---: |
| Cold overview | 4,817.5 ms | 11.8 ms |
| Warm overview | 2.6 ms | 3.1 ms |
| Reset | 1,194.6 ms | 223.1 ms |

Overview after the full Ramesh flow took **28.4 ms**. Tests confirm the seeded and post-flow rows match the legacy calculation exactly. Measurements and cProfile findings are in [notes-codex.md](/Users/aditya/dev/refill-loop/docs/notes-codex.md). Render performance remains unmeasured.

Ruff: `All checks passed!`  
Full pytest final line: `113 passed, 1 skipped, 1 warning in 27.90s`

No commit, push, or deploy was performed.