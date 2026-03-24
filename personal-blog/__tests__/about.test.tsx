import React from 'react';
import { render, screen } from '@testing-library/react';

// ── Mocks ────────────────────────────────────────────────────────────────────

const ABOUT_CONTENT = `## 안녕하세요, 반갑습니다!

저는 프론트엔드 개발자입니다.

## 기술 스택

- TypeScript
- Next.js`;

jest.mock('fs', () => ({
  promises: {
    readFile: jest.fn().mockResolvedValue(
      `---\ntitle: 소개\n---\n${ABOUT_CONTENT}`,
    ),
  },
}));

jest.mock('next-mdx-remote/rsc', () => ({
  MDXRemote: ({ source }: { source: string }) => (
    <div data-testid="mdx-content">{source}</div>
  ),
}));

import AboutPage from '@/app/about/page';

// ── Setup ─────────────────────────────────────────────────────────────────────

beforeEach(() => {
  jest.clearAllMocks();
});

// ── AboutPage ─────────────────────────────────────────────────────────────────

describe('AboutPage', () => {
  it('renders the MDX content area', async () => {
    render(await AboutPage());
    expect(screen.getByTestId('mdx-content')).toBeInTheDocument();
  });

  it('renders the about.md content (without frontmatter)', async () => {
    render(await AboutPage());
    const mdxContent = screen.getByTestId('mdx-content');
    // frontmatter (title: 소개) should NOT appear as raw text
    expect(mdxContent.textContent).not.toContain('title: 소개');
    // body content should appear
    expect(mdxContent.textContent).toContain('안녕하세요');
  });

  it('renders in a prose container', async () => {
    const { container } = render(await AboutPage());
    const proseDiv = container.querySelector('.prose');
    expect(proseDiv).not.toBeNull();
  });

  it('reads from content/about.md', async () => {
    const fs = require('fs');
    render(await AboutPage());
    expect(fs.promises.readFile).toHaveBeenCalledWith(
      expect.stringContaining('content/about.md'),
      'utf-8',
    );
  });
});
