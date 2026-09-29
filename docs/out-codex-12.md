Updated the 60 synthetic patient profiles with varied North-Indian names, matching Devanagari names, both sexes, and ages 35–75. `patient-001` remains Ramesh, 54 (`रमेश`). I added a [roster regression test](/Users/aditya/dev/refill-loop/backend/tests/test_seed.py), regenerated [API examples](/Users/aditya/dev/refill-loop/docs/api-examples.md), and updated the [handoff note](/Users/aditya/dev/refill-loop/docs/notes-codex.md). Existing populated databases need a demo reset to show the new seed. I did not edit `frontend/`.

Ruff: `All checks passed!`  
Full pytest final line: `120 passed, 1 skipped, 1 warning in 86.50s (0:01:26)`

I did not commit, push, or deploy. An external commit, `31585e3`, appeared during this turn; the handoff note remains uncommitted.