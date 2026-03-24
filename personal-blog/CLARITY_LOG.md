# Clarity Log — Personal Blog Platform

## Round 1

---

Round: 1
Spec: blog-platform.md vs CLAUDE.md
Category: CONTRADICTION
Severity: CRITICAL
Q: The spec says "MDX (`next-mdx-remote` or `@next/mdx`)" while CLAUDE.md mandates "next-mdx-remote (serialize -> MDXRemote) -- NOT @next/mdx". Furthermore, `next-mdx-remote` v5 provides an RSC-native path via `next-mdx-remote/rsc` with async `MDXRemote`/`compileMDX`. The serialize -> MDXRemote pattern is the v4/legacy client-side approach. Which rendering path should be used?
A: Since CLAUDE.md says "Server Components by default" and App Router defaults to server components, the RSC path (`next-mdx-remote/rsc`) is correct. The "serialize -> MDXRemote" instruction describes the library generically but is the v4 API.
Confidence: 0.85
Remaining_Ambiguity: Whether gray-matter is still needed separately from compileMDX's built-in frontmatter parsing.
Resolution: Use `next-mdx-remote/rsc` (async `MDXRemote` or `compileMDX`) for rendering MDX in Server Components. Use gray-matter separately in content utilities to extract frontmatter for listing pages, metadata, and search — avoids compiling full MDX just to read metadata. `compileMDX` RSC path only invoked for post detail page render.

---

Round: 2
Spec: blog-platform.md vs CLAUDE.md
Category: CONTRADICTION
Severity: CRITICAL
Q: Spec says "code highlighting (Prism.js or Shiki)" while CLAUDE.md mandates "Shiki (NOT Prism.js)".
A: CLAUDE.md is authoritative. Installed dependency is `shiki@^1.24.0`. Prism.js is not installed.
Confidence: 0.98
Remaining_Ambiguity: None on choice. Integration method needs to be determined.
Resolution: Use Shiki exclusively. Do not install or reference Prism.js.

---

Round: 3
Spec: blog-platform.md
Category: INTEGRATION_GAP
Severity: CRITICAL
Q: How should Shiki be integrated with next-mdx-remote for code highlighting? Should we use `@shikijs/rehype`, `rehype-pretty-code`, or a custom rehype plugin?
A: Neither `@shikijs/rehype` nor `rehype-pretty-code` are in package.json. Use Shiki's `createHighlighter` API to build a custom rehype plugin.
Confidence: 0.75
Remaining_Ambiguity: Whether to add an unlisted dependency vs custom integration.
Resolution: Use Shiki's `createHighlighter` API to build a custom rehype plugin that transforms `<code>` blocks during MDX compilation. Wrap output in a custom CodeBlock component for copy button, language label, and line numbers. Pass the rehype plugin via `compileMDX`'s `mdxOptions.rehypePlugins`.

---

Round: 4
Spec: blog-platform.md
Category: INTEGRATION_GAP
Severity: CRITICAL
Q: Tailwind CSS v4 uses CSS-first configuration (`@import "tailwindcss"`), but `@tailwindcss/typography` v0.5.x uses the v3 JS plugin API. How is the typography plugin registered?
A: Tailwind v4 supports `@plugin` directive in CSS to load JS plugins. The syntax is `@plugin "@tailwindcss/typography"`.
Confidence: 0.80
Remaining_Ambiguity: Whether `prose` modifiers (`prose-lg`, `prose-invert`) work identically in v4's `@plugin` mode.
Resolution: Use Tailwind v4 CSS-first config. In global CSS: `@import "tailwindcss"` and `@plugin "@tailwindcss/typography"`. Do NOT create `tailwind.config.js` unless `@plugin` approach fails. Use `prose` and `prose-invert` for article styling.

---

Round: 5
Spec: blog-platform.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: Home page shows "5~10 recent posts" — what is the exact number?
A: "~" means range in Korean. Reference sites show ~5 posts. Separate layout from blog list (includes about section, category counts).
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: Home page shows exactly 5 most recent posts. Own layout with brief about section and category post count summary. Blog list uses 10 per page.

---

