/**
 * @jest-environment node
 */
import type { PostMeta } from '@/lib/types';

// ── Mocks ─────────────────────────────────────────────────────────────────────

jest.mock('@/lib/posts', () => ({
  getAllPosts: jest.fn(),
}));

import { getAllPosts } from '@/lib/posts';
import sitemap from '@/app/sitemap';
import { GET } from '@/app/feed.xml/route';

// ── Fixtures ──────────────────────────────────────────────────────────────────

function makePosts(): PostMeta[] {
  return [
    { title: 'Next.js 가이드', date: '2026-02-20', category: '개발', tags: ['Next.js'], slug: 'nextjs-guide' },
    { title: 'TypeScript 입문', date: '2026-01-15', category: '개발', tags: ['TypeScript'], slug: 'typescript-intro' },
    { title: '2025 회고', date: '2025-12-15', category: '회고', tags: [], slug: '2025-review' },
  ];
}

beforeEach(() => {
  jest.clearAllMocks();
  (getAllPosts as jest.Mock).mockResolvedValue(makePosts());
});

// ── Sitemap tests ─────────────────────────────────────────────────────────────

describe('sitemap', () => {
  it('includes all 4 static pages', async () => {
    const entries = await sitemap();
    const urls = entries.map((e) => e.url);
    expect(urls.some((u) => u.endsWith('localhost:3000') || u === 'http://localhost:3000')).toBe(true);
    expect(urls.some((u) => u.endsWith('/blog'))).toBe(true);
    expect(urls.some((u) => u.endsWith('/tags'))).toBe(true);
    expect(urls.some((u) => u.endsWith('/about'))).toBe(true);
  });

  it('includes an entry for each post slug', async () => {
    const entries = await sitemap();
    const urls = entries.map((e) => e.url);
    expect(urls.some((u) => u.includes('/blog/nextjs-guide'))).toBe(true);
    expect(urls.some((u) => u.includes('/blog/typescript-intro'))).toBe(true);
    expect(urls.some((u) => u.includes('/blog/2025-review'))).toBe(true);
  });

  it('post entries have lastModified matching post date', async () => {
    const entries = await sitemap();
    const post = entries.find((e) => e.url.includes('nextjs-guide'));
    expect(post?.lastModified).toEqual(new Date('2026-02-20'));
  });

  it('total entries = 4 static + number of posts', async () => {
    const entries = await sitemap();
    expect(entries.length).toBe(4 + 3);
  });

  it('handles empty posts list (only static pages)', async () => {
    (getAllPosts as jest.Mock).mockResolvedValue([]);
    const entries = await sitemap();
    expect(entries.length).toBe(4);
  });

  it('home page entry has priority 1', async () => {
    const entries = await sitemap();
    const home = entries.find((e) => !e.url.includes('/blog') && !e.url.includes('/tags') && !e.url.includes('/about') && !e.url.includes('/category'));
    expect(home?.priority).toBe(1);
  });
});

// ── RSS feed tests ────────────────────────────────────────────────────────────

describe('GET /feed.xml', () => {
  it('returns 200 status', async () => {
    const response = await GET();
    expect(response.status).toBe(200);
  });

  it('Content-Type is application/rss+xml', async () => {
    const response = await GET();
    expect(response.headers.get('Content-Type')).toContain('application/rss+xml');
  });

  it('body contains RSS 2.0 root element', async () => {
    const response = await GET();
    const body = await response.text();
    expect(body).toContain('<rss');
    expect(body).toContain('version="2.0"');
  });

  it('body contains <channel> element', async () => {
    const response = await GET();
    const body = await response.text();
    expect(body).toContain('<channel>');
  });

  it('body contains all post titles', async () => {
    const response = await GET();
    const body = await response.text();
    expect(body).toContain('Next.js 가이드');
    expect(body).toContain('TypeScript 입문');
    expect(body).toContain('2025 회고');
  });

  it('body contains <item> elements for all posts', async () => {
    const response = await GET();
    const body = await response.text();
    const itemCount = (body.match(/<item>/g) ?? []).length;
    expect(itemCount).toBe(3);
  });

  it('post items include correct blog links', async () => {
    const response = await GET();
    const body = await response.text();
    expect(body).toContain('/blog/nextjs-guide');
    expect(body).toContain('/blog/typescript-intro');
  });

  it('handles empty posts list (no <item> elements)', async () => {
    (getAllPosts as jest.Mock).mockResolvedValue([]);
    const response = await GET();
    const body = await response.text();
    expect(body).not.toContain('<item>');
    expect(response.status).toBe(200);
  });
});
