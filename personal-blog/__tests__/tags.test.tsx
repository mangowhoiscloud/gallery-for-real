import React from 'react';
import { render, screen } from '@testing-library/react';

// ── Mocks ────────────────────────────────────────────────────────────────────

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
  getAllTags: jest.fn(),
}));

import { getAllTags } from '@/lib/posts';
import TagsPage from '@/app/tags/page';

// ── Fixtures ──────────────────────────────────────────────────────────────────

const TAGS: Record<string, number> = {
  'TypeScript': 3,
  'Next.js': 2,
  'CSS': 1,
  '디자인': 1,
};

// ── Setup ─────────────────────────────────────────────────────────────────────

beforeEach(() => {
  jest.clearAllMocks();
  (getAllTags as jest.Mock).mockResolvedValue(TAGS);
});

// ── TagsPage ──────────────────────────────────────────────────────────────────

describe('TagsPage — heading', () => {
  it('renders 태그 as h1', async () => {
    render(await TagsPage());
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('태그');
  });
});

describe('TagsPage — tag list', () => {
  it('renders all tags', async () => {
    render(await TagsPage());
    expect(screen.getByRole('link', { name: /TypeScript/ })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Next\.js/ })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /CSS/ })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /디자인/ })).toBeInTheDocument();
  });

  it('displays each tag with its count', async () => {
    render(await TagsPage());
    expect(screen.getByRole('link', { name: 'TypeScript (3)' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Next.js (2)' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'CSS (1)' })).toBeInTheDocument();
  });

  it('tag links point to /blog?tag=<tagname>', async () => {
    render(await TagsPage());
    const tsLink = screen.getByRole('link', { name: 'TypeScript (3)' });
    expect(tsLink).toHaveAttribute('href', '/blog?tag=TypeScript');
  });

  it('encodes tag names in URLs', async () => {
    render(await TagsPage());
    const designLink = screen.getByRole('link', { name: '디자인 (1)' });
    expect(designLink).toHaveAttribute('href', `/blog?tag=${encodeURIComponent('디자인')}`);
  });

  it('renders correct number of tag list items', async () => {
    render(await TagsPage());
    const listItems = screen.getAllByRole('listitem');
    expect(listItems).toHaveLength(4);
  });
});

describe('TagsPage — empty state', () => {
  it('renders no list items when there are no tags', async () => {
    (getAllTags as jest.Mock).mockResolvedValue({});
    render(await TagsPage());
    expect(screen.queryAllByRole('listitem')).toHaveLength(0);
  });
});
