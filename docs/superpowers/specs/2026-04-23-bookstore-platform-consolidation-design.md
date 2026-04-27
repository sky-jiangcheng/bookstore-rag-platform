# BookStore Platform Consolidation Design

## Goal

Consolidate `bookstore-local-platform` into a single production-facing service with one external entrypoint, while keeping the repository modular internally.

The final platform should keep only the features that matter for the current core workflow:

- authentication and login
- intelligent book recommendations
- booklist generation and export

Anything not needed for that path should be removed from the production deployment graph.

## Scope

### Keep

- `apps/bookstore-frontend`
- `apps/bookstore-gateway` as the primary backend entry during migration
- `apps/bookstore-auth`
- recommendation/booklist logic that serves the core workflow
- shared utilities and data-access helpers

### Remove from the production path

- `apps/bookstore-catalog`
- `apps/bookstore-ops`
- standalone `apps/bookstore-rag`
- any deployment wiring that assumes these are separate public services

These modules can remain in the repository for reference during migration, but they should no longer be part of the deployed platform.

## Target Architecture

The consolidated platform will expose one public service:

- `/` serves the frontend
- `/api/*` serves backend APIs

Internally, the backend remains split by responsibility:

- authentication
- recommendation and booklist generation
- shared infrastructure and helpers

The frontend and backend should share the same origin in production so the app can avoid cross-origin complexity and hard-coded internal service URLs.

## Recommended Runtime Shape

The simplest production shape is:

- one Docker image for the public platform
- the backend process serves the API
- the built frontend assets are served by the same runtime or its companion web server
- one set of production environment variables

The implementation should avoid keeping unused runtime containers alive just because they existed in the old layout.

## Data and Integration Rules

- Keep the core auth and recommendation data paths intact.
- Remove runtime dependencies on catalog/ops/rag services for the production path.
- If a feature cannot be justified by the core workflow, do not keep it in the deployed service.
- Shared code should stay in shared modules instead of being copied into multiple entrypoints.

## Migration Plan

1. Flatten the production entrypoint to one service.
2. Rewire frontend build and backend hosting so they run under one origin.
3. Remove production references to catalog, ops, and standalone rag services.
4. Keep only the code paths required by login, recommendation, and export.
5. Verify the full flow end to end:
   - login
   - request recommendation
   - generate booklist
   - export booklist

## Risks

- The current codebase still assumes multiple services in a few places, especially in deployment and proxy configuration.
- Frontend API base URLs must be rewritten to match the new single-origin runtime.
- Some old helper code may still import catalog or ops paths even if the UI no longer uses them.

## Testing

The minimum validation set after consolidation should be:

- frontend build passes
- backend service starts in production-like mode
- login still works
- recommendation requests return booklists
- exported booklists contain the expected rows

## Success Criteria

The consolidation is complete when:

- only one public platform service is deployed
- the user can complete the login-to-export flow without cross-service routing
- unused modules are no longer part of the runtime path
- the repo remains modular enough to maintain internally, but the deployment surface is minimal
