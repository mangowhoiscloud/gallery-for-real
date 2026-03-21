# Learnings

### Learning: Jest config must be .js not .ts
- Context: Item 1 scaffolding, setting up Jest
- Discovery: `jest.config.ts` requires `ts-node` at runtime, which was not installed. Switching to `jest.config.js` with `/** @type {import('@jest/types').Config.InitialOptions} */` JSDoc gives full type hints without the dependency.
- Rule: Always use `jest.config.js` unless `ts-node` is explicitly installed as a devDependency.

### Learning: next lint requires eslint.config.mjs in Next.js 15
- Context: Item 1 scaffolding, setting up lint
- Discovery: Next.js 15 moved to flat ESLint config. Without `eslint.config.mjs`, `next lint` enters an interactive setup prompt and exits 1 in non-TTY mode.
- Rule: Always create `eslint.config.mjs` using FlatCompat + `next/core-web-vitals` + `next/typescript` when initializing a Next.js 15 project.

### Learning: Tailwind v4 CSS @theme syntax
- Context: Item 1 scaffolding, globals.css
- Discovery: Tailwind v4 uses `@import "tailwindcss"` + `@theme { ... }` CSS blocks instead of a JS tailwind.config. Custom tokens use CSS custom property names like `--color-primary`, `--font-sans`, etc.
- Rule: No tailwind.config.ts needed. Put all design tokens in `app/globals.css` under `@theme { ... }`.

### Learning: Jest testMatch picks up all .ts files in __tests__/
- Context: Item 2 types, creating test factory helpers
- Discovery: Jest's default testMatch `**/__tests__/**/*.{ts,tsx}` matches every TypeScript file in the `__tests__/` directory, including non-test helper files. A file with no `describe`/`it` blocks causes Jest to fail with "Your test suite must contain at least one test."
- Rule: Place test helper/factory files in `lib/test-factories.ts` (or a `test-utils/` directory at the repo root), NOT inside `__tests__/`. Only actual test files (*.test.ts) go in `__tests__/`.

### Learning: fetch is not natively available in jest-environment-jsdom 29.7.0
- Context: Item 3, API client tests
- Discovery: jest-environment-jsdom 29.7.0 uses jsdom 20.x which does NOT include `fetch`. Calling fetch without a mock throws `ReferenceError: fetch is not defined`. No polyfill is needed if you're fully mocking fetch — just set `global.fetch = jest.fn()` in `beforeAll`.
- Rule: In API client tests, always declare `global.fetch = jest.fn()` in `beforeAll` and `(global.fetch as jest.Mock).mockReset()` in `beforeEach`. Do not assume fetch is globally available.

### Learning: btoa() is available in jsdom test environment
- Context: Item 3, testing Base64 encoding in login()
- Discovery: `btoa()` (browser-native Base64 encoder) is available in jsdom without any polyfill. No need to use `Buffer.from(str).toString('base64')` in test assertions.
- Rule: Use `btoa()` directly in test files running under jsdom environment.

### Learning: next/link and next/image need global mocks in jest.config.js
- Context: Item 5, testing Header and Footer components
- Discovery: next/link and next/image require Next.js internals that aren't available in jsdom. Mocking them via moduleNameMapper in jest.config.js with simple <a> and <img> wrappers prevents errors without needing per-file jest.mock() calls.
- Rule: Add `'^next/link$': '<rootDir>/__mocks__/nextLink.tsx'` and `'^next/image$': '<rootDir>/__mocks__/nextImage.tsx'` to moduleNameMapper in jest.config.js for all Next.js projects. Create the mock files once; all future component tests benefit automatically.

### Learning: Multiple buttons with same aria-label require getAllByRole in tests
- Context: Item 5, Header has two "Toggle theme" buttons (desktop + mobile)
- Discovery: When a component renders the same logical button in both desktop and mobile layouts (hidden via CSS), jsdom renders both. screen.getByRole() throws "multiple elements found". Use getAllByRole(...)[0] or check length with toBeGreaterThanOrEqual(1).
- Rule: For responsive components with duplicate interactive elements, use getAllByRole() in tests and access by index, or assign distinct aria-labels to the mobile version if it needs different accessibility semantics.

### Learning: Next.js async server pages need force-dynamic when API is external
- Context: Item 8, home page with async server sub-components
- Discovery: Next.js 15 tries to statically pre-render all pages at build time by default. When a page (or its async sub-components) calls an external API, the build times out if the API is not running. Adding `export const dynamic = 'force-dynamic'` to the page module opts it into server-side rendering on every request.
- Rule: Always add `export const dynamic = 'force-dynamic'` to Next.js pages that fetch external API data, unless the data is truly static and cacheable at build time.

### Learning: window.matchMedia must be stubbed in ThemeProvider tests
- Context: Item 5, ThemeProvider tests
- Discovery: jsdom does not implement window.matchMedia. ThemeProvider calls it in useEffect to detect system dark preference. Without a stub, the call throws TypeError. Must add Object.defineProperty(window, 'matchMedia', ...) in the test file before rendering.
- Rule: Any component that calls window.matchMedia must stub it in tests. Put the stub in a helper function called in beforeEach so tests can vary the matches return value (true/false for prefersDark).

### Learning: Filter chips with aria-labels conflict with getByLabelText on form controls
- Context: Item 10, product listing page tests with active filter chips
- Discovery: When a page has both a `<label for="category">` on a `<select>` AND a filter chip `<button aria-label="Remove Category: Electronics filter">`, `screen.getByLabelText(/category/i)` matches both elements. This causes "Found multiple elements" errors.
- Rule: When filter chips coexist with form controls that share overlapping label text, use role-based selectors (`screen.getByRole('combobox', { name: /category/i })` for `<select>`, `screen.getByRole('textbox', { name: /search/i })` for `<input type="text">`) to disambiguate in tests.

### Learning: findByText throws on multiple matches — use findAllByText or unique selectors
- Context: Item 14, order detail tests
- Discovery: `screen.findByText('Order #1001')` times out (instead of failing immediately) when there are multiple matching elements (heading + breadcrumb both contain "Order #1001"). RTL's waitFor retries on "multiple elements" errors as if they're "not found" errors, causing a 1000ms timeout. Use `findAllByText` when multiple matches are expected, or use a unique text/role that appears only once.
- Rule: When a page repeats the same text (breadcrumb + heading pattern), use `findAllByText` or query by a unique attribute. Never rely on `findByText` for text that appears more than once on the page.

### Learning: fireEvent.click on a stale element reference doesn't re-render
- Context: Item 14, testing expand/collapse toggle
- Discovery: Storing a button reference with `const toggle = getByRole('button', { expanded: false })` and clicking it twice (expand then collapse) fails on the second click because React updated the button's `aria-expanded` attribute in place. The second `fireEvent.click(toggle)` fires but the state update isn't reflected if you use `waitFor` between clicks. Re-querying with `getByRole('button', { expanded: true })` after the expand picks up the correct element.
- Rule: After a state-changing click that mutates an element's attributes, re-query the element before the next interaction (e.g., `getByRole('button', { expanded: true })` instead of reusing the old reference).

### Learning: Avoid test data where line total === order total
- Context: Item 14, order detail test "renders item list with product names and line totals"
- Discovery: When the makeOrder factory's single item price × quantity equals totalAmount, `getByText(/\$59\.97/)` finds two elements (the line total paragraph AND the "Total: $59.97" paragraph) causing "Found multiple elements" error.
- Rule: In order-related tests, set `totalAmount` to a value different from any individual line total (e.g., add simulated shipping) to avoid duplicate text matches.
