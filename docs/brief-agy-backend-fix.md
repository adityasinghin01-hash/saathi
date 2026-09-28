You are standing in for the backend engineer (Codex is offline). Claude is the instructor.
Read docs/CONTRACT.md (especially "v0.2 decisions" item 7 and 8) and docs/notes-codex.md.

Task: exactly one failing test — `backend/tests/test_cases.py::test_stock_available_supply_deducts_stock`.
Run: `cd backend && .venv/bin/python -m pytest -q`. Find why the supply endpoint no longer writes the DispensingRecord the test expects (likely from the partial-supply change). Decide whether the CODE or the TEST is wrong according to the CONTRACT v0.2 (supply writes one DispensingRecord per supply call with the quantity handed over; stock snapshot deducted). Fix the minimal thing.

Rules: edit only files in backend/. Do not change docs/CONTRACT.md. Do not commit. Run the full suite at the end; all tests must pass. Append a short section "Antigravity fix" to docs/notes-codex.md: root cause, what you changed, final pytest summary line.
