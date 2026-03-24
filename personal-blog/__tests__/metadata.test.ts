import type { Post, PostMeta } from '@/lib/types';

// ── Mocks ────────────────────────────────────────────────────────────────────

jest.mock('next-mdx-remote/rsc', () => ({ MDXRemote: () => null }));
jest.mock('@/lib/shiki', () => ({ rehypeShiki: jest.fn() }));
jest.mock('next/navigation', () => ({
  notFound: jest.fn(() => { throw new Error('NOT_FOUND'); }),
}));

jest.mock('@/lib/posts', () => ({
  getAllPosts: jest.fn(),
  getPostBySlug: jest.fn(),
  getCategories: jest.fn(),
  getAllTags: jest.fn(),
}));

import { getAllPosts, getPostBySlug } from '@/lib/posts';

// ── Helpers ───────────────────────────────────────────────────────────────────

function makePost(overrides: Partial<Post> = {}): Post {
  return {
    title: '테스트 게시물 제목',
    date: '2026-02-15',
    category: '개발',
    tags: ['TypeScript', 'Next.js'],
    slug: 'test-post',
    content: '## 섹션 1\n\n이것은 테스트 내용입니다. TypeScript와 Next.js에 대해 이야기합니다.',
    original_url: undefined,
    ...overrides,
  };
}

// ── Layout metadata ───────────────────────────────────────────────────────────

describe('layout metadata', () => {
  it('metadataBase is a URL instance (fallback when NEXT_PUBLIC_SITE_URL not set)', async () => {
    const { metadata } = await import('@/app/layout');
    expect(metadata.metadataBase).toBeInstanceOf(URL);
  });

  it('metadataBase defaults to localhost when NEXT_PUBLIC_SITE_URL is absent', async () => {
    const { metadata } = await import('@/app/layout');
    expect(metadata.metadataBase?.href).toContain('localhost');
  });
});

// ── Static page metadata ──────────────────────────────────────────────────────

describe('home page metadata', () => {
  it('has OG type website', async () => {
    const { metadata } = await import('@/app/page');
    expect(metadata.openGraph?.type).toBe('website');
  });

  it('has description set', async () => {
    const { metadata } = await import('@/app/page');
    expect(typeof metadata.description).toBe('string');
    expect((metadata.description as string).length).toBeGreaterThan(0);
  });
});

describe('blog list page metadata', () => {
  it('title contains "블로그"', async () => {
    const { metadata } = await import('@/app/blog/page');
    expect(metadata.title).toContain('블로그');
  });

  it('has OG type website', async () => {
    const { metadata } = await import('@/app/blog/page');
    expect(metadata.openGraph?.type).toBe('website');
  });
});

describe('tags page metadata', () => {
  it('title is "태그"', async () => {
    const { metadata } = await import('@/app/tags/page');
    expect(metadata.title).toBe('태그');
  });
});

describe('about page metadata', () => {
  it('title is "소개"', async () => {
    const { metadata } = await import('@/app/about/page');
    expect(metadata.title).toBe('소개');
  });
});

// ── Post generateMetadata ─────────────────────────────────────────────────────

describe('post generateMetadata', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (getAllPosts as jest.Mock).mockResolvedValue([]);
    (getPostBySlug as jest.Mock).mockResolvedValue(makePost());
  });

  it('returns post title', async () => {
    const { generateMetadata } = await import('@/app/blog/[slug]/page');
    const result = await generateMetadata({ params: Promise.resolve({ slug: 'test-post' }) });
    expect(result.title).toBe('테스트 게시물 제목');
  });

  it('returns excerpt as description', async () => {
    const { generateMetadata } = await import('@/app/blog/[slug]/page');
    const result = await generateMetadata({ params: Promise.resolve({ slug: 'test-post' }) });
    expect(typeof result.description).toBe('string');
    expect((result.description as string).length).toBeGreaterThan(0);
  });

  it('has OG type article', async () => {
    const { generateMetadata } = await import('@/app/blog/[slug]/page');
    const result = await generateMetadata({ params: Promise.resolve({ slug: 'test-post' }) });
    expect(result.openGraph?.type).toBe('article');
  });

  it('OG url contains the slug', async () => {
    const { generateMetadata } = await import('@/app/blog/[slug]/page');
    const result = await generateMetadata({ params: Promise.resolve({ slug: 'test-post' }) });
    // openGraph url is a string or URL
    const url = result.openGraph?.url?.toString() ?? '';
    expect(url).toContain('test-post');
  });

  it('returns fallback title for unknown slug', async () => {
    (getPostBySlug as jest.Mock).mockResolvedValue(null);
    const { generateMetadata } = await import('@/app/blog/[slug]/page');
    const result = await generateMetadata({ params: Promise.resolve({ slug: 'no-such' }) });
    expect(result.title).toBeTruthy();
  });
});

// ── Category generateMetadata ─────────────────────────────────────────────────

describe('category generateMetadata', () => {
  const POSTS: PostMeta[] = [
    { title: '포스트 1', date: '2026-01-01', category: '개발', tags: [], slug: 'p1' },
    { title: '포스트 2', date: '2026-02-01', category: '개발', tags: [], slug: 'p2' },
    { title: '포스트 3', date: '2026-03-01', category: '디자인', tags: [], slug: 'p3' },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    (getAllPosts as jest.Mock).mockResolvedValue(POSTS);
  });

  it('title contains category name', async () => {
    const { generateMetadata } = await import('@/app/category/[name]/page');
    const result = await generateMetadata({ params: Promise.resolve({ name: encodeURIComponent('개발') }) });
    expect(result.title?.toString()).toContain('개발');
  });

  it('description mentions post count', async () => {
    const { generateMetadata } = await import('@/app/category/[name]/page');
    const result = await generateMetadata({ params: Promise.resolve({ name: encodeURIComponent('개발') }) });
    expect(result.description).toContain('2');
  });

  it('has OG type website', async () => {
    const { generateMetadata } = await import('@/app/category/[name]/page');
    const result = await generateMetadata({ params: Promise.resolve({ name: encodeURIComponent('개발') }) });
    expect(result.openGraph?.type).toBe('website');
  });
});
