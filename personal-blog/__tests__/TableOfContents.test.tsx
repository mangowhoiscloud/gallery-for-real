import { render, screen, fireEvent, act } from '@testing-library/react';
import TableOfContents from '@/components/TableOfContents';
import type { Heading } from '@/lib/markdown';

let intersectionCallback: IntersectionObserverCallback = () => {};
const mockObserve = jest.fn();
const mockDisconnect = jest.fn();

beforeEach(() => {
  jest.clearAllMocks();
  global.IntersectionObserver = jest.fn((callback: IntersectionObserverCallback) => {
    intersectionCallback = callback;
    return {
      observe: mockObserve,
      disconnect: mockDisconnect,
      unobserve: jest.fn(),
      root: null,
      rootMargin: '',
      thresholds: [],
      takeRecords: () => [],
    };
  }) as unknown as typeof IntersectionObserver;
});

const headings: Heading[] = [
  { id: 'intro', text: '소개', level: 2 },
  { id: 'details', text: '세부 내용', level: 3 },
  { id: 'conclusion', text: '결론', level: 2 },
];

describe('TableOfContents', () => {
  it('renders null for empty headings', () => {
    const { container } = render(<TableOfContents headings={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders nav with accessible label', () => {
    render(<TableOfContents headings={headings} />);
    expect(screen.getByRole('navigation', { name: 'Table of contents' })).toBeInTheDocument();
  });

  it('desktop list always renders all headings', () => {
    render(<TableOfContents headings={headings} />);
    // mobile list is hidden (isOpen=false), desktop always rendered
    expect(screen.getAllByRole('link', { name: '소개' })).toHaveLength(1);
    expect(screen.getAllByRole('link', { name: '세부 내용' })).toHaveLength(1);
    expect(screen.getAllByRole('link', { name: '결론' })).toHaveLength(1);
  });

  it('heading links point to correct anchor hrefs', () => {
    render(<TableOfContents headings={headings} />);
    expect(screen.getByRole('link', { name: '소개' })).toHaveAttribute('href', '#intro');
    expect(screen.getByRole('link', { name: '세부 내용' })).toHaveAttribute('href', '#details');
    expect(screen.getByRole('link', { name: '결론' })).toHaveAttribute('href', '#conclusion');
  });

  it('h3 heading li has 1rem left indentation', () => {
    render(<TableOfContents headings={headings} />);
    const h3Link = screen.getByRole('link', { name: '세부 내용' });
    expect(h3Link.parentElement).toHaveStyle({ paddingLeft: '1rem' });
  });

  it('h2 heading li does not have h3-level indentation', () => {
    render(<TableOfContents headings={headings} />);
    const h2Link = screen.getByRole('link', { name: '소개' });
    expect(h2Link.parentElement).not.toHaveStyle({ paddingLeft: '1rem' });
  });

  it('renders mobile toggle button', () => {
    render(<TableOfContents headings={headings} />);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('mobile toggle starts closed (aria-expanded false)', () => {
    render(<TableOfContents headings={headings} />);
    expect(screen.getByRole('button')).toHaveAttribute('aria-expanded', 'false');
  });

  it('clicking toggle opens mobile TOC and doubles link count', () => {
    render(<TableOfContents headings={headings} />);
    fireEvent.click(screen.getByRole('button'));
    expect(screen.getByRole('button')).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getAllByRole('link', { name: '소개' })).toHaveLength(2);
  });

  it('clicking toggle twice closes mobile TOC', () => {
    render(<TableOfContents headings={headings} />);
    fireEvent.click(screen.getByRole('button'));
    fireEvent.click(screen.getByRole('button'));
    expect(screen.getByRole('button')).toHaveAttribute('aria-expanded', 'false');
    expect(screen.getAllByRole('link', { name: '소개' })).toHaveLength(1);
  });

  it('desktop section has sticky positioning', () => {
    render(<TableOfContents headings={headings} />);
    expect(screen.getByTestId('toc-desktop')).toHaveStyle({ position: 'sticky' });
  });

  it('active heading gets aria-current="location" on intersection', () => {
    const el = document.createElement('h2');
    el.id = 'intro';
    document.body.appendChild(el);

    render(<TableOfContents headings={headings} />);

    act(() => {
      intersectionCallback(
        [{ isIntersecting: true, target: el } as unknown as IntersectionObserverEntry],
        {} as IntersectionObserver,
      );
    });

    expect(screen.getByRole('link', { name: '소개' })).toHaveAttribute('aria-current', 'location');
    document.body.removeChild(el);
  });

  it('non-intersecting headings have no aria-current', () => {
    const el = document.createElement('h2');
    el.id = 'intro';
    document.body.appendChild(el);

    render(<TableOfContents headings={headings} />);

    act(() => {
      intersectionCallback(
        [{ isIntersecting: true, target: el } as unknown as IntersectionObserverEntry],
        {} as IntersectionObserver,
      );
    });

    expect(screen.getByRole('link', { name: '결론' })).not.toHaveAttribute('aria-current');
    document.body.removeChild(el);
  });
});
