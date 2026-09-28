Continue as backend engineer. You now HAVE network access for package installation.

1. Read docs/CONTRACT.md again — section "v0.2 decisions" answers your 8 questions. Update the code to match (partially_supplied, transfer cancelled, /cases/{id}/cancel, ops shape, horizon_days, demand_rule, rejection returns case to verified).
2. Create backend/.venv with python3.11, install `-e 'backend[dev]'`, run the FULL test suite and ruff. Fix every failure. Add tests for all v0.2 changes. Tests must actually pass — report real output.
3. Start the server locally once (uvicorn on port 8000), hit /api/v1/health and /api/v1/district/overview with a seeded district_officer header, confirm responses, then stop it.
4. Same rules as before: edit only backend/, tick TASKS.md boxes only for tasks that are verified by passing tests, update docs/notes-codex.md (replace the test summary with the real run output, list remaining questions). No commit, push or deploy.
