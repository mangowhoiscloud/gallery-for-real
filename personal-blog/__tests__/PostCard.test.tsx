import React from 'react';
import { render, screen } from '@testing-library/react';
import PostCard from '@/components/PostCard';
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

const SAMPLE_POST: Post = {
  title: 'Next.js App Router 완전 가이드',
  date: '2026-02-20',
  category: '개발',
  tags: ['Next.js', 'React', 'TypeScript'],
  slug: 'nextjs-app-router-guide',
  content:
    '## 소개\n\nNext.js 13부터 새롭게 도입된 App Router에 대해 알아봅시다. ' +
    '기존의 Pages Router와 다르게 서버 컴포넌트를 기본으로 사용합니다. '.repeat(5),
};

const MINIMAL_POST: Post = {
  title: '최소 포스트',
  date: '2026-01-01',
  category: '회고',
  tags: [],
  slug: 'minimal-post',
  content: '짧은 내용입니다.',
};

describe('PostCard', () => {
  describe('title', () => {
    it('renders the post title', () => {
      render(<PostCard post={SAMPLE_POST} />);
      expect(screen.getByRole('heading', { name: /Next\.js App Router 완전 가이드/ })).toBeInTheDocument();
    });

    it('title links to /blog/[slug]', () => {
      render(<PostCard post={SAMPLE_POST} />);
      const titleLink = screen.getByRole('link', { name: /Next\.js App Router 완전 가이드/ });
      expect(titleLink).toHaveAttribute('href', '/blog/nextjs-app-router-guide');
    });
  });

  describe('date', () => {
    it('renders the post date in Korean format', () => {
      render(<PostCard post={SAMPLE_POST} />);
      expect(screen.getByText('2026년 2월 20일')).toBeInTheDocument();
    });

    it('date element has dateTime attribute with ISO value', () => {
      render(<PostCard post={SAMPLE_POST} />);
      const timeEl = screen.getByText('2026년 2월 20일').closest('time');
      expect(timeEl).toHaveAttribute('dateTime', '2026-02-20');
    });
  });

  describe('category', () => {
    it('renders the category name', () => {
      render(<PostCard post={SAMPLE_POST} />);
      expect(screen.getByRole('link', { name: '개발' })).toBeInTheDocument();
    });

    it('category links to /category/[name]', () => {
      render(<PostCard post={SAMPLE_POST} />);
      const catLink = screen.getByRole('link', { name: '개발' });
      expect(catLink).toHaveAttribute('href', '/category/%EA%B0%9C%EB%B0%9C');
    });
  });

  describe('tags', () => {
    it('renders all tags', () => {
      render(<PostCard post={SAMPLE_POST} />);
      expect(screen.getByText('Next.js')).toBeInTheDocument();
      expect(screen.getByText('React')).toBeInTheDocument();
      expect(screen.getByText('TypeScript')).toBeInTheDocument();
    });

    it('does not render tags section when tags array is empty', () => {
      render(<PostCard post={MINIMAL_POST} />);
      expect(screen.queryByText('Next.js')).not.toBeInTheDocument();
    });
  });

  describe('excerpt', () => {
    it('renders an excerpt of the post content', () => {
      render(<PostCard post={SAMPLE_POST} />);
      // excerpt should start with stripped heading text
      const excerptEl = screen.getByText(/소개/);
      expect(excerptEl).toBeInTheDocument();
    });

    it('truncates long content with "..."', () => {
      const longPost: Post = {
        ...MINIMAL_POST,
        slug: 'long-post',
        content: '가'.repeat(300),
      };
      render(<PostCard post={longPost} />);
      const p = screen.getByText(/가+\.\.\./);
      expect(p.textContent).toMatch(/\.\.\.$/);
    });

    it('renders short content without "..."', () => {
      render(<PostCard post={MINIMAL_POST} />);
      expect(screen.getByText('짧은 내용입니다.')).toBeInTheDocument();
    });
  });

  describe('reading time', () => {
    it('renders reading time in "N분 소요" format', () => {
      render(<PostCard post={SAMPLE_POST} />);
      expect(screen.getByText(/\d+분 소요/)).toBeInTheDocument();
    });

    it('shows at least 1분 for any content', () => {
      render(<PostCard post={MINIMAL_POST} />);
      expect(screen.getByText('1분 소요')).toBeInTheDocument();
    });
  });

  describe('rendered as article', () => {
    it('wraps post in an <article> element', () => {
      render(<PostCard post={SAMPLE_POST} />);
      const article = screen.getByRole('article');
      expect(article).toBeInTheDocument();
    });
  });
});
