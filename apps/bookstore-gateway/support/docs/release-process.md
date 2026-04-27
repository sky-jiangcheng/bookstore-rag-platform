# Release Process

This project uses a simple two-branch flow:

- `develop` for ongoing work
- `master` for release snapshots

## Release Steps

1. Finish work on `develop`.
2. Run the test suite and confirm it is green.
3. Merge `develop` into `master`.
4. Create a version tag, for example `v1.0.1`.
5. Push `master` and the tag to `origin`.
6. Start the next cycle on `develop`.

## Versioning

- Use semantic version tags.
- Increment `patch` for bugfixes and cleanup.
- Increment `minor` for backward-compatible feature work.
- Increment `major` for incompatible changes.

## Notes

- Keep generated artifacts out of git.
- Keep release notes short and scoped to the tagged changes.
- Prefer one release tag per reviewed snapshot.
