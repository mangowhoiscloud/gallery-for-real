import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import type { Post } from '@/lib/types';

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

jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  useSearchParams: jest.fn(),
}));

jest.mock('@/lib/posts', () => ({
  getAllPosts: jest.fn(),
  getPostBySlug: jest.fn(),
  getCategories: jest.fn(),
  getAllTags: jest.fn(),
}));

import { useRouter, useSearchParams } from 'next/navigation';
import { getAllPosts, getPostBySlug, getCategories, getAllTags } from '@/lib/posts';
import BlogListClient from '@/components/BlogListClient';
import BlogPage from '@/app/blog/page';

const mockRouterReplace = jest.fn();

function setupNavigation(params: Record<string, string> = {}) {
  const sp = new URLSearchParams(params);
  (useSearchParams as jest.Mock).mockReturnValue({
    get: (key: string) => sp.get(key),
    toString: () => sp.toString(),
  });
  (useRouter as jest.Mock).mockReturnValue({ replace: mockRouterReplace });
}

function makePost(n: number): Post {
  const category =
    n <= 4 ? '개발' : n <= 8 ? '디자인' : '회고';
  const tags =
    n % 3 === 0
      ? ['React', 'TypeScript']
      : n % 3 === 1
      ? ['Next.js']
      : ['CSS'];
  return {
    title: `포스트 제목 ${n}`,
    date: `2026-01-${String(n).padStart(2, '0')}`,
    category,
    tags,
    slug: `post-slug-${n}`,
    original_url: undefined,
    content: `## 섹션 제목\n\n이것은 ${n}번 포스트의 내용입니다. `.repeat(5),
  };
}

// 12 posts: posts 1-4 → 개발, 5-8 → 디자인, 9-12 → 회고
// tags: posts %3===0 (3,6,9,12) → [React,TypeScript]
//       posts %3===1 (1,4,7,10) → [Next.js]
//       posts %3===2 (2,5,8,11) → [CSS]
const MOCK_POSTS: Post[] = Array.from({ length: 12 }, (_, i) => makePost(i + 1));
const CATEGORIES = ['개발', '디자인', '회고'];
const ALL_TAGS = ['Next.js', 'CSS', 'React', 'TypeScript'];

beforeEach(() => {
  jest.clearAllMocks();
  setupNavigation();
});

