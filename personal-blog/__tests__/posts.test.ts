import fs from 'fs';
import os from 'os';
import path from 'path';
import {
  getAllPosts,
  getPostBySlug,
  getPostSlugs,
  getCategories,
  getAllTags,
} from '../lib/posts';

const REAL_POSTS_DIR = path.join(process.cwd(), 'content/posts');

// ─── getAllPosts ───────────────────────────────────────────────────────────────

describe('getAllPosts', () => {
  it('returns all 5 sample posts', async () => {
    const posts = await getAllPosts();
    expect(posts).toHaveLength(5);
  });

  it('returns posts sorted by date descending (newest first)', async () => {
    const posts = await getAllPosts();
    for (let i = 0; i < posts.length - 1; i++) {
      const a = new Date(posts[i].date).getTime();
      const b = new Date(posts[i + 1].date).getTime();
      expect(a).toBeGreaterThanOrEqual(b);
    }
  });

  it('every post has required fields: title, date, category, tags, slug', async () => {
    const posts = await getAllPosts();
    for (const post of posts) {
      expect(typeof post.title).toBe('string');
      expect(post.title.length).toBeGreaterThan(0);
      expect(typeof post.date).toBe('string');
      expect(typeof post.category).toBe('string');
      expect(Array.isArray(post.tags)).toBe(true);
      expect(typeof post.slug).toBe('string');
      expect(post.slug.length).toBeGreaterThan(0);
    }
  });

  it('posts do NOT include content field (metadata only)', async () => {
    const posts = await getAllPosts();
    for (const post of posts) {
      expect((post as { content?: string }).content).toBeUndefined();
    }
  });

  it('returns empty array for empty directory', async () => {
    const tmpDir = await fs.promises.mkdtemp(path.join(os.tmpdir(), 'posts-'));
    try {
      const posts = await getAllPosts(tmpDir);
      expect(posts).toHaveLength(0);
    } finally {
      await fs.promises.rmdir(tmpDir);
    }
  });

  it('ignores non-.md files in directory', async () => {
    const tmpDir = await fs.promises.mkdtemp(path.join(os.tmpdir(), 'posts-'));
    try {
      await fs.promises.writeFile(path.join(tmpDir, 'note.txt'), 'ignored');
      await fs.promises.writeFile(path.join(tmpDir, 'draft.md'), `---\ntitle: Draft\ndate: "2026-01-01"\ncategory: test\ntags: []\nslug: draft\n---\nContent`);
      const posts = await getAllPosts(tmpDir);
      expect(posts).toHaveLength(1);
      expect(posts[0].slug).toBe('draft');
    } finally {
      await fs.promises.rm(tmpDir, { recursive: true });
    }
  });
});

// ─── getPostBySlug ─────────────────────────────────────────────────────────────

describe('getPostBySlug', () => {
  it('returns the correct post for a valid slug', async () => {
    const post = await getPostBySlug('nextjs-app-router-guide');
    expect(post).not.toBeNull();
    expect(post!.slug).toBe('nextjs-app-router-guide');
    expect(post!.title).toBe('Next.js 15 App Router 완전 가이드');
    expect(post!.category).toBe('개발');
  });

  it('returns post with content field populated', async () => {
    const post = await getPostBySlug('nextjs-app-router-guide');
    expect(post).not.toBeNull();
    expect(typeof post!.content).toBe('string');
    expect(post!.content.length).toBeGreaterThan(0);
  });

  it('returns all frontmatter fields in the post', async () => {
    const post = await getPostBySlug('nextjs-app-router-guide');
    expect(post).not.toBeNull();
    expect(post!.date).toBe('2026-01-10');
    expect(Array.isArray(post!.tags)).toBe(true);
    expect(post!.tags).toContain('Next.js');
    expect(post!.original_url).toBe('https://example.tistory.com/nextjs-app-router');
  });

  it('returns null for a slug that does not exist', async () => {
    const post = await getPostBySlug('this-slug-does-not-exist');
    expect(post).toBeNull();
  });

  it('returns null for empty string slug', async () => {
    const post = await getPostBySlug('');
    expect(post).toBeNull();
  });

  it('returns post without original_url for posts that omit it', async () => {
    const post = await getPostBySlug('2025-year-review');
    expect(post).not.toBeNull();
    expect(post!.original_url).toBeUndefined();
  });
});

