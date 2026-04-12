# Repository Hygiene

This repository keeps generated artifacts out of version control to avoid noisy diffs and accidental submissions.

## Ignored generated paths

- `OpenEnv-upstream/` (temporary upstream clone/mirror)
- `submission-artifacts/` (generated pre-submit evidence outputs)
- `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`

## Working rule

- Keep source, tests, runtime config, and stable docs tracked.
- Treat reports and temporary mirrors as disposable local outputs.