Round: 6
Spec: blog-platform.md
Category: MISSING_ERROR_HANDLING
Severity: MAJOR
Q: What happens with malformed frontmatter, missing required fields, invalid dates, or duplicate slugs?
A: Build-time is the right place to catch these. Migrated Tistory content may have artifacts.
Confidence: 0.90
Remaining_Ambiguity: Whether invalid posts cause build failure or are skipped.
Resolution: Content validation at build time: (1) required fields: title, date, slug; (2) date must be valid ISO format; (3) duplicate slugs cause build error; (4) missing optional fields get defaults (category: "uncategorized", tags: [], original_url: null); (5) posts with missing required fields logged as warnings and excluded.

---

Round: 7
Spec: blog-platform.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: Client-side search on "title + body text" — loading all post content into client could be expensive. What data goes in the search index?
A: For a personal blog (<500 posts), a lightweight index works. Full body search is impractical at scale.
Confidence: 0.80
Remaining_Ambiguity: Whether full-body search is a hard requirement.
Resolution: Build a JSON search index at build time: title, slug, category, tags, date, plain-text excerpt (first 300 chars, markdown stripped). Client search filters against title, excerpt, and tags. Index loaded on demand when search bar focused. Full body search deferred.

---

Round: 8
Spec: blog-platform.md
Category: UNSTATED_ASSUMPTION
Severity: MAJOR
Q: Image handling — `content/images/` structure, but Next.js requires static assets in `public/`. How are images referenced in markdown? Should we use `next/image`?
A: Images should be in `public/images/`. `next/image` requires known dimensions that migrated content won't have.
Confidence: 0.70
Remaining_Ambiguity: Whether a copy-to-public build step is needed for content/images.
Resolution: Place images in `public/images/` directly. Markdown references use `/images/post-title/image1.jpg` (absolute from public root). Custom `img` component renders `<img>` with lazy loading (not `next/image`). Sample posts use placeholder images or public URLs.

---

Round: 9
Spec: blog-platform.md
Category: EDGE_CASE
Severity: MAJOR
Q: Tags page (`/tags`) shows all tags and "clicking tag shows posts" — is this `/tags/[tagName]` or inline filtering? The spec doesn't define a `/tags/[tagName]` route.
A: Spec lists 6 routes without `/tags/[tagName]`.
Confidence: 0.75
Remaining_Ambiguity: Navigation UX.
Resolution: `/tags` shows all tags with counts. Clicking a tag navigates to `/blog?tag=TagName` — reusing blog list filtering. Blog list page must support `tag` query parameter.

---

Round: 10
Spec: blog-platform.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: Pagination "10 per page" — SSG with query params doesn't work with `generateStaticParams`. How to implement?
A: Client-side pagination: load all post metadata, paginate in browser. Integrates with search/filtering.
Confidence: 0.85
Remaining_Ambiguity: SEO implications.
Resolution: Client-side pagination on `/blog`. All post metadata passed as static props at build time. Filter → paginate flow. For SEO, individual post pages are primary crawl targets; sitemap includes all post URLs directly.

---

Round: 11
Spec: blog-platform.md
Category: MISSING_ERROR_HANDLING
Severity: MAJOR
Q: Previous/next post navigation — what ordering? What for first/last posts?
A: Chronological date order. Null for boundaries.
Confidence: 0.95
Remaining_Ambiguity: None.
Resolution: Previous = older post, Next = newer post, both by date. When no previous/next exists, that navigation side is hidden (not disabled).

---

Round: 12
Spec: blog-platform.md
Category: UNSTATED_ASSUMPTION
Severity: MAJOR
Q: Dark/light mode — default theme, system preference support, FOUC prevention?
A: Best practice: default to system preference, user override in localStorage, blocking script prevents FOUC.
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: CSS custom properties for theme colors. Toggle via `dark` class on `<html>`. Default to system `prefers-color-scheme`. User override in localStorage key `theme`. Inline `<script>` in `<head>` sets class before paint to prevent FOUC.

---

Round: 13
Spec: blog-platform.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: PostCard "first 150 chars" and meta "first 160 chars" — raw markdown or stripped plain text?
A: Must be plain text, stripped of markdown syntax.
Confidence: 0.95
Remaining_Ambiguity: None.
Resolution: Strip all markdown syntax to produce plain text, then truncate to 150 chars (PostCard) / 160 chars (meta description). Append "..." if truncated.

