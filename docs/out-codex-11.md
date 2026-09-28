Implemented the backend fixes. District overview rows are cached by district, horizon, and demand rule; writes to overview source records and demo reset invalidate the cache. Voice uploads now accept the requested audio types with codec parameters, including Chrome’s `audio/webm;codecs=opus`.

**Before/after**, using the same seeded in-memory app through TestClient: repeated overview calls fell from **3,064.5 / 3,125.7 ms** to **2.2 / 1.8 ms**. A cold call still takes about **4 seconds** after startup or invalidation. No local server was listening for a comparable curl run. The cache is per app process.

Ruff: `All checks passed!`  
Full pytest final line: `119 passed, 1 skipped, 1 warning in 79.76s (0:01:19)`

The changes and timings are recorded in [notes-codex.md](/Users/aditya/dev/refill-loop/docs/notes-codex.md). No commit, push, or deploy was performed.