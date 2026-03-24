import React from 'react';
import { render, screen } from '@testing-library/react';
import type { Post, PostMeta } from '@/lib/types';

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

import { getAllPosts, getPostBySlug, getCategories } from '@/lib/posts';
import Home from '@/app/page';

const mockGetAllPosts = getAllPosts as jest.Mock;
const mockGetPostBySlug = getPostBySlug as jest.Mock;
const mockGetCategories = getCategories as jest.Mock;

function makePostMeta(n: number): PostMeta {
  return {
    title: `포스트 제목 ${n}`,
    date: `2026-0${n}-10`,
    category: n % 2 === 0 ? '디자인' : '개발',
    tags: [`태그${n}`],
    slug: `post-slug-${n}`,
    original_url: undefined,
  };
}

function makePost(n: number): Post {
  return {
    ...makePostMeta(n),
    content: `## 섹션 ${n}\n\n포스트 ${n}의 내용입니다. `.repeat(10),
  };
}

// 6 posts to verify only 5 are shown
const ALL_POST_META: PostMeta[] = [6, 5, 4, 3, 2, 1].map(makePostMeta);
const ALL_POSTS: Post[] = [6, 5, 4, 3, 2, 1].map(makePost);

const CATEGORIES: Record<string, number> = {
  '개발': 3,
  '디자인': 2,
};

beforeEach(() => {
  mockGetAllPosts.mockResolvedValue(ALL_POST_META);
  mockGetPostBySlug.mockImplementation(async (slug: string) => {
    return ALL_POSTS.find((p) => p.slug === slug) ?? null;
  });
  mockGetCategories.mockResolvedValue(CATEGORIES);
});

describe('Home page', () => {
  describe('bio section', () => {
    it('renders a bio/intro section', async () => {
      render(await Home());
      expect(screen.getByRole('region', { name: '소개' })).toBeInTheDocument();
    });

    it('bio section contains Korean text', async () => {
      render(await Home());
      const bio = screen.getByRole('region', { name: '소개' });
      expect(bio.textContent).toMatch(/블로그|개발|Next\.js/);
    });
  });

  describe('recent posts', () => {
    it('renders exactly 5 post articles (not all 6)', async () => {
      render(await Home());
      const articles = screen.getAllByRole('article');
      expect(articles).toHaveLength(5);
    });

    it('renders the most recent posts (posts 6 down to 2)', async () => {
      render(await Home());
      // Post 6 is most recent, post 1 is omitted
      expect(screen.getByText('포스트 제목 6')).toBeInTheDocument();
      expect(screen.getByText('포스트 제목 2')).toBeInTheDocument();
      expect(screen.queryByText('포스트 제목 1')).not.toBeInTheDocument();
    });

    it('post titles link to /blog/[slug]', async () => {
      render(await Home());
      const link = screen.getByRole('link', { name: '포스트 제목 6' });
      expect(link).toHaveAttribute('href', '/blog/post-slug-6');
    });
  });

  describe('category summary', () => {
    it('renders a category section', async () => {
      render(await Home());
      expect(screen.getByRole('complementary', { name: '카테고리' })).toBeInTheDocument();
    });

    it('shows each category with its count', async () => {
      render(await Home());
      expect(screen.getByRole('link', { name: '개발 (3)' })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: '디자인 (2)' })).toBeInTheDocument();
    });

    it('category links point to /category/[encoded-name]', async () => {
      render(await Home());
      const devLink = screen.getByRole('link', { name: '개발 (3)' });
      expect(devLink).toHaveAttribute('href', `/category/${encodeURIComponent('개발')}`);
      const designLink = screen.getByRole('link', { name: '디자인 (2)' });
      expect(designLink).toHaveAttribute('href', `/category/${encodeURIComponent('디자인')}`);
    });
  });

  describe('section headings', () => {
    it('has a 최근 게시물 heading', async () => {
      render(await Home());
      expect(screen.getByRole('heading', { name: '최근 게시물' })).toBeInTheDocument();
    });

    it('has a 카테고리 heading', async () => {
      render(await Home());
      expect(screen.getByRole('heading', { name: '카테고리' })).toBeInTheDocument();
    });
  });
});
