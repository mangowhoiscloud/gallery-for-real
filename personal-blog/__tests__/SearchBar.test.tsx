import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { useRouter, useSearchParams } from 'next/navigation';
import SearchBar, { filterPosts } from '../components/SearchBar';
import type { PostMeta } from '../lib/types';

jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  useSearchParams: jest.fn(),
}));

const posts: PostMeta[] = [
  { slug: 'a', title: 'React Tutorial', date: '2026-01-01', category: '개발', tags: ['react', 'javascript'] },
  { slug: 'b', title: 'TypeScript Guide', date: '2026-01-02', category: '개발', tags: ['typescript'] },
  { slug: 'c', title: 'Korean Food', date: '2026-01-03', category: '음식', tags: ['korean', 'recipe'] },
];

const mockReplace = jest.fn();

function setupMocks(qParam: string | null = null) {
  (useRouter as jest.Mock).mockReturnValue({ replace: mockReplace });
  (useSearchParams as jest.Mock).mockReturnValue({
    get: jest.fn((key: string) => (key === 'q' ? qParam : null)),
    toString: jest.fn(() => (qParam ? `q=${qParam}` : '')),
  });
}

describe('filterPosts', () => {
  test('empty query returns all posts', () => {
    expect(filterPosts(posts, '')).toHaveLength(3);
  });

  test('whitespace-only query returns all posts', () => {
    expect(filterPosts(posts, '   ')).toHaveLength(3);
  });

  test('filters by title substring (case-insensitive)', () => {
    expect(filterPosts(posts, 'react')).toHaveLength(1);
    expect(filterPosts(posts, 'REACT')).toHaveLength(1);
    expect(filterPosts(posts, 'guide')).toHaveLength(1);
  });

  test('filters by category', () => {
    expect(filterPosts(posts, '개발')).toHaveLength(2);
    expect(filterPosts(posts, '음식')).toHaveLength(1);
  });

  test('filters by tag', () => {
    expect(filterPosts(posts, 'typescript')).toHaveLength(1);
    expect(filterPosts(posts, 'korean')).toHaveLength(1);
    expect(filterPosts(posts, 'javascript')).toHaveLength(1);
  });

  test('no match returns empty array', () => {
    expect(filterPosts(posts, 'xxxxxxxxxx')).toHaveLength(0);
  });
});

describe('SearchBar component', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    mockReplace.mockClear();
    setupMocks();
  });

  afterEach(() => {
    jest.runAllTimers();
    jest.useRealTimers();
  });

  test('renders search input with placeholder', () => {
    render(<SearchBar posts={posts} />);
    expect(screen.getByRole('searchbox', { name: '검색' })).toBeInTheDocument();
    expect(screen.getByPlaceholderText('검색...')).toBeInTheDocument();
  });

  test('shows total post count when query is empty', () => {
    render(<SearchBar posts={posts} />);
    expect(screen.getByTestId('results-count')).toHaveTextContent('3개 결과');
  });

  test('filters by title and updates count', async () => {
    render(<SearchBar posts={posts} />);
    await act(async () => {
      fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'React' } });
    });
    expect(screen.getByTestId('results-count')).toHaveTextContent('1개 결과');
  });

  test('filters by category and updates count', async () => {
    render(<SearchBar posts={posts} />);
    await act(async () => {
      fireEvent.change(screen.getByRole('searchbox'), { target: { value: '음식' } });
    });
    expect(screen.getByTestId('results-count')).toHaveTextContent('1개 결과');
  });

  test('filters by tag and updates count', async () => {
    render(<SearchBar posts={posts} />);
    await act(async () => {
      fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'typescript' } });
    });
    expect(screen.getByTestId('results-count')).toHaveTextContent('1개 결과');
  });

  test('debounces URL update — no router.replace on each keystroke', async () => {
    render(<SearchBar posts={posts} />);
    const input = screen.getByRole('searchbox');

    fireEvent.change(input, { target: { value: 'R' } });
    fireEvent.change(input, { target: { value: 'Re' } });
    fireEvent.change(input, { target: { value: 'Rea' } });

    // URL not yet updated
    expect(mockReplace).not.toHaveBeenCalled();

    // After 300ms debounce fires
    await act(async () => {
      jest.advanceTimersByTime(300);
    });

    // Only one URL update (the last value)
    expect(mockReplace).toHaveBeenCalledTimes(1);
  });

  test('sets URL q param after debounce', async () => {
    render(<SearchBar posts={posts} />);
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'React' } });

    await act(async () => {
      jest.advanceTimersByTime(300);
    });

    expect(mockReplace).toHaveBeenCalledWith(expect.stringContaining('q=React'));
  });

  test('removes URL q param when query is cleared', async () => {
    render(<SearchBar posts={posts} />);
    const input = screen.getByRole('searchbox');

    fireEvent.change(input, { target: { value: 'React' } });
    await act(async () => { jest.advanceTimersByTime(300); });
    mockReplace.mockClear();

    fireEvent.change(input, { target: { value: '' } });
    await act(async () => { jest.advanceTimersByTime(300); });

    expect(mockReplace).toHaveBeenCalledWith(expect.not.stringContaining('q='));
  });

  test('calls onFilter with filtered posts when query changes', async () => {
    const onFilter = jest.fn();
    render(<SearchBar posts={posts} onFilter={onFilter} />);

    await act(async () => {
      fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'React' } });
    });

    expect(onFilter).toHaveBeenCalledWith(
      expect.arrayContaining([expect.objectContaining({ slug: 'a' })])
    );
    // Only the React Tutorial matches
    const lastCall = onFilter.mock.calls[onFilter.mock.calls.length - 1][0];
    expect(lastCall).toHaveLength(1);
  });

  test('initializes query and count from URL q param', () => {
    (useSearchParams as jest.Mock).mockReturnValue({
      get: jest.fn((key: string) => (key === 'q' ? 'typescript' : null)),
      toString: jest.fn(() => 'q=typescript'),
    });
    render(<SearchBar posts={posts} />);
    expect(screen.getByRole('searchbox')).toHaveValue('typescript');
    expect(screen.getByTestId('results-count')).toHaveTextContent('1개 결과');
  });

  test('shows 0 results for no-match query', async () => {
    render(<SearchBar posts={posts} />);
    await act(async () => {
      fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'xxxxxxxxxx' } });
    });
    expect(screen.getByTestId('results-count')).toHaveTextContent('0개 결과');
  });
});
