# Operational Guide

## How to Run
```bash
# Build
npm run build

# Run tests
npm test

# Lint
npm run lint

# Typecheck

```

## Project Type
node (package manager: npm)

## Architecture Decisions
- Next.js 15 App Router: Server Components default, "use client" only for interactive UI
- Page pattern: Server Component wrapper (page.tsx) with Suspense around Client Component (XxxPage.tsx)
- Tailwind CSS v4: CSS-based @theme tokens in globals.css, no tailwind.config.ts
- API client: centralized lib/api.ts with Base64 Basic Auth header injection, 16 typed endpoints
- Auth: sessionStorage default, localStorage on "Remember me", useSyncExternalStore for reactivity
- Error handling: typed errors (AuthError/NotFoundError/ApiRequestError), toast feedback, error boundaries
- Pagination: 0-indexed pages matching Spring Boot PageResponse format
- Testing: global mocks for next/link, next/image, @radix-ui/react-toast in jest.config.js moduleNameMapper
- Verified: 364 tests, 28 suites, all LEARNINGS applied, 67 spec criteria PASS

## Patterns to Follow
- Single source of truth: no adapters, no migrations
- Test-first: write test → implement → verify
- Atomic commits: one logical change per commit

## Anti-Patterns
- Don't duplicate utilities — check shared code first
- Don't modify test assertions to make tests pass
- Don't leave console.log/print debugging statements
