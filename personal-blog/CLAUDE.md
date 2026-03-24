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
- Next.js 15 App Router — SSG with generateStaticParams, Server Components by default
- TypeScript strict mode — no `any`
- Tailwind CSS 4 + @tailwindcss/typography for prose styling
- MDX rendering via next-mdx-remote (serialize → MDXRemote)
- gray-matter for frontmatter parsing
- Shiki for code syntax highlighting (NOT Prism.js)
- Content files in content/posts/*.md — NOT in app/ directory
- Frontmatter: title, date, category, tags, slug, original_url
- Korean content — use Pretendard or system-ui font stack
- Dark/light mode via CSS variables + localStorage
- SEO: dynamic metadata per page, Open Graph, sitemap.xml, RSS feed
- Static generation: all blog posts built at build time
- Jest + React Testing Library for tests
- Include 3-5 sample markdown posts in content/posts/ for build/test

## Backpressure
All must pass before committing:
1. `npm run build` succeeds
2. `npm run test` — all tests pass
3. No `it.skip` or `describe.skip` tests unless documented in IMPLEMENTATION_PLAN.md
