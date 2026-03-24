import React from 'react';
import { render, screen } from '@testing-library/react';
import type { Post, PostMeta } from '@/lib/types';

// ── Mocks ────────────────────────────────────────────────────────────────────

jest.mock('next/navigation', () => ({
  notFound: jest.fn(() => {
    throw new Error('NOT_FOUND');
  }),
}));

jest.mock('next-mdx-remote/rsc', () => ({
  MDXRemote: ({ source }: { source: string }) => (
    <div data-testid="mdx-content">{source}</div>
  ),
}));

jest.mock('@/lib/shiki', () => ({
  rehypeShiki: jest.fn(),
}));

jest.mock('next/link', () => {
  return function MockLink({
    href,
    children,
    ...rest
  }: {
    href: string;
    children: React.ReactNode;
    [key: string]: unknown;
  }) {
    return (
      <a href={href} {...rest}>
        {children}
      </a>
    );
  };
});

jest.mock('@/lib/posts', () => ({
  getAllPosts: jest.fn(),
  getPostBySlug: jest.fn(),
}));

import { notFound } from 'next/navigation';
import { getAllPosts, getPostBySlug } from '@/lib/posts';
import PostPage, { generateStaticParams } from '@/app/blog/[slug]/page';

// ── Helpers ───────────────────────────────────────────────────────────────────

function makePost(n: number, overrides: Partial<Post> = {}): Post {
  return {
    title: `포스트 제목 ${n}`,
    date: `2026-0${n}-10`,
    category: '개발',
    tags: [`태그${n}`, 'TypeScript'],
    slug: `post-slug-${n}`,
    content: `## 섹션 ${n}\n\n포스트 ${n}의 내용입니다. TypeScript는 정적 타입 언어입니다.`.repeat(5),
    original_url: undefined,
    ...overrides,
  };
}

function makeMeta(n: number): PostMeta {
  const { content: _c, ...meta } = makePost(n);
  return meta;
}

// 3 posts, sorted newest first: post3, post2, post1
const ALL_META: PostMeta[] = [3, 2, 1].map(makeMeta);
const ALL_POSTS: Post[] = [3, 2, 1].map((n) => makePost(n));

function setupMocks(currentSlug: string, overridePost?: Post | null) {
  (getAllPosts as jest.Mock).mockResolvedValue(ALL_META);
  (getPostBySlug as jest.Mock).mockImplementation(async (slug: string) => {
    if (slug === currentSlug && overridePost !== undefined) return overridePost;
    return ALL_POSTS.find((p) => p.slug === slug) ?? null;
  });
}

async function renderPost(slug: string) {
  return render(await PostPage({ params: Promise.resolve({ slug }) }));
}

// ── Setup ─────────────────────────────────────────────────────────────────────

beforeEach(() => {
  jest.clearAllMocks();
  global.IntersectionObserver = jest.fn(() => ({
    observe: jest.fn(),
    disconnect: jest.fn(),
    unobserve: jest.fn(),
    root: null,
    rootMargin: '',
    thresholds: [],
    takeRecords: () => [],
  })) as unknown as typeof IntersectionObserver;

  // Default: render post-slug-2 (middle post)
  setupMocks('post-slug-2');
});

// ── generateStaticParams ──────────────────────────────────────────────────────

describe('generateStaticParams', () => {
  it('returns a slug entry for every post', async () => {
    (getAllPosts as jest.Mock).mockResolvedValue(ALL_META);
    const params = await generateStaticParams();
    expect(params).toEqual([
      { slug: 'post-slug-3' },
      { slug: 'post-slug-2' },
      { slug: 'post-slug-1' },
    ]);
  });
});

// ── PostPage ──────────────────────────────────────────────────────────────────

describe('PostPage — header', () => {
  it('renders post title as h1', async () => {
    await renderPost('post-slug-2');
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('포스트 제목 2');
  });

  it('renders date in Korean format', async () => {
    // post-slug-2 date: 2026-02-10 → 2026년 2월 10일
    await renderPost('post-slug-2');
    expect(screen.getByText('2026년 2월 10일')).toBeInTheDocument();
  });

  it('renders category as a link to /category/[encoded-name]', async () => {
    await renderPost('post-slug-2');
    const catLink = screen.getByRole('link', { name: '개발' });
    expect(catLink).toHaveAttribute('href', `/category/${encodeURIComponent('개발')}`);
  });

  it('renders reading time (N분 소요)', async () => {
    await renderPost('post-slug-2');
    expect(screen.getByText(/분 소요/)).toBeInTheDocument();
  });

  it('renders post tags', async () => {
    await renderPost('post-slug-2');
    expect(screen.getByText('태그2')).toBeInTheDocument();
    expect(screen.getByText('TypeScript')).toBeInTheDocument();
  });

  it('renders original_url link when present', async () => {
    setupMocks('post-slug-2', makePost(2, { original_url: 'https://example.tistory.com/42' }));
    await renderPost('post-slug-2');
    const link = screen.getByRole('link', { name: '원문 Tistory에서 보기' });
    expect(link).toHaveAttribute('href', 'https://example.tistory.com/42');
  });

  it('does not render original_url link when absent', async () => {
    await renderPost('post-slug-2');
    expect(screen.queryByText('원문 Tistory에서 보기')).not.toBeInTheDocument();
  });
});

describe('PostPage — content', () => {
  it('renders MDX content area', async () => {
    await renderPost('post-slug-2');
    expect(screen.getByTestId('mdx-content')).toBeInTheDocument();
  });

  it('renders TableOfContents for post headings', async () => {
    await renderPost('post-slug-2');
    expect(
      screen.getByRole('navigation', { name: 'Table of contents' }),
    ).toBeInTheDocument();
  });
});

describe('PostPage — prev/next navigation', () => {
  it('renders prev post link (older) for middle post', async () => {
    // post-slug-2 is index 1; prevPost = index 2 = post-slug-1 (older)
    await renderPost('post-slug-2');
    const prevLink = screen.getByRole('link', { name: /이전 글/ });
    expect(prevLink).toHaveAttribute('href', '/blog/post-slug-1');
  });

  it('renders next post link (newer) for middle post', async () => {
    // nextPost = index 0 = post-slug-3 (newer)
    await renderPost('post-slug-2');
    const nextLink = screen.getByRole('link', { name: /다음 글/ });
    expect(nextLink).toHaveAttribute('href', '/blog/post-slug-3');
  });

  it('hides prev link for oldest post (index 2 = post-slug-1)', async () => {
    setupMocks('post-slug-1');
    await renderPost('post-slug-1');
    expect(screen.queryByRole('link', { name: /이전 글/ })).not.toBeInTheDocument();
  });

  it('hides next link for newest post (index 0 = post-slug-3)', async () => {
    setupMocks('post-slug-3');
    await renderPost('post-slug-3');
    expect(screen.queryByRole('link', { name: /다음 글/ })).not.toBeInTheDocument();
  });
});

describe('PostPage — error handling', () => {
  it('calls notFound() for unrecognised slug', async () => {
    (getPostBySlug as jest.Mock).mockResolvedValue(null);
    await expect(
      PostPage({ params: Promise.resolve({ slug: 'no-such-slug' }) }),
    ).rejects.toThrow();
    expect(notFound as jest.Mock).toHaveBeenCalled();
  });
});
