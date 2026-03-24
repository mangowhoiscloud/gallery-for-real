import React from 'react';
import { render, screen } from '@testing-library/react';

// ── Mocks ────────────────────────────────────────────────────────────────────

jest.mock('next/link', () => {
  const Link = ({ href, children, ...props }: { href: string; children: React.ReactNode; [key: string]: unknown }) => (
    <a href={href} {...props}>{children}</a>
  );
  Link.displayName = 'Link';
  return Link;
});

import Loading from '@/app/loading';
import NotFound from '@/app/not-found';
import PostNotFound from '@/app/blog/[slug]/not-found';

// ── Loading ────────────────────────────────────────────────────────────────

describe('Loading', () => {
  it('renders with role="status"', () => {
    render(<Loading />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders the spinner element', () => {
    render(<Loading />);
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('renders "로딩 중..." text', () => {
    render(<Loading />);
    expect(screen.getByText('로딩 중...')).toBeInTheDocument();
  });

  it('has aria-label for accessibility', () => {
    render(<Loading />);
    expect(screen.getByLabelText('로딩 중')).toBeInTheDocument();
  });
});

// ── NotFound (global 404) ─────────────────────────────────────────────────

describe('NotFound', () => {
  it('renders 404 heading', () => {
    render(<NotFound />);
    expect(screen.getByText('404')).toBeInTheDocument();
  });

  it('renders the Korean not-found message', () => {
    render(<NotFound />);
    expect(screen.getByText('페이지를 찾을 수 없습니다')).toBeInTheDocument();
  });

  it('renders description text', () => {
    render(<NotFound />);
    expect(screen.getByText(/요청하신 페이지가 존재하지 않거나/)).toBeInTheDocument();
  });

  it('renders a link back to home', () => {
    render(<NotFound />);
    const homeLink = screen.getByRole('link', { name: '홈으로 돌아가기' });
    expect(homeLink).toBeInTheDocument();
    expect(homeLink).toHaveAttribute('href', '/');
  });
});

// ── PostNotFound (blog/[slug] 404) ────────────────────────────────────────

describe('PostNotFound', () => {
  it('renders 404 heading', () => {
    render(<PostNotFound />);
    expect(screen.getByText('404')).toBeInTheDocument();
  });

  it('renders the Korean post not-found message', () => {
    render(<PostNotFound />);
    expect(screen.getByText('게시물을 찾을 수 없습니다')).toBeInTheDocument();
  });

  it('renders description text', () => {
    render(<PostNotFound />);
    expect(screen.getByText(/요청하신 게시물이 존재하지 않거나/)).toBeInTheDocument();
  });

  it('renders a link to blog list', () => {
    render(<PostNotFound />);
    const blogLink = screen.getByRole('link', { name: '블로그 목록으로' });
    expect(blogLink).toBeInTheDocument();
    expect(blogLink).toHaveAttribute('href', '/blog');
  });

  it('renders a link back to home', () => {
    render(<PostNotFound />);
    const homeLink = screen.getByRole('link', { name: '홈으로 돌아가기' });
    expect(homeLink).toBeInTheDocument();
    expect(homeLink).toHaveAttribute('href', '/');
  });

  it('PostNotFound has different message than global NotFound', () => {
    const { unmount } = render(<PostNotFound />);
    expect(screen.getByText('게시물을 찾을 수 없습니다')).toBeInTheDocument();
    unmount();
    render(<NotFound />);
    expect(screen.getByText('페이지를 찾을 수 없습니다')).toBeInTheDocument();
  });
});