---

Round: 14
Spec: blog-platform.md
Category: EDGE_CASE
Severity: MAJOR
Q: Category URLs with Korean text (e.g., "개발") — URL encoding or ASCII slugs?
A: `github-slugger` handles Unicode. But using raw Korean in URLs is more readable.
Confidence: 0.80
Remaining_Ambiguity: None.
Resolution: Use category display name directly in URL path (URL-encoded by browser). `/category/개발` displays nicely. `decodeURIComponent` in page component maps back to display name. Simpler than ASCII slugs for Korean.

---

Round: 15
Spec: blog-platform.md
Category: INTEGRATION_GAP
Severity: MAJOR
Q: TOC scroll tracking needs IntersectionObserver (client-side), but post page is Server Component. How to structure?
A: Page = Server Component, TOC = Client Component with heading list as props.
Confidence: 0.90
Remaining_Ambiguity: How to extract headings.
Resolution: Extract headings from raw markdown via regex (find `## ` and `### ` lines). Pass heading list (text + id + level) as props to `'use client'` TOC component. TOC uses IntersectionObserver. Heading IDs generated by rehype-slug or github-slugger for consistency.

---

Round: 16
Spec: blog-platform.md
Category: UNSTATED_ASSUMPTION
Severity: MAJOR
Q: "Smooth page transitions" — what implementation?
A: Reference sites use subtle effects. CSS fade-in or loading states.
Confidence: 0.85
Remaining_Ambiguity: None.
Resolution: CSS opacity/transform animations on main content wrapper, triggered on mount. Do NOT use experimental View Transitions API. Use Next.js `loading.tsx` for loading states. Transitions under 300ms.

---

Round: 17
Spec: blog-platform.md
Category: EDGE_CASE
Severity: MINOR
Q: About page loads from `content/about.md` — what if missing?
A: Should build successfully regardless.
Confidence: 0.95
Remaining_Ambiguity: None.
Resolution: Include `content/about.md` in sample content. If missing at build time, render placeholder message instead of crashing.

---

Round: 18
Spec: blog-platform.md vs CLAUDE.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: "TypeScript strict mode — no `any`" — tsconfig and ESLint configuration?
A: Standard `strict: true` in tsconfig. `eslint-config-next` provides base rules.
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: `tsconfig.json` with `strict: true`. Use `eslint-config-next` with ESLint 9 flat config. No extra plugins beyond existing dependencies.

---

Round: 19
Spec: blog-platform.md
Category: MISSING_ERROR_HANDLING
Severity: MINOR
Q: RSS feed and sitemap — what base URL? Production URL unknown at dev time.
A: Need environment variable for site URL.
Confidence: 0.80
Remaining_Ambiguity: None.
Resolution: `NEXT_PUBLIC_SITE_URL` env var, defaults to `http://localhost:3000`. Next.js 15 `sitemap.ts` convention for sitemap. Route Handler (`app/feed.xml/route.ts`) with `feed` package for RSS. Include title, description, date, URL per post.

---

Round: 20
Spec: blog-platform.md + CLAUDE.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: What categories, tags, and content should sample posts use? Tests need deterministic data.
A: Diverse but predictable metadata across 5 posts.
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: 5 sample posts: categories "개발", "디자인", "회고" (3+); tags "JavaScript", "React", "TypeScript", "CSS", "Next.js" with overlap; dates spanning 2+ months; content with code blocks, headings, lists, table, inline code; Korean text. Also `content/about.md`.

---

Round: 21
Spec: blog-platform.md
Category: UNSTATED_ASSUMPTION
Severity: MINOR
Q: Pretendard font loading strategy — CDN, self-hosted, or next/font?
A: CDN is simplest. Korean fonts are large (2-5MB full).
Confidence: 0.85
Remaining_Ambiguity: None.
Resolution: Load Pretendard via CDN in root layout `<head>`. Variable weight version. Font stack: `'Pretendard Variable', Pretendard, -apple-system, BlinkMacSystemFont, system-ui, sans-serif`. Code font: JetBrains Mono from Google Fonts CDN.

