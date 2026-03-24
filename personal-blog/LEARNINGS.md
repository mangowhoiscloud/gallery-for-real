# Learnings

### Learning: next build and next lint require app/ directory
- Context: Implementing Item 1 (tsconfig, next.config, postcss config) — no app/ directory existed
- Discovery: Both `next build` and `next lint` fail with "Couldn't find any `pages` or `app` directory" before even running. The backpressure requires build to pass, so a minimal app/layout.tsx + app/page.tsx scaffold was necessary.
- Rule: When the project has no app/ directory, create a minimal scaffold (layout + page + globals.css) as part of the first session to unblock all subsequent items. This scaffold will be replaced by Items 2, 9, and 18.

### Learning: npm test passes without jest.config.ts
- Context: Item 3 creates jest.config.ts, but running npm test for Item 1 — no jest config exists
- Discovery: Jest defaults work for plain .js test files. TypeScript tests require ts-jest config (Item 3). Writing Item 1's tests in .js avoids the circular dependency.
- Rule: Write early infrastructure tests (Items 1-4) as .js files. Switch to .ts once Item 3 (jest.config.ts with ts-jest) is done.

### Learning: next lint prompts interactively without eslint.config.mjs
- Context: Item 2 (Tailwind/CSS) ran `npm run lint` for backpressure — no ESLint config yet (Item 3 creates it)
- Discovery: `next lint` enters an interactive setup wizard when no eslint.config.mjs is found, causing CI/non-TTY runs to hang or fail. Personal-blog backpressure only requires build + test, not lint.
- Rule: Don't run `npm run lint` as backpressure until Item 3 (eslint.config.mjs) is done. Items 1–2 can commit without lint passing.

### Learning: jest.config.ts requires ts-node to be explicitly installed
- Context: Item 3 — creating jest.config.ts so Jest runs TypeScript tests via ts-jest
- Discovery: Jest 29 parses jest.config.ts using ts-node under the hood, but ts-node is NOT bundled with jest or ts-jest. Without it, Jest errors with "ts-node is required for TypeScript configuration files."
- Rule: When using jest.config.ts (not .js), install ts-node as a devDependency. Alternatively, use jest.config.js with JSDoc type annotation (`/** @type {import('jest').Config} */`) to avoid the ts-node requirement.

### Learning: ESLint 9 flat config for Next.js 15 uses FlatCompat
- Context: Item 3 — creating eslint.config.mjs with ESLint 9 flat config
- Discovery: eslint-config-next 15 still uses the legacy sharable config format (index.js, core-web-vitals.js). Wrapping it via FlatCompat from @eslint/eslintrc (a transitive dep of eslint-config-next) bridges old-style configs to ESLint 9 flat config. This is the same pattern create-next-app generates.
- Rule: Use `FlatCompat.extends('next/core-web-vitals', 'next/typescript')` in eslint.config.mjs. @eslint/eslintrc is available without explicit install.

### Learning: next-mdx-remote needs no next.config changes
- Context: Item 1 description says "MDX support" in next.config — Socratic phase resolved MDX approach to next-mdx-remote
- Discovery: Unlike @next/mdx, next-mdx-remote is a React library that processes MDX at call time, not a webpack plugin. No next.config.ts changes needed.
- Rule: Keep next.config.ts minimal. next-mdx-remote setup is entirely in lib/ and page components.

### Learning: Jest toHaveProperty treats dots as nested path separators
- Context: Item 5 — testing getAllTags(), where tag keys contain dots (e.g., "Next.js")
- Discovery: `expect(obj).toHaveProperty('Next.js')` looks for `obj.Next.js` (nested), not `obj['Next.js']`. Jest's toHaveProperty uses dot notation as path navigation.
- Rule: For keys containing dots, use `expect(Object.keys(obj)).toContain('Next.js')` or `expect(obj['Next.js']).toBeDefined()` instead of toHaveProperty.

### Learning: Accept optional postsDir for testable fs-based functions
- Context: Item 5 — lib/posts.ts reads from content/posts/ using process.cwd()
- Discovery: Passing an optional `postsDir` parameter (defaulting to the real dir) allows tests to create real temp directories for edge cases (empty dir, non-.md files) without mocking fs. This avoids complex jest.mock() setup while still testing edge cases properly.
- Rule: For functions that read from a fixed directory, accept an optional dir parameter to enable clean unit testing without mocking.

### Learning: JavaScript Date silently overflows invalid days (2026-02-30 → March 2)
- Context: Item 6 — isValidISODate() in lib/validation.ts
- Discovery: `new Date('2026-02-30')` returns a valid Date (March 2, 2026), not NaN. The `isNaN(d.getTime())` check passes. Only UTC field comparison catches the overflow: `d.getUTCDate() !== 30`.
- Rule: To strictly validate ISO dates, compare parsed UTC year/month/day back against the original string parts. `new Date(str)` alone does not reject overflow dates.

### Learning: Testing ESM-only packages (shiki, unist-util-visit) in Jest CJS mode
- Context: Item 7 — writing unit tests for lib/shiki.ts which statically imports from shiki and unist-util-visit (both ESM-only)
- Discovery: Attempting `await import('shiki')` in Jest CJS mode fails with "Unexpected token 'export'" — Jest can't evaluate ESM files even via dynamic import. Using `jest.mock('shiki', factory)` with a factory function WORKS because Jest never evaluates the actual ESM file; it returns the factory output directly when any code requires that module ID. The factory approach works for both static imports and ts-jest-compiled dynamic imports.
- Rule: For ESM-only packages, always use `jest.mock('pkg', () => ({ ... }))` with a factory in test files. The factory prevents Jest from loading the real file. Also mock transitive ESM deps (e.g., unist-util-visit) the same way. The actual package is only used in the real build (Next.js, Node ESM context).