describe('BlogListClient', () => {
  describe('rendering without filters', () => {
    it('shows total post count', () => {
      render(
        <BlogListClient posts={MOCK_POSTS} categories={CATEGORIES} allTags={ALL_TAGS} />
      );
      expect(screen.getByTestId('filtered-count')).toHaveTextContent('12개 게시물');
    });

    it('renders first 10 posts on page 1 (pagination)', () => {
      render(
        <BlogListClient posts={MOCK_POSTS} categories={CATEGORIES} allTags={ALL_TAGS} />
      );
      expect(screen.getAllByRole('article')).toHaveLength(10);
    });

    it('page 2 shows remaining 2 posts', () => {
      setupNavigation({ page: '2' });
      render(
        <BlogListClient posts={MOCK_POSTS} categories={CATEGORIES} allTags={ALL_TAGS} />
      );
      expect(screen.getAllByRole('article')).toHaveLength(2);
    });

    it('renders category select with all category options', () => {
      render(
        <BlogListClient posts={MOCK_POSTS} categories={CATEGORIES} allTags={ALL_TAGS} />
      );
      const select = screen.getByRole('combobox', { name: '카테고리 필터' });
      expect(select).toBeInTheDocument();
      for (const cat of CATEGORIES) {
        expect(screen.getByRole('option', { name: cat })).toBeInTheDocument();
      }
    });

    it('renders tag select with all tag options', () => {
      render(
        <BlogListClient posts={MOCK_POSTS} categories={CATEGORIES} allTags={ALL_TAGS} />
      );
      const select = screen.getByRole('combobox', { name: '태그 필터' });
      expect(select).toBeInTheDocument();
      for (const tag of ALL_TAGS) {
        expect(screen.getByRole('option', { name: tag })).toBeInTheDocument();
      }
    });

    it('renders pagination component', () => {
      render(
        <BlogListClient posts={MOCK_POSTS} categories={CATEGORIES} allTags={ALL_TAGS} />
      );
      expect(screen.getByRole('navigation', { name: 'Pagination' })).toBeInTheDocument();
    });
  });

  describe('category filtering', () => {
    it('filters to 4 개발 posts when category=개발', () => {
      setupNavigation({ category: '개발' });
      render(
        <BlogListClient posts={MOCK_POSTS} categories={CATEGORIES} allTags={ALL_TAGS} />
      );
      expect(screen.getByTestId('filtered-count')).toHaveTextContent('4개 게시물');
      expect(screen.getAllByRole('article')).toHaveLength(4);
    });

    it('category select change calls router.replace with encoded category param', () => {
      render(
        <BlogListClient posts={MOCK_POSTS} categories={CATEGORIES} allTags={ALL_TAGS} />
      );
      fireEvent.change(screen.getByRole('combobox', { name: '카테고리 필터' }), {
        target: { value: '디자인' },
      });
      expect(mockRouterReplace).toHaveBeenCalledWith(
        expect.stringContaining('category=')
      );
      const callArg = mockRouterReplace.mock.calls[0][0] as string;
      // 디자인 URL-encoded: %EB%94%94%EC%9E%90%EC%9D%B8
      expect(callArg).toMatch(/category=/);
    });

    it('category change resets page param', () => {
      setupNavigation({ page: '2' });
      render(
        <BlogListClient posts={MOCK_POSTS} categories={CATEGORIES} allTags={ALL_TAGS} />
      );
      fireEvent.change(screen.getByRole('combobox', { name: '카테고리 필터' }), {
        target: { value: '개발' },
      });
      const callArg = mockRouterReplace.mock.calls[0][0] as string;
      expect(callArg).not.toMatch(/page=/);
    });

    it('selecting 모든 카테고리 shows all posts', () => {
      setupNavigation({ category: '개발' });
      render(
        <BlogListClient posts={MOCK_POSTS} categories={CATEGORIES} allTags={ALL_TAGS} />
      );
      fireEvent.change(screen.getByRole('combobox', { name: '카테고리 필터' }), {
        target: { value: '' },
      });
      // router.replace is called without category param
      const callArg = mockRouterReplace.mock.calls[0][0] as string;
      expect(callArg).not.toMatch(/category=/);
    });
  });

  describe('tag filtering', () => {
    it('filters to 4 React posts when tag=React', () => {
      // posts 3,6,9,12 have React tag
      setupNavigation({ tag: 'React' });
      render(
        <BlogListClient posts={MOCK_POSTS} categories={CATEGORIES} allTags={ALL_TAGS} />
      );
      expect(screen.getByTestId('filtered-count')).toHaveTextContent('4개 게시물');
    });

    it('tag select change calls router.replace with tag param', () => {
      render(
        <BlogListClient posts={MOCK_POSTS} categories={CATEGORIES} allTags={ALL_TAGS} />
      );
      fireEvent.change(screen.getByRole('combobox', { name: '태그 필터' }), {
        target: { value: 'Next.js' },
      });
      const callArg = mockRouterReplace.mock.calls[0][0] as string;
      expect(callArg).toMatch(/tag=Next\.js/);
    });

    it('tag change resets page param', () => {
      setupNavigation({ page: '2' });
      render(
        <BlogListClient posts={MOCK_POSTS} categories={CATEGORIES} allTags={ALL_TAGS} />
      );
      fireEvent.change(screen.getByRole('combobox', { name: '태그 필터' }), {
        target: { value: 'CSS' },
      });
      const callArg = mockRouterReplace.mock.calls[0][0] as string;
      expect(callArg).not.toMatch(/page=/);
    });
  });

  describe('combined filtering', () => {
    it('applies category AND tag filter: 개발 + React → 1 post', () => {
      // 개발: posts 1,2,3,4 | React: posts 3,6,9,12 | intersection: post 3
      setupNavigation({ category: '개발', tag: 'React' });
      render(
        <BlogListClient posts={MOCK_POSTS} categories={CATEGORIES} allTags={ALL_TAGS} />
      );
      expect(screen.getByTestId('filtered-count')).toHaveTextContent('1개 게시물');
    });

    it('applies q AND category filter', () => {
      // q="포스트 제목 3" matches post 3 only; post 3 is 개발 category
      setupNavigation({ q: '포스트 제목 3', category: '개발' });
      render(
        <BlogListClient posts={MOCK_POSTS} categories={CATEGORIES} allTags={ALL_TAGS} />
      );
      expect(screen.getByTestId('filtered-count')).toHaveTextContent('1개 게시물');
    });
  });

  describe('search query (q param)', () => {
    it('q param filters posts by title', () => {
      // "포스트 제목 3" matches only post 3 in our 12-post dataset
      setupNavigation({ q: '포스트 제목 3' });
      render(
        <BlogListClient posts={MOCK_POSTS} categories={CATEGORIES} allTags={ALL_TAGS} />
      );
      expect(screen.getByTestId('filtered-count')).toHaveTextContent('1개 게시물');
    });
  });

  describe('zero results', () => {
    it('shows empty message when no posts match', () => {
      setupNavigation({ q: '이런검색결과없음xyz' });
      render(
        <BlogListClient posts={MOCK_POSTS} categories={CATEGORIES} allTags={ALL_TAGS} />
      );
      expect(screen.getByTestId('filtered-count')).toHaveTextContent('0개 게시물');
      expect(screen.getByText('검색 결과가 없습니다.')).toBeInTheDocument();
    });
  });

  describe('pagination', () => {
    it('clicking page 2 calls router.replace with page=2', () => {
      render(
        <BlogListClient posts={MOCK_POSTS} categories={CATEGORIES} allTags={ALL_TAGS} />
      );
      fireEvent.click(screen.getByRole('button', { name: '2' }));
      expect(mockRouterReplace).toHaveBeenCalledWith('?page=2');
    });

    it('clicking page 1 when on page 2 removes page param', () => {
      setupNavigation({ page: '2' });
      render(
        <BlogListClient posts={MOCK_POSTS} categories={CATEGORIES} allTags={ALL_TAGS} />
      );
      fireEvent.click(screen.getByRole('button', { name: '1' }));
      const callArg = mockRouterReplace.mock.calls[0][0] as string;
      expect(callArg).not.toMatch(/page=/);
    });
  });
});

describe('Blog page (app/blog/page.tsx)', () => {
  beforeEach(() => {
    const postsMeta = MOCK_POSTS.map(({ content: _content, ...m }) => m);
    (getAllPosts as jest.Mock).mockResolvedValue(postsMeta);
    (getPostBySlug as jest.Mock).mockImplementation(async (slug: string) =>
      MOCK_POSTS.find((p) => p.slug === slug) ?? null
    );
    (getCategories as jest.Mock).mockResolvedValue(
      Object.fromEntries(CATEGORIES.map((c) => [c, 4]))
    );
    (getAllTags as jest.Mock).mockResolvedValue(
      Object.fromEntries(ALL_TAGS.map((t) => [t, 3]))
    );
  });

  it('renders the 블로그 heading', async () => {
    render(await BlogPage());
    expect(screen.getByRole('heading', { name: '블로그' })).toBeInTheDocument();
  });

  it('renders 10 post articles on page 1', async () => {
    render(await BlogPage());
    expect(screen.getAllByRole('article')).toHaveLength(10);
  });

  it('renders category and tag selects', async () => {
    render(await BlogPage());
    expect(screen.getByRole('combobox', { name: '카테고리 필터' })).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: '태그 필터' })).toBeInTheDocument();
  });
});
