Updated the [seed](/Users/aditya/dev/refill-loop/backend/app/seed/data.py:103) so the six PHCs hold 0, 136, 280, 28, 110, and 25 metformin tablets respectively; the district store holds 1,500. The [donor selector](/Users/aditya/dev/refill-loop/backend/app/domain/transfers.py:19) now considers PHCs, keeping Nayagaon (`phc-2`) the sole feasible donor for Ramesh’s 30 tablets.

Regenerated [api-examples.md](/Users/aditya/dev/refill-loop/docs/api-examples.md). The Ramesh script completed through case closure, and the oversized request still returned `no_feasible_transfer`. These ran in-process because the sandbox blocked a local Uvicorn listener.

Ruff: `All checks passed!`  
Full pytest final line: `83 passed, 1 skipped, 1 warning in 57.04s`

The existing local SQLite database still has the old seed and four cases. A demo reset will load the new stock values but clear those cases, so I left it intact. I did not edit `frontend/` or commit, push, or deploy.