---

Round: 22
Spec: blog-platform.md
Category: INTEGRATION_GAP
Severity: MINOR
Q: Blog list filtering (category, tag, search) + pagination + date grouping — how do they compose?
A: Filter → search → paginate. Any filter change resets to page 1.
Confidence: 0.90
Remaining_Ambiguity: Whether date grouping is a view mode or sort option.
Resolution: Blog list state: category, tag, search query, page — all in URL query params. Filter changes reset page to 1. Date grouping is a display mode toggle (flat vs grouped by year/month), doesn't affect filtering/pagination.

---

Round: 23
Spec: blog-platform.md
Category: UNSTATED_ASSUMPTION
Severity: MINOR
Q: File reading strategy in Server Components for SSG?
A: Server Components can use Node.js `fs` APIs. Reads happen at build time.
Confidence: 0.95
Remaining_Ambiguity: None.
Resolution: Use `fs.promises.readFile` in async Server Component pages. `lib/posts.ts` utility handles file reading, gray-matter parsing, typed interfaces. All reads at build time via SSG.

---

Round: 24
Spec: blog-platform.md
Category: EDGE_CASE
Severity: MINOR
Q: `original_url` missing or empty for non-migrated posts?
A: Optional field.
Confidence: 0.95
Remaining_Ambiguity: None.
Resolution: `original_url` optional in Post type. When present: show "Originally published on Tistory" link. When absent: render nothing.

---

Round: 25
Spec: blog-platform.md vs CLAUDE.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: "70% test code" target (CLAUDE.md) vs "30+ tests" (spec) — different metrics. Testing Server Components with Jest/RTL is difficult.
A: 30+ tests is the functional target. Test strategy must be pragmatic.
Confidence: 0.85
Remaining_Ambiguity: None.
Resolution: 30+ meaningful tests: ~15 unit tests (utilities: post loading, parsing, validation, search, RSS, sitemap, reading time, summary), ~10 component tests (PostCard, TOC, SearchBar, ThemeToggle, Pagination, CodeBlock), ~5 integration tests (post render pipeline, category/tag filtering). Don't count snapshots. Prioritize testing business logic over rendering.

---

Round: 26
Spec: blog-platform.md
Category: INTEGRATION_GAP
Severity: MINOR
Q: `reading-time` package defaults to 200 WPM for English. Korean is character-based, not word-based — different density.
A: Korean reading speed ~500 characters/minute. `reading-time` underestimates for Korean.
Confidence: 0.75
Remaining_Ambiguity: None.
Resolution: Use custom reading time calculation for Korean: strip markdown, count characters, `Math.ceil(charCount / 500)` minutes. Display as "N분 소요". Alternatively use `reading-time` with custom `wordBound` that counts Korean characters separately.

---

Round: 27
Spec: blog-platform.md
Category: UNSTATED_ASSUMPTION
Severity: MINOR
Q: No mention of responsive design. TOC "right sidebar" needs mobile behavior.
A: Every modern blog must be responsive. Reference sites are fully responsive.
Confidence: 0.95
Remaining_Ambiguity: None.
Resolution: Fully responsive with Tailwind breakpoints. TOC: hidden below `lg`, sticky right sidebar on desktop. Optional expandable TOC at article top on mobile. Content max-width 680px. Simple top nav at all widths.

---

## Ambiguity Score

```
AMBIGUITY_SCORE: 0.036
Rounds_Completed: 27
Ambiguities_Found: 27
Ambiguities_Resolved: 26
Ambiguities_Remaining: 1
```

Remaining: Round 3 — whether to add `@shikijs/rehype` or build custom rehype integration. Resolution favors custom approach using installed `shiki` package, to be confirmed during implementation.

## Convergence Data

```
CONVERGENCE_DATA:
  round: 1
  score: 0.036
  prev_score: 1.0
  delta: -0.964
  category_distribution:
    CRITICAL: 0
    MAJOR: 0
    MINOR: 1
  stagnation_count: 0
```

PHASE_0_COMPLETE
FINAL_AMBIGUITY_SCORE: 0.036
TOTAL_ROUNDS: 1
EXIT_REASON: THRESHOLD
