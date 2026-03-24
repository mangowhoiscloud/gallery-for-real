import React from 'react';
import { render, screen } from '@testing-library/react';
import type { Post, PostMeta } from '@/lib/types';

// ── Mocks ────────────────────────────────────────────────────────────────────

jest.mock('next/navigation', () => ({
  notFound: jest.fn(() => {
    throw new Error('NOT_FOUND');
  }),
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
  getCategories: jest.fn(),
}));

import { notFound } from 'next/navigation';
import { getAllPosts, getPostBySlug, getCategories } from '@/lib/posts';
import CategoryPage, { generateStaticParams } from '@/app/category/[name]/page';

// ── Helpers ───────────────────────────────────────────────────────────────────

function makePost(n: number, category: string): Post {
  return {
    title: `포스트 제목 ${n}`,
    date: `2026-0${n}-10`,
    category,
    tags: [`태그${n}`],
    slug: `post-slug-${n}`,
    content: `## 섹션 ${n}\n\n포스트 ${n}의 내용입니다. `.repeat(10),
    original_url: undefined,
  };
}

function makeMeta(post: Post): PostMeta {
  const { content: _c, ...meta } = post;
  return meta;
}

const POST_개발_1 = makePost(1, '개발');
const POST_개발_2 = makePost(2, '개발');
const POST_디자인_3 = makePost(3, '디자인');

const ALL_META: PostMeta[] = [POST_개발_2, POST_개발_1, POST_디자인_3].map(makeMeta);
const ALL_POSTS = [POST_개발_2, POST_개발_1, POST_디자인_3];

const CATEGORIES: Record<string, number> = { '개발': 2, '디자인': 1 };

function setupMocks() {
  (getAllPosts as jest.Mock).mockResolvedValue(ALL_META);
  (getPostBySlug as jest.Mock).mockImplementation(async (slug: string) =>
    ALL_POSTS.find((p) => p.slug === slug) ?? null,
  );
  (getCategories as jest.Mock).mockResolvedValue(CATEGORIES);
}

async function renderCategory(name: string) {
  return render(await CategoryPage({ params: Promise.resolve({ name }) }));
}

// ── Setup ─────────────────────────────────────────────────────────────────────

beforeEach(() => {
  jest.clearAllMocks();
  setupMocks();
});

// ── generateStaticParams ──────────────────────────────────────────────────────

describe('generateStaticParams', () => {
  it('returns one entry per category', async () => {
    const params = await generateStaticParams();
    expect(params).toHaveLength(2);
  });

  it('includes encoded category names', async () => {
    const params = await generateStaticParams();
    const names = params.map((p) => p.name);
    expect(names).toContain(encodeURIComponent('개발'));
    expect(names).toContain(encodeURIComponent('디자인'));
  });
});

// ── CategoryPage ──────────────────────────────────────────────────────────────

describe('CategoryPage — heading and count', () => {
  it('renders category name as h1', async () => {
    await renderCategory(encodeURIComponent('개발'));
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('개발');
  });

  it('renders correct post count for category', async () => {
    await renderCategory(encodeURIComponent('개발'));
    expect(screen.getByText('2개의 게시물')).toBeInTheDocument();
  });

  it('renders correct count for single-post category', async () => {
    await renderCategory(encodeURIComponent('디자인'));
    expect(screen.getByText('1개의 게시물')).toBeInTheDocument();
  });
});

describe('CategoryPage — post filtering', () => {
  it('renders only posts in the requested category', async () => {
    await renderCategory(encodeURIComponent('개발'));
    // 개발 has 2 posts (1 and 2)
    expect(screen.getByText('포스트 제목 1')).toBeInTheDocument();
    expect(screen.getByText('포스트 제목 2')).toBeInTheDocument();
    // 디자인 post should NOT appear
    expect(screen.queryByText('포스트 제목 3')).not.toBeInTheDocument();
  });

  it('renders only 디자인 posts on that category page', async () => {
    await renderCategory(encodeURIComponent('디자인'));
    expect(screen.getByText('포스트 제목 3')).toBeInTheDocument();
    expect(screen.queryByText('포스트 제목 1')).not.toBeInTheDocument();
    expect(screen.queryByText('포스트 제목 2')).not.toBeInTheDocument();
  });

  it('renders articles for each matching post', async () => {
    await renderCategory(encodeURIComponent('개발'));
    const articles = screen.getAllByRole('article');
    expect(articles).toHaveLength(2);
  });
});

describe('CategoryPage — error handling', () => {
  it('calls notFound() for a category with no posts', async () => {
    await expect(
      CategoryPage({ params: Promise.resolve({ name: encodeURIComponent('없는카테고리') }) }),
    ).rejects.toThrow();
    expect(notFound as jest.Mock).toHaveBeenCalled();
  });
});
