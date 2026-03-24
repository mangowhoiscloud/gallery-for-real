/**
 * Integration tests — end-to-end data flow through multiple real modules.
 *
 * Rules:
 *  - Internal lib/* and components/* modules are NOT mocked.
 *  - Only Next.js framework externals (next/navigation) are mocked to allow
 *    importing SearchBar (which references useRouter at module scope).
 *  - All tests read real files from content/posts/ — no synthetic test data.
 */

// Mocking only the Next.js framework external — not internal modules
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  useSearchParams: jest.fn(() => ({ get: () => null, toString: () => '' })),
}));

import { getAllPosts, getPostBySlug, getCategories, getAllTags } from '@/lib/posts';
import { generateExcerpt, extractHeadings, calculateReadingTime } from '@/lib/markdown';
import { validatePosts } from '@/lib/validation';
import { filterPosts } from '@/components/SearchBar';

// ---------------------------------------------------------------------------
// Test 1 — Full post render pipeline (data layer)
// Flow: getPostBySlug → extractHeadings + calculateReadingTime + generateExcerpt
// ---------------------------------------------------------------------------
describe('Integration: full post render pipeline', () => {
  it('reads a post and passes it through all markdown utilities', async () => {
    const post = await getPostBySlug('nextjs-app-router-guide');
    expect(post).not.toBeNull();
    expect(post!.title).toBe('Next.js 15 App Router 완전 가이드');
    expect(post!.slug).toBe('nextjs-app-router-guide');
    expect(post!.original_url).toBeTruthy(); // this post has original_url
    expect(post!.content.length).toBeGreaterThan(100);

    // extractHeadings — real post has h2/h3 headings
    const headings = extractHeadings(post!.content);
    expect(headings.length).toBeGreaterThan(0);
    expect(headings.every((h) => h.level === 2 || h.level === 3)).toBe(true);
    expect(headings.every((h) => h.id && h.text)).toBe(true);
    // headings should not leak markdown syntax
    expect(headings.every((h) => !h.text.startsWith('#'))).toBe(true);

    // calculateReadingTime — must return "N분 소요" format
    const readingTime = calculateReadingTime(post!.content);
    expect(readingTime).toMatch(/^\d+분 소요$/);

    // generateExcerpt — long post → truncated to 150 chars + '...'
    const excerpt = generateExcerpt(post!.content);
    expect(excerpt).toMatch(/\.\.\.$/); // should be truncated
    expect(excerpt.length).toBe(153); // 150 chars + '...'
    expect(excerpt).not.toMatch(/^#+\s/); // no markdown heading syntax
    expect(excerpt).not.toMatch(/```/); // no code fence syntax
  });

  it('posts without original_url have content and a null original_url', async () => {
    const post = await getPostBySlug('tailwind-css-design-system');
    expect(post).not.toBeNull();
    expect(post!.original_url).toBeFalsy();
    // Markdown utilities still work for this post
    const headings = extractHeadings(post!.content);
    expect(headings.length).toBeGreaterThan(0);
    const excerpt = generateExcerpt(post!.content);
    expect(typeof excerpt).toBe('string');
    expect(excerpt.length).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// Test 2 — Validation pipeline with real content
// Flow: getAllPosts → validatePosts
// ---------------------------------------------------------------------------
describe('Integration: validation pipeline with real content', () => {
  it('all 5 sample posts pass validation with no warnings', async () => {
    const posts = await getAllPosts();
    expect(posts).toHaveLength(5);

    const result = validatePosts(posts);
    expect(result.warnings).toHaveLength(0);
    expect(result.valid).toHaveLength(5);

    for (const post of result.valid) {
      expect(post.title).toBeTruthy();
      expect(post.date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      expect(post.slug).toBeTruthy();
    }
  });

  it('getAllPosts returns posts sorted newest-first (date descending)', async () => {
    const posts = await getAllPosts();
    const timestamps = posts.map((p) => new Date(p.date).getTime());
    for (let i = 0; i < timestamps.length - 1; i++) {
      expect(timestamps[i]).toBeGreaterThanOrEqual(timestamps[i + 1]);
    }
    // Most recent post should be mdx-blog-architecture (2026-02-20)
    expect(posts[0].slug).toBe('mdx-blog-architecture');
    // Oldest post should be 2025-year-review (2025-12-15)
    expect(posts[posts.length - 1].slug).toBe('2025-year-review');
  });
});

// ---------------------------------------------------------------------------
// Test 3 — Category filtering pipeline
// Flow: getAllPosts + getCategories — verify consistency across both functions
// ---------------------------------------------------------------------------
describe('Integration: category filtering pipeline', () => {
  it('getCategories() counts match manual counting from getAllPosts()', async () => {
    const [posts, categories] = await Promise.all([getAllPosts(), getCategories()]);

    const manual: Record<string, number> = {};
    for (const post of posts) {
      manual[post.category] = (manual[post.category] ?? 0) + 1;
    }
    expect(categories).toEqual(manual);
  });

  it('sample content has expected category distribution', async () => {
    const categories = await getCategories();
    expect(Object.keys(categories)).toHaveLength(3);
    expect(categories['개발']).toBe(3);   // nextjs, typescript, mdx
    expect(categories['디자인']).toBe(1); // tailwind
    expect(categories['회고']).toBe(1);   // year-review
  });

  it('filtering posts by category returns only matching posts', async () => {
    const posts = await getAllPosts();

    const devPosts = posts.filter((p) => p.category === '개발');
    expect(devPosts).toHaveLength(3);
    expect(devPosts.every((p) => p.category === '개발')).toBe(true);

    const designPosts = posts.filter((p) => p.category === '디자인');
    expect(designPosts).toHaveLength(1);
    expect(designPosts[0].slug).toBe('tailwind-css-design-system');
  });
});

// ---------------------------------------------------------------------------
// Test 4 — Tag pipeline
// Flow: getAllPosts + getAllTags — verify cross-module consistency
// ---------------------------------------------------------------------------
describe('Integration: tag pipeline', () => {
  it('getAllTags() counts match manual counting from getAllPosts()', async () => {
    const [posts, tags] = await Promise.all([getAllPosts(), getAllTags()]);

    const manual: Record<string, number> = {};
    for (const post of posts) {
      for (const tag of post.tags ?? []) {
        manual[tag] = (manual[tag] ?? 0) + 1;
      }
    }
    expect(tags).toEqual(manual);
  });

  it('filterPosts finds posts by tag using real PostMeta from getAllPosts()', async () => {
    const posts = await getAllPosts();

    // 'TypeScript' tag appears in nextjs-app-router-guide and typescript-strict-mode
    // 'typescript' also matches typescript-strict-mode title
    const tsPosts = filterPosts(posts, 'TypeScript');
    expect(tsPosts.length).toBeGreaterThanOrEqual(2);
    for (const p of tsPosts) {
      const haystack = [p.title, p.category, ...p.tags].join(' ').toLowerCase();
      expect(haystack).toContain('typescript');
    }

    // 'Next.js' matches nextjs-app-router-guide (title) and mdx-blog-architecture (tag)
    const nextPosts = filterPosts(posts, 'Next.js');
    expect(nextPosts.length).toBeGreaterThanOrEqual(2);
    for (const p of nextPosts) {
      const haystack = [p.title, p.category, ...p.tags].join(' ').toLowerCase();
      expect(haystack).toContain('next.js');
    }
  });
});

// ---------------------------------------------------------------------------
// Test 5 — Search filtering pipeline with real data
// Flow: getAllPosts → filterPosts — comprehensive search scenarios
// ---------------------------------------------------------------------------
describe('Integration: search filtering pipeline', () => {
  it('filterPosts covers all search scenarios with real post data', async () => {
    const posts = await getAllPosts();

    // Empty query returns all posts unchanged
    expect(filterPosts(posts, '')).toHaveLength(5);
    expect(filterPosts(posts, '   ')).toHaveLength(5); // whitespace-only

    // Category text match — '디자인' is the category of tailwind-css-design-system
    // and its title also contains '디자인'
    const designResults = filterPosts(posts, '디자인');
    expect(designResults).toHaveLength(1);
    expect(designResults[0].slug).toBe('tailwind-css-design-system');

    // Tag match — 'MDX' tag appears in mdx-blog-architecture only
    const mdxResults = filterPosts(posts, 'MDX');
    expect(mdxResults.length).toBeGreaterThanOrEqual(1);
    expect(mdxResults.some((p) => p.slug === 'mdx-blog-architecture')).toBe(true);

    // No match returns empty array
    const noResults = filterPosts(posts, 'zzznonexistent999xyz');
    expect(noResults).toHaveLength(0);

    // Case-insensitive — 'typescript' lower-case should match TypeScript tag/title
    const lower = filterPosts(posts, 'typescript');
    const upper = filterPosts(posts, 'TypeScript');
    expect(lower.map((p) => p.slug).sort()).toEqual(upper.map((p) => p.slug).sort());
  });
});
