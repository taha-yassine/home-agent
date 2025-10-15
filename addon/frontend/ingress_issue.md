### Background and problem statement

Home Assistant serves add-ons behind a dynamic ingress path of the form `/api/hassio_ingress/<token>/`. Most SPAs assume they run at the web root `/` and that links, assets, and API/WS calls resolve from that root. When such an SPA is placed behind HA ingress, several issues appear:

- **Absolute URLs break**: Navigations like `/conversations` ignore the ingress prefix and jump to HA core, not the add-on.
- **API calls 404 or hit the wrong server**: Requests to `/api/...` go to HA Core instead of the add-on API unless prefixed properly.
- **Asset resolution breaks**: When JS chunks load from `/assets`, their own relative imports can resolve to `/assets/assets/...` and 404 when combined with a non-root base path.
- **Deep linking and reloads fail**: Direct loads of nested routes 404 unless the server provides an SPA fallback under the effective base path.
- **Dev vs ingress divergence**: Code that works in local dev at `/` fails under `/api/hassio_ingress/<token>/` due to path assumptions.

These are well-known pain points across ingress-enabled add-ons. Related discussion: `blakeblackshear/frigate#541` (ideas include injecting a `<base>` tag at serve time or using an ingress-aware proxy substitution; API calls must also be under the same base).

#### Goals
- Make routing, navigation, assets, and API/WS calls work seamlessly under the dynamic ingress prefix.
- Keep a good developer experience: the same code runs in dev at `/` with no special flags.
- Centralize path handling so new components do not need token-aware logic.

#### Constraints
- The ingress token is dynamic and cannot be hardcoded at build time.
- Prefer relative URLs for links, assets, API, and WebSockets so the browser resolves against the correct base.
- Avoid framework-specific hacks (e.g., static basenames) that don’t support a dynamic prefix.

### Ingress integration (current state)

This add-on is served under a dynamic ingress prefix: `/api/hassio_ingress/<token>/`. All SPA URLs (HTML, JS, CSS, images) and API/WS calls must work under that prefix. Reference: Home Assistant ingress and `X-Ingress-Path` header [`developers.home-assistant.io/docs/add-ons/presentation/#ingress`](https://developers.home-assistant.io/docs/add-ons/presentation/#ingress).

#### What we implemented
- Router
  - Conditional mount for dev vs. ingress:
    - In dev (local): the app mounts at the web root `/` with children exported directly (no parent wrapper route).
    - In prod (ingress): a parent route captures the dynamic token and nests the app at `api/hassio_ingress/:token`.
    - File: `addon/frontend/app/routes.ts` uses `import.meta.env.DEV` to export either bare `children` (dev) or `[route("api/hassio_ingress/:token", "routes/ingress.tsx", children)]` (prod).
    - Layout placement:
      - The global header/layout lives in `addon/frontend/app/root.tsx` (default export) so dev and prod share the same UI shell.
      - `addon/frontend/app/routes/ingress.tsx` is a minimal pass-through (just `<Outlet />`) used only to match `:token` in prod.
  - All client links and redirects remain relative (no leading `/`).

- Breadcrumbs (ingress-aware)
  - Breadcrumbs derive the ingress base from the `routes/ingress` match and strip it from labels.
  - Breadcrumb links are prefixed with the same base so navigation stays under ingress.
  - No hardcoded app root segments; adding new pages does not require changes.
  - File: `addon/frontend/app/components/Breadcrumbs.tsx`.
  - In dev, there is no `routes/ingress` parent, so the match is absent and the inferred base is empty; breadcrumbs gracefully fall back to app-relative paths.

- Shared ingress base hook + header navigation
  - Centralized base-path derivation in a shared hook so components do not reimplement logic.
  - The hook prefers the `routes/ingress` match and falls back to a regex on `location.pathname` when used at the root layout.
  - Files:
    - `addon/frontend/app/hooks/useIngressBase.ts`: exports `useIngressBasePath()`
    - `addon/frontend/app/components/Breadcrumbs.tsx`: uses the shared hook
    - `addon/frontend/app/components/Header.tsx`: uses the shared hook; all `NavLink` targets are prefixed with the ingress base in prod

- Backend `<base>` injection + SPA fallback (FastAPI)
  - Middleware inspects `X-Ingress-Path` (or falls back to `/`) and injects `<base href="<prefix>/">` into HTML responses, so the browser resolves all relative links, assets, and fetch URLs under the ingress prefix automatically.
  - Static assets are served under `/assets` without modification.
  - SPA fallback handles deep links: a catch-all GET route serves built files if present, otherwise returns `index.html` so routes like `/conversations` load the SPA instead of 404.
  - Files:
    - `addon/app/main.py`: `IngressBaseMiddleware`; mounts `/assets`; adds catch-all SPA fallback for non-API routes

- Frontend `<base>` in dev (React Router)
  - In local dev we mount at `/`. To ensure relative URLs (e.g., `fetch("api/...")`) resolve from the root regardless of the current nested route, we add a dev-only `<base href="/">` in the document head.
  - File: `addon/frontend/app/root.tsx` (within `<head>`): renders `<base href="/">` only when `import.meta.env.DEV` is true.

- Assets and chunk URLs
  - Root cause of prior `/assets/assets/...` 404s: chunks imported from `/assets` with further relative imports.
  - Fix: emit all JS (entry + chunks) at the build root; non-JS assets stay under `/assets`.
    - `addon/frontend/vite.config.ts`:
      - `base: "/"` in dev, `"./"` in build
      - `build.rollupOptions.output`: `entryFileNames: "[name]-[hash].js"`, `chunkFileNames: "[name]-[hash].js"`, `assetFileNames: "assets/[name]-[hash][extname]"`
  - Result: relative imports like `./assets/route.js` now resolve correctly under the ingress prefix.

- API calls
  - Use simple relative paths everywhere (no token logic in the client):
    - Examples: `fetch("api/frontend/...")`, `fetch("api/agent/...")`


#### Coding guidelines (to avoid regressions)
- Prefer relative `Link`/`NavLink`/`Navigate` and form actions; avoid leading `/`.
- Keep API/WS URLs relative to current origin.
- Do not assume the app runs at `/`; under HA it runs at `/api/hassio_ingress/<token>/` and the backend injects `<base>` accordingly.

#### Verification checklist
- Dev (local):
  - Initial load at `/` renders without a 404.
  - Relative API calls resolve to `/api/frontend/...` and `/api/agent/...` and reach the backend.
  - Assets load (JS at root, non-JS under `/assets/*`).
- Ingress (prod):
  - Initial load at `/api/hassio_ingress/<token>/` renders without a 404.
  - Client navigation preserves the token in the URL.
  - API calls resolve to `/api/hassio_ingress/<token>/api/frontend/...` automatically via the injected `<base>`.
  - Breadcrumbs show only app segments while links include the ingress base.
  - Deep links and reloads (e.g., `/conversations`) return `index.html` via the SPA fallback and hydrate correctly.

#### Follow-ups
- Audit websocket URLs (if any) to ensure they’re relative and thus base-aware.
- Add a brief note in the main README about backend `<base>` injection and the convention to use relative URLs.

This approach centralizes ingress handling on the backend, keeps the router minimal (one wrapper route), and simplifies the frontend by avoiding any token-aware link or fetch logic.