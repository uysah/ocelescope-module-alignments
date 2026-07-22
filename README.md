# Ocelescope instance template

A starter monorepo for running your own [Ocelescope](https://www.ocelescope.org)
instance and building your own modules.

It's a single repo with two workspaces:

- **Frontend** (pnpm) — the Next.js app in `app/`, plus your custom frontend
  modules in `frontend-modules/`.
- **Backend** (uv) — the published `ocelescope-backend` host, plus your custom
  Python modules in `backend-modules/`.

A bundled **example module** (frontend + backend) shows the full wiring,
including a typed API client. Copy it to start your own.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python ≥ 3.11)
- [pnpm](https://pnpm.io/) ≥ 8 and Node ≥ 20

## Getting started

```bash
cp .env.example .env                 # backend config (optional)
cp app/.env.example app/.env.local   # frontend config (optional)

pnpm run sync                        # install backend + frontend
pnpm run dev                         # run everything
```

The backend runs on <http://localhost:8000>, the frontend on
<http://localhost:3000>.

## Scripts

| Script | What it does |
| --- | --- |
| `pnpm run sync` | Full setup: backend then frontend. |
| `pnpm run dev` | Runs the backend and frontend together. |
| `pnpm run dev:modules` | Watch-rebuild local frontend modules while editing them. |
| `pnpm run build:modules` | Builds local frontend modules (regenerates their API clients). |

## Adding a module

A frontend module and its backend module come as a pair — the example shows the
full pattern (a backend `/hello` endpoint and a typed `useHello` hook generated
from the backend's OpenAPI schema).

**Frontend** — copy `frontend-modules/example`, rename it in its `package.json`,
then in `app/`:

1. add it to `dependencies` (`"@instance/your-module": "workspace:*"`),
2. register it in `app/ocelescope.config.ts`,
3. add it to `transpilePackages` in `app/next.config.ts`,
4. import its `styles.css` in `app/pages/_app.tsx` if it ships one.

**Backend** — copy `backend-modules/example`, rename the package and its entry
point in `pyproject.toml`, add it to the root `pyproject.toml` (`dependencies` +
a `[tool.uv.sources]` `{ workspace = true }` entry), then run `uv sync`.
