# Contributing

This repository is on the `develop` branch for active work and uses `master` for release snapshots.

## Branching

- `develop`: default development branch
- `master`: release branch, only merged from reviewed/stable work
- `feature/<name>`: short-lived feature branches
- `hotfix/<name>`: urgent fixes branched from `master`

## Commit Style

- Use short imperative commit messages.
- Keep each commit focused on one concern.
- Prefer conventional prefixes when useful, for example `fix:`, `refactor:`, `docs:`, `test:`.

## Before You Commit

- Run the relevant tests for the files you changed.
- Keep `backend/tests` green when touching backend code.
- Avoid introducing new parallel implementations unless they replace an existing path.
- Do not commit generated artifacts such as `output/`, `logs/`, build outputs, or local config files.

## Release Flow

1. Merge or fast-forward `develop` into `master`.
2. Run the full test suite.
3. Create a version tag like `v1.2.3`.
4. Push `master` and the tag.
5. Keep `develop` as the next integration branch.
