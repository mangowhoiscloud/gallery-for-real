# Implementation Plan
Generated: 2026-03-24T00:00:00Z
Total_Items: 25
Completed: 2
Test_Items: 18 (target: ≥70% of implementation items)

## Dependency Graph
```
Independent_Groups:
  - group_1: [Item 1, Item 2, Item 3, Item 4]           # infrastructure, no deps
  - group_2: [Item 5, Item 6, Item 7, Item 9]           # core lib + layout
  - group_3: [Item 8, Item 10, Item 11, Item 12, Item 13, Item 14, Item 15, Item 16, Item 25] # components + unit tests
  - group_4: [Item 17, Item 18, Item 19, Item 20, Item 21, Item 22, Item 23] # pages + SEO + component tests
  - group_5: [Item 24]                                   # integration tests
Build_Order: group_1 → group_2 → group_3 → group_4 → group_5
```

---

## Item 1: TypeScript + Next.js + PostCSS configuration
- status: DONE
- priority: P0
- complexity: S
- depends_on: []
- spec: specs/blog-platform.md
- clarity_ref: CLARITY_LOG.md#Round-18
- description: Create tsconfig.json with strict:true and path aliases (@/*), next.config.ts with MDX support and static export settings, and postcss.config.mjs for Tailwind CSS 4.
- acceptance: `npx tsc --noEmit` runs without config errors. `next.config.ts` exports valid configuration. PostCSS config references @tailwindcss/postcss.
- tests: Verify tsconfig strict mode enabled, path aliases resolve correctly.

## Item 2: Tailwind CSS 4 + global styles with theme variables
- status: DONE
- priority: P0
- complexity: S
- depends_on: []
- spec: specs/blog-platform.md
- clarity_ref: CLARITY_LOG.md#Round-3, CLARITY_LOG.md#Round-4
- description: Create app/globals.css with Tailwind v4 CSS-first configuration (@import "tailwindcss", @plugin "@tailwindcss/typography"). Define CSS custom properties for dark/light theme (--bg, --text, --accent, --code-bg, etc.). Set up typography prose styles with 680px max-width and 1.8 line-height.
- acceptance: Tailwind builds without errors. CSS variables switch between light and dark themes via `.dark` class on `<html>`. Prose content renders at 680px max-width.
- tests: CSS file parses correctly during build.

## Item 3: Jest + ESLint 9 configuration
- status: DONE
- priority: P0
- complexity: S
- depends_on: []
- spec: specs/blog-platform.md
- clarity_ref: CLARITY_LOG.md#Round-18
- description: Create jest.config.ts with ts-jest, jsdom environment, module name mapping for @/* paths, and setup file for React Testing Library. Create eslint.config.mjs with ESLint 9 flat config extending eslint-config-next.
- acceptance: `npm test -- --passWithNoTests` exits 0. `npm run lint` runs without config errors.
- tests: Jest discovers and runs a placeholder test file.

## Item 4: Sample markdown content
- status: DONE
- priority: P0
- complexity: M
- depends_on: []
- spec: specs/blog-platform.md
- clarity_ref: CLARITY_LOG.md#Round-20, CLARITY_LOG.md#Round-17
- description: Create 5 diverse sample posts in content/posts/*.md with proper frontmatter (title, date, category, tags, slug, original_url). Categories: "개발", "디자인", "회고". Dates spanning 2+ months. Korean text with code blocks, headings, lists, tables, images. Create content/about.md with author bio. Create placeholder images in public/images/.
- acceptance: All 5 posts have valid frontmatter with required fields. Posts contain diverse markdown elements (h2/h3, code, lists, tables). At least one post has original_url. Dates span 2+ months. content/about.md exists.
- tests: Content files exist and have valid frontmatter (verified by Item 8 unit tests).

## Item 5: Post type definitions + lib/posts.ts
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 1, Item 4]
- spec: specs/blog-platform.md
- clarity_ref: CLARITY_LOG.md#Round-23, CLARITY_LOG.md#Round-6
- description: Define Post and PostMeta TypeScript interfaces. Implement lib/posts.ts with functions: getAllPosts() returns sorted post metadata, getPostBySlug(slug) returns full post with content, getPostSlugs() for generateStaticParams, getCategories() returns category counts, getAllTags() returns tag counts. Use fs.promises.readFile + gray-matter. Sort by date descending.
- acceptance: getAllPosts() returns all 5 sample posts sorted by date. getPostBySlug() returns correct post content and metadata. getCategories()/getAllTags() return accurate counts.
- tests: Test getAllPosts sorting, getPostBySlug with valid/invalid slug, category and tag counting, empty content directory handling.

## Item 6: Content validation + markdown utilities
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 1]
- spec: specs/blog-platform.md
- clarity_ref: CLARITY_LOG.md#Round-6, CLARITY_LOG.md#Round-13, CLARITY_LOG.md#Round-15, CLARITY_LOG.md#Round-26
- description: Implement lib/validation.ts for build-time content validation (required fields: title, date, slug; ISO date format; no duplicate slugs; skip invalid with warnings). Implement lib/markdown.ts with utilities: generateExcerpt(content) strips markdown and truncates to 150 chars with "...", extractHeadings(content) parses h2/h3 from raw markdown via regex, calculateReadingTime(content) for Korean text (~500 chars/min, display as "N분 소요").
- acceptance: Validation catches missing required fields and duplicate slugs. Excerpt strips markdown syntax and truncates correctly. Heading extraction finds all h2/h3. Korean reading time calculates at 500 chars/min.
- tests: Validation with missing fields, duplicate slugs, invalid dates. Excerpt generation from various markdown. Heading extraction with nested headings. Reading time for Korean vs mixed content.

## Item 7: Shiki rehype plugin for code highlighting
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 1]
- spec: specs/blog-platform.md
- clarity_ref: CLARITY_LOG.md#Round-2
- description: Implement lib/shiki.ts as a custom rehype plugin using Shiki's createHighlighter API. Support dual themes (light and dark) for theme toggling. Handle language detection from code fence info strings. Cache the highlighter instance for build performance.
- acceptance: Code blocks in markdown render with Shiki syntax highlighting. Both light and dark theme styles are present. Language-specific highlighting works (typescript, javascript, bash, css at minimum).
- tests: Plugin transforms code blocks with language annotation. Handles missing language gracefully. Output contains Shiki theme classes.

## Item 8: Unit tests for lib/* utilities
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 5, Item 6, Item 7]
- spec: specs/blog-platform.md
- clarity_ref: CLARITY_LOG.md#Round-25
- description: Write ~15 unit tests covering all lib/ modules. Tests for posts.ts (loading, sorting, filtering, slug lookup), validation.ts (required fields, duplicates, date format), markdown.ts (excerpt generation, heading extraction, reading time), and shiki.ts (code highlighting output).
- acceptance: All 15+ unit tests pass. Tests cover happy paths, edge cases (empty content, missing fields, invalid data), and error conditions.
- tests: This IS a test item. Target: 15 meaningful unit tests across all lib/ modules.

## Item 9: Root layout with fonts + FOUC prevention
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 1, Item 2]
- spec: specs/blog-platform.md
- clarity_ref: CLARITY_LOG.md#Round-21, CLARITY_LOG.md#Round-12
- description: Create app/layout.tsx as root Server Component. Load Pretendard Variable via CDN link and JetBrains Mono via next/font/google. Add blocking `<script>` in `<head>` that reads localStorage 'theme' key and applies 'dark' class to prevent FOUC. Set default metadata (site title, description). Include globals.css import.
- acceptance: Layout renders with correct font stack. Theme script prevents flash on page load. Default metadata appears in `<head>`. Pretendard loads for Korean text, JetBrains Mono for code.
- tests: Layout renders children correctly. Meta tags present in head. Theme script exists in output.

## Item 10: ThemeToggle component
- status: DONE
- priority: P1
- complexity: S
- depends_on: [Item 2, Item 9]
- spec: specs/blog-platform.md
- clarity_ref: CLARITY_LOG.md#Round-12
- description: Create components/ThemeToggle.tsx as 'use client' component. Toggle between light/dark by adding/removing 'dark' class on `<html>` and persisting to localStorage key 'theme'. Use sun/moon icons. CSS opacity/transform transition <300ms.
- acceptance: Clicking toggles dark class on html element. Preference persists across page reloads via localStorage. Smooth icon transition animation.
- tests: Toggle updates document class. LocalStorage is written on toggle. Renders correct icon per theme state.

## Item 11: Navigation component
- status: DONE
- priority: P1
- complexity: S
- depends_on: [Item 9]
- spec: specs/blog-platform.md
- description: Create components/Navigation.tsx with links to Home (/), Blog (/blog), Tags (/tags), About (/about). Include ThemeToggle. Responsive: hamburger menu on mobile, horizontal links on desktop.
- acceptance: All navigation links render and point to correct routes. ThemeToggle is included. Responsive behavior works at mobile and desktop breakpoints.
- tests: All nav links render with correct href values. ThemeToggle is present.

## Item 12: PostCard component
- status: DONE
- priority: P1
- complexity: S
- depends_on: [Item 5, Item 9]
- spec: specs/blog-platform.md
- clarity_ref: CLARITY_LOG.md#Round-13
- description: Create components/PostCard.tsx displaying post title (linked to /blog/[slug]), date, category (linked to /category/[name]), tags, excerpt (150 chars), and reading time. Minimal tech blog style.
- acceptance: PostCard renders all post metadata fields. Title links to correct slug URL. Category links to correct category URL. Excerpt is truncated with "...". Reading time shows "N분 소요".
- tests: Renders title, date, category, tags, excerpt. Links point to correct URLs. Handles missing optional fields (original_url, tags).

## Item 13: Pagination component
- status: DONE
- priority: P1
- complexity: S
- depends_on: [Item 9]
- spec: specs/blog-platform.md
- clarity_ref: CLARITY_LOG.md#Round-10
- description: Create components/Pagination.tsx as 'use client' component. Accept totalItems, itemsPerPage (default 10), currentPage, onPageChange. Render page numbers with previous/next buttons. Disable buttons at boundaries.
- acceptance: Correct number of page buttons rendered. Previous disabled on page 1. Next disabled on last page. onPageChange fires with correct page number.
- tests: Renders correct page count. Boundary buttons disabled. Click fires callback with page number.

## Item 14: CodeBlock component with copy button
- status: DONE
- priority: P1
- complexity: S
- depends_on: [Item 7, Item 9]
- spec: specs/blog-platform.md
- description: Create components/CodeBlock.tsx as 'use client' component wrapping Shiki-highlighted code output. Add a copy-to-clipboard button that shows "Copied!" feedback for 2 seconds. Display language label. Style with JetBrains Mono font.
- acceptance: Copy button copies code text to clipboard. "Copied!" feedback appears and disappears. Language label displays. Code uses JetBrains Mono font.
- tests: Copy button calls navigator.clipboard.writeText. Feedback text appears after click. Language label renders.

## Item 15: TableOfContents component with scroll tracking
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 6, Item 9]
- spec: specs/blog-platform.md
- clarity_ref: CLARITY_LOG.md#Round-15, CLARITY_LOG.md#Round-27
- description: Create components/TableOfContents.tsx as 'use client' component. Accept headings array (id, text, level). Render nested h2/h3 list. Use IntersectionObserver to highlight the current section. Sticky positioning on desktop (lg+). Hidden below lg breakpoint; expandable toggle at article top on mobile.
- acceptance: TOC renders all headings with correct nesting. Clicking a heading scrolls to that section. Current section highlights on scroll. Sticky on desktop, expandable on mobile.
- tests: Renders headings list. Correct nesting for h2/h3. Active class applied based on intersection.

## Item 16: SearchBar component
- status: DONE
- priority: P1
- complexity: S
- depends_on: [Item 5, Item 9]
- spec: specs/blog-platform.md
- clarity_ref: CLARITY_LOG.md#Round-7
- description: Create components/SearchBar.tsx as 'use client' component. Accept posts metadata array. Filter by title, category, and tags on input. Debounce input (300ms). Display filtered results count. Update URL query param `q` for shareable search state.
- acceptance: Typing filters posts by title/category/tags. Debounced input (no filter on every keystroke). Results count updates. URL query param reflects search term.
- tests: Filtering matches title substring. Filtering matches category. Filtering matches tags. Empty query returns all posts.

## Item 17: Component tests
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 10, Item 11, Item 12, Item 13, Item 14, Item 15, Item 16]
- spec: specs/blog-platform.md
- clarity_ref: CLARITY_LOG.md#Round-25
- description: Write ~10 component tests using React Testing Library. Cover ThemeToggle (toggle behavior, persistence), PostCard (rendering, links), Pagination (page calculation, callbacks), CodeBlock (copy functionality), TableOfContents (heading rendering), SearchBar (filtering logic), Navigation (link rendering).
- acceptance: All 10+ component tests pass. Each component has at least one test. Tests verify user-facing behavior, not implementation details.
- tests: This IS a test item. Target: 10 meaningful component tests.

## Item 18: Home page
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 5, Item 12]
- spec: specs/blog-platform.md
- clarity_ref: CLARITY_LOG.md#Round-5
- description: Create app/page.tsx as Server Component. Display 5 most recent posts using PostCard. Show brief bio section. Show category summary with post counts (linked to /category/[name]). Static generation at build time.
- acceptance: Home page renders exactly 5 most recent posts. Bio section is visible. Category summary shows accurate counts. All links work. Page is statically generated.
- tests: Renders 5 post cards. Category counts are accurate. Bio section present.

## Item 19: Blog list page with filtering + pagination
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 5, Item 12, Item 13, Item 16]
- spec: specs/blog-platform.md
- clarity_ref: CLARITY_LOG.md#Round-10, CLARITY_LOG.md#Round-22
- description: Create app/blog/page.tsx. Load all post metadata at build time, pass to client components. Include SearchBar for filtering. Category and tag filter via URL query params (?category=X&tag=Y&q=Z&page=N). Client-side pagination at 10 posts per page. All filter/page state in URL query params.
- acceptance: All posts display with pagination (10/page). Category filter narrows results. Tag filter narrows results. Search filters by title/category/tags. Page state preserved in URL. Combining filters works correctly.
- tests: All posts render. Pagination shows correct page. Filters narrow results. URL params reflect state.

## Item 20: Post detail page with MDX + TOC + prev/next
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 5, Item 6, Item 7, Item 14, Item 15]
- spec: specs/blog-platform.md
- clarity_ref: CLARITY_LOG.md#Round-1, CLARITY_LOG.md#Round-11, CLARITY_LOG.md#Round-24
- description: Create app/blog/[slug]/page.tsx with generateStaticParams. Render post content via next-mdx-remote/rsc MDXRemote with Shiki rehype plugin. Display title, date, category, tags, reading time. Include TableOfContents from extracted headings. Previous/next navigation by date order (hidden at boundaries). Show "Originally published on Tistory" link when original_url present.
- acceptance: All sample posts render correctly with syntax-highlighted code. TOC displays and tracks scroll. Previous/next links navigate correctly. Reading time shows. Original URL link appears only when present. generateStaticParams builds all slugs.
- tests: Post renders with correct title and content. TOC headings match post. Prev/next links are correct. Original URL conditionally renders.

## Item 21: Category + Tags + About pages
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 5, Item 6, Item 12]
- spec: specs/blog-platform.md
- clarity_ref: CLARITY_LOG.md#Round-9, CLARITY_LOG.md#Round-14, CLARITY_LOG.md#Round-17
- description: Create app/category/[name]/page.tsx with generateStaticParams — filter posts by category, display with PostCard. Create app/tags/page.tsx — show all tags with counts, each linking to /blog?tag=TagName. Create app/about/page.tsx — render content/about.md via MDXRemote. Korean category names in URLs (URL-encoded by browser).
- acceptance: Category page shows only posts in that category. Tags page lists all tags with accurate counts. Tag links navigate to /blog?tag=X. About page renders markdown content. Korean URLs work correctly.
- tests: Category page filters correctly. Tags page shows all tags. About page renders content.

## Item 22: Dynamic metadata + Open Graph
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 5, Item 9]
- spec: specs/blog-platform.md
- clarity_ref: CLARITY_LOG.md#Round-19
- description: Add generateMetadata to all page routes. Include title, description, Open Graph tags (og:title, og:description, og:type, og:url). Use NEXT_PUBLIC_SITE_URL env var for canonical URLs. Post pages include article-specific OG tags. Home page includes site-level OG tags.
- acceptance: Each page has unique title and description in `<head>`. Open Graph tags present on all pages. Post pages have article-specific metadata. Canonical URLs use NEXT_PUBLIC_SITE_URL.
- tests: Metadata function returns correct title per page. OG tags include required fields. Missing NEXT_PUBLIC_SITE_URL falls back gracefully.

## Item 23: Sitemap + RSS feed
- status: DONE
- priority: P1
- complexity: S
- depends_on: [Item 5]
- spec: specs/blog-platform.md
- clarity_ref: CLARITY_LOG.md#Round-19
- description: Create app/sitemap.ts using Next.js 15 convention — returns all page URLs with lastModified dates. Create app/feed.xml/route.ts as Route Handler — generates RSS 2.0 feed using 'feed' package with all posts.
- acceptance: /sitemap.xml returns valid XML with all page URLs. /feed.xml returns valid RSS 2.0 with all posts. Both include correct URLs using NEXT_PUBLIC_SITE_URL.
- tests: Sitemap includes all post URLs. RSS feed contains all posts with correct structure. Both handle empty posts list.

## Item 24: Integration tests
- status: DONE
- priority: P2
- complexity: M
- depends_on: [Item 18, Item 19, Item 20, Item 21]
- spec: specs/blog-platform.md
- clarity_ref: CLARITY_LOG.md#Round-25
- description: Write ~5 integration tests verifying end-to-end flows: full post render pipeline (markdown → MDX → HTML with code highlighting), category filtering produces correct subset, tag filtering via /blog?tag=X works, search filtering returns relevant results, and build completes successfully with all static pages generated.
- acceptance: All 5+ integration tests pass. Tests verify real data flow through multiple modules. No mocking of internal modules.
- tests: This IS a test item. Target: 5 meaningful integration tests covering cross-module flows.

## Item 25: Loading states + error handling
- status: DONE
- priority: P2
- complexity: S
- depends_on: [Item 9]
- spec: specs/blog-platform.md
- clarity_ref: CLARITY_LOG.md#Round-16
- description: Create app/loading.tsx with CSS opacity/transform animation for page transitions. Create app/not-found.tsx for 404 pages. Create app/blog/[slug]/not-found.tsx for invalid post slugs. Transitions under 300ms.
- acceptance: Loading state appears during navigation. 404 page renders for invalid routes. Post-specific 404 renders for invalid slugs. Animations complete within 300ms.
- tests: Loading component renders. Not-found pages render with appropriate messages.

PHASE_1_COMPLETE
