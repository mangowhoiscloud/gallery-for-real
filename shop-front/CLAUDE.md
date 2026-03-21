# Project Rules

## Build & Test
Commands are defined in `.harness-config`. Run `cat .harness-config` to see current settings.

## Conventions
- Read AGENTS.md for operational guide
- Read IMPLEMENTATION_PLAN.md for current task state
- Read progress.txt for recent session context
- Read CLARITY_LOG.md for resolved ambiguities from Socratic phase

## Rules
- ONE task per session. Pick the highest-priority TODO from IMPLEMENTATION_PLAN.md
- Search before assuming something isn't implemented
- Write tests alongside implementation. Target: 70% test code
- Capture the WHY in commit messages, not just the what
- Keep AGENTS.md under 60 lines. State goes in IMPLEMENTATION_PLAN.md
- Implement completely. No placeholders, no stubs, no TODOs in code
- If unrelated tests fail, fix them in this session

## Stack-Specific Rules
- Next.js 15 App Router — use app/ directory, Server Components by default, "use client" only when needed
- TypeScript strict mode — no `any`, proper interfaces for all API responses
- Tailwind CSS 4 — utility-first, no inline styles, use design tokens in tailwind.config
- shadcn/ui — use Radix UI primitives via shadcn, install components as needed
- Frontend Design Skill active — leverage for Shopify-grade visual quality
- next/image for all images — proper width/height/alt attributes
- API client in lib/api.ts — centralized fetch with error handling and auth header
- Auth credentials stored in localStorage (Base64 encoded email:password)
- HTTP Basic Auth — attach Authorization header to all authenticated API calls
- Server Components for read-heavy pages (products), Client Components for interactive (cart, auth)
- Environment variable NEXT_PUBLIC_API_URL for backend URL
- Jest + React Testing Library for component tests
- NO CSS modules — Tailwind only

## Backpressure
All must pass before committing:
1. `npm run build` succeeds (no TypeScript errors)
2. `npm run test` — all tests pass
3. No `it.skip` or `describe.skip` tests unless documented in IMPLEMENTATION_PLAN.md