### Learning: tsc --noEmit fails on test files without @types/jest — pre-existing issue
- Context: Item 6 — running typecheck after adding __tests__/validation-markdown.test.ts
- Discovery: `@types/jest` is absent from devDependencies. tsc treats test globals (describe, it, expect) as unknown names. This was pre-existing since Item 3. Build and test both pass normally; only naked tsc fails.
- Rule: The backpressure for personal-blog is `npm run build` + `npm run test`, not `tsc --noEmit`. Don't block commits on tsc --noEmit until @types/jest is installed (Item 8 or separate fix).

### Learning: Next.js layout files only allow specific named exports
- Context: Item 9 — exporting THEME_SCRIPT as a named export from app/layout.tsx
- Discovery: Next.js build fails with "X is not a valid Layout export field" for any named export that isn't in the allowed set (metadata, generateMetadata, viewport, generateViewport, etc.). The default export must be the layout component.
- Rule: Never export non-metadata constants from app/layout.tsx. Move shared constants to lib/ files and import them in both layout.tsx and tests.

### Learning: Jest needs CSS and next/font mocks for importing layout files
- Context: Item 9 — layout.test.tsx imports app/layout.tsx which has CSS and next/font/google imports
- Discovery: Jest CJS mode can't parse @import CSS syntax or load next/font internals. Need to add `'\\.(css)$': fileMock` and `'^next/font/(.*)$': nextFontMock` to moduleNameMapper in jest.config.ts. A Proxy-based mock for next/font handles any exported font constructor call.
- Rule: When testing any component that imports CSS or next/font, ensure these are mapped in jest.config.ts moduleNameMapper. Create __mocks__/fileMock.js (returns {}) and __mocks__/next-font-mock.js (Proxy returning {className, variable, style}).

### Learning: @testing-library/user-event is not installed — use fireEvent
- Context: Item 14 — writing tests for CodeBlock copy button click
- Discovery: @testing-library/user-event is not in node_modules. Importing it causes a Jest module-not-found error.
- Rule: Use `fireEvent` from `@testing-library/react` for all click/change events. Pair with `await act(async () => { fireEvent.click(...) })` to flush async state updates (like Promise-based clipboard.writeText).

### Learning: JSX brace literals in children need expression wrapping
- Context: Item 14 — test file had `.foo { color: red }` as JSX child string
- Discovery: `<CodeBlock lang="css">.foo { color: red }</CodeBlock>` is a TypeScript parse error because `{` opens an expression context in JSX. Must wrap: `<CodeBlock lang="css">{'.foo { color: red }'}</CodeBlock>`.
- Rule: Any string child containing `{` or `}` must be wrapped in a JSX expression: `{'the { string }'}`.

### Learning: Mocking next/navigation (useRouter, useSearchParams) in Jest
- Context: Item 16 — SearchBar uses useRouter and useSearchParams from next/navigation
- Discovery: `jest.mock('next/navigation', () => ({ useRouter: jest.fn(), useSearchParams: jest.fn() }))` plus importing these hooks in the test file, then calling `(useRouter as jest.Mock).mockReturnValue(...)` in beforeEach works cleanly. No additional jest.config.ts moduleNameMapper entry is needed for next/navigation.
- Rule: Mock next/navigation hooks with jest.fn() factory, import them in the test, cast to jest.Mock for per-test configuration. This pattern handles all Next.js navigation hooks (useRouter, useSearchParams, usePathname, etc.).

### Learning: useSearchParams() requires Suspense boundary for SSG
- Context: Item 19 — blog list page with SearchBar/BlogListClient using useSearchParams()
- Discovery: Next.js 15 static page generation fails with "useSearchParams() should be wrapped in a suspense boundary" when a client component using useSearchParams() is rendered directly in a Server Component page. Error only appears at build time (next build), not during development or tests.
- Rule: Wrap any client component that uses useSearchParams() in <Suspense fallback={...}> at the page level in Server Components. This applies to direct usage and to child components (e.g., SearchBar inside BlogListClient).

### Learning: @ts-expect-error is flagged by Next.js build when directive is unused
- Context: Item 20 — post detail page using MDXRemote from next-mdx-remote/rsc (async RSC)
- Discovery: Adding `@ts-expect-error` when there is no actual TypeScript error causes `next build` to fail with "Unused '@ts-expect-error' directive." in strict mode. Next.js 15 + TypeScript correctly handles async RSC components returning `Promise<ReactElement>` in JSX without any special directive.
- Rule: Only use `@ts-expect-error` when there is an actual TypeScript error that cannot be avoided. Test without it first — Next.js async RSC typing works out of the box.

### Learning: Next.js 15 dynamic route params is a Promise — await before use
- Context: Item 20 — app/blog/[slug]/page.tsx
- Discovery: In Next.js 15, `params` in page components is typed as `Promise<{ slug: string }>` (not the synchronous object it was in Next.js 14). Accessing `params.slug` directly causes a TypeScript error; must `await params` first.
- Rule: Always type dynamic route props as `{ params: Promise<{ ... }> }` and `const { slug } = await params` at the top of the component.

### Learning: Jest jsdom environment lacks the Response global for Route Handler tests
- Context: Item 23 — testing the /feed.xml Route Handler which uses `new Response(...)` to return RSS XML
- Discovery: Jest's default jsdom environment does not provide the Web Fetch API `Response` constructor. Tests fail with "ReferenceError: Response is not defined". Node.js 18+ provides `Response` as a global, but Jest's jsdom overrides the environment.
- Rule: Add `/** @jest-environment node */` docblock to any test file that tests Next.js Route Handlers using `new Response(...)` or `NextResponse`. The node environment has the Fetch API globals. Route handler tests don't need DOM APIs so the switch is safe.