// ─── getPostSlugs ─────────────────────────────────────────────────────────────

describe('getPostSlugs', () => {
  it('returns an array of all 5 slugs', async () => {
    const slugs = await getPostSlugs();
    expect(slugs).toHaveLength(5);
  });

  it('each slug is a non-empty string', async () => {
    const slugs = await getPostSlugs();
    for (const slug of slugs) {
      expect(typeof slug).toBe('string');
      expect(slug.length).toBeGreaterThan(0);
    }
  });

  it('slugs are in date-descending order (matches getAllPosts order)', async () => {
    const slugs = await getPostSlugs();
    const posts = await getAllPosts();
    expect(slugs).toEqual(posts.map((p) => p.slug));
  });

  it('includes known slugs from sample posts', async () => {
    const slugs = await getPostSlugs();
    expect(slugs).toContain('nextjs-app-router-guide');
    expect(slugs).toContain('2025-year-review');
  });
});

// ─── getCategories ─────────────────────────────────────────────────────────────

describe('getCategories', () => {
  it('returns an object with category names as keys', async () => {
    const categories = await getCategories();
    expect(typeof categories).toBe('object');
    expect(Object.keys(categories).length).toBeGreaterThan(0);
  });

  it('includes the three expected categories', async () => {
    const categories = await getCategories();
    expect(categories).toHaveProperty('개발');
    expect(categories).toHaveProperty('디자인');
    expect(categories).toHaveProperty('회고');
  });

  it('counts sum to total number of posts', async () => {
    const categories = await getCategories();
    const total = Object.values(categories).reduce((sum, n) => sum + n, 0);
    expect(total).toBe(5);
  });

  it('개발 category has 3 posts', async () => {
    const categories = await getCategories();
    expect(categories['개발']).toBe(3);
  });

  it('returns empty object for empty directory', async () => {
    const tmpDir = await fs.promises.mkdtemp(path.join(os.tmpdir(), 'posts-'));
    try {
      const categories = await getCategories(tmpDir);
      expect(categories).toEqual({});
    } finally {
      await fs.promises.rmdir(tmpDir);
    }
  });
});

// ─── getAllTags ────────────────────────────────────────────────────────────────

describe('getAllTags', () => {
  it('returns an object with tag names as keys', async () => {
    const tags = await getAllTags();
    expect(typeof tags).toBe('object');
    expect(Object.keys(tags).length).toBeGreaterThan(0);
  });

  it('includes tags from the sample posts', async () => {
    const tags = await getAllTags();
    expect(Object.keys(tags)).toContain('Next.js');
    expect(Object.keys(tags)).toContain('TypeScript');
  });

  it('count values are positive integers', async () => {
    const tags = await getAllTags();
    for (const count of Object.values(tags)) {
      expect(count).toBeGreaterThan(0);
      expect(Number.isInteger(count)).toBe(true);
    }
  });

  it('total tag occurrences matches sum of all posts tags lengths', async () => {
    const tags = await getAllTags();
    const posts = await getAllPosts();
    const expectedTotal = posts.reduce((sum, p) => sum + (p.tags?.length ?? 0), 0);
    const actualTotal = Object.values(tags).reduce((sum, n) => sum + n, 0);
    expect(actualTotal).toBe(expectedTotal);
  });

  it('returns empty object for empty directory', async () => {
    const tmpDir = await fs.promises.mkdtemp(path.join(os.tmpdir(), 'posts-'));
    try {
      const tags = await getAllTags(tmpDir);
      expect(tags).toEqual({});
    } finally {
      await fs.promises.rmdir(tmpDir);
    }
  });
});
