import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import ProductListing from '@/app/products/ProductListing';
import { makeProduct, makePageResponse, makeProductList } from '@/lib/test-factories';

jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  useSearchParams: jest.fn(),
}));

jest.mock('@/lib/api', () => ({
  searchProducts: jest.fn(),
}));

import { useRouter, useSearchParams } from 'next/navigation';
import { searchProducts } from '@/lib/api';

const mockUseRouter = useRouter as jest.Mock;
const mockUseSearchParams = useSearchParams as jest.Mock;
const mockSearchProducts = searchProducts as jest.Mock;

function createMockSearchParams(params: Record<string, string> = {}) {
  return {
    get: (key: string) => params[key] ?? null,
  };
}

describe('ProductListing', () => {
  const mockPush = jest.fn();

  beforeEach(() => {
    jest.useFakeTimers();
    mockUseRouter.mockReturnValue({ push: mockPush });
    mockUseSearchParams.mockReturnValue(createMockSearchParams());

    const products = makeProductList(6);
    const pageResponse = makePageResponse(products, {
      totalElements: 6,
      totalPages: 1,
      number: 0,
    });
    mockSearchProducts.mockResolvedValue(pageResponse);
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.clearAllMocks();
  });

  // ── Rendering ──────────────────────────────────────────────

  it('renders page heading, search input, category dropdown, price inputs, and sort', async () => {
    render(<ProductListing />);
    await act(async () => {
      await Promise.resolve();
    });

    expect(screen.getByRole('heading', { name: /products/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/search/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/category/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/min price/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/max price/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/sort by/i)).toBeInTheDocument();
  });

  it('shows loading skeleton initially then product cards after fetch', async () => {
    render(<ProductListing />);

    // Loading skeleton should be visible initially
    expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();

    // Wait for products to load
    await act(async () => {
      await Promise.resolve();
    });

    // Should show products after loading
    await waitFor(() => {
      expect(screen.queryByTestId('loading-skeleton')).not.toBeInTheDocument();
    });
    expect(screen.getByText('6 products found')).toBeInTheDocument();
  });

  it('calls searchProducts with default params on mount', async () => {
    render(<ProductListing />);
    await act(async () => {
      await Promise.resolve();
    });

    expect(mockSearchProducts).toHaveBeenCalledWith(
      expect.objectContaining({
        page: 0,
        size: 12,
        sortBy: 'createdAt',
        sortDir: 'desc',
      }),
    );
  });

  // ── Search ─────────────────────────────────────────────────

  it('debounces search input at 300ms', async () => {
    render(<ProductListing />);
    await act(async () => {
      await Promise.resolve();
    });

    const searchInput = screen.getByLabelText(/search/i);
    fireEvent.change(searchInput, { target: { value: 'laptop' } });

    // Should not push immediately
    expect(mockPush).not.toHaveBeenCalled();

    // Advance past debounce
    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(mockPush).toHaveBeenCalledWith(
      expect.stringContaining('keyword=laptop'),
    );
  });

  it('does not push before 300ms debounce elapses', async () => {
    render(<ProductListing />);
    await act(async () => {
      await Promise.resolve();
    });

    const searchInput = screen.getByLabelText(/search/i);
    fireEvent.change(searchInput, { target: { value: 'lap' } });

    act(() => {
      jest.advanceTimersByTime(100);
    });

    expect(mockPush).not.toHaveBeenCalled();

    // Change again before first debounce fires — should reset timer
    fireEvent.change(searchInput, { target: { value: 'laptop' } });

    act(() => {
      jest.advanceTimersByTime(200);
    });

    // Still not enough total time since last keystroke
    expect(mockPush).not.toHaveBeenCalled();

    act(() => {
      jest.advanceTimersByTime(100);
    });

    // Now 300ms after last change
    expect(mockPush).toHaveBeenCalledTimes(1);
    expect(mockPush).toHaveBeenCalledWith(expect.stringContaining('keyword=laptop'));
  });

  // ── Category Filter ────────────────────────────────────────

  it('updates URL with category param when category is selected', async () => {
    render(<ProductListing />);
    await act(async () => {
      await Promise.resolve();
    });

    const categorySelect = screen.getByLabelText(/category/i);
    fireEvent.change(categorySelect, { target: { value: 'Electronics' } });

    expect(mockPush).toHaveBeenCalledWith(
      expect.stringContaining('category=Electronics'),
    );
  });

  it('removes category param when "All Categories" is selected', async () => {
    mockUseSearchParams.mockReturnValue(
      createMockSearchParams({ category: 'Electronics' }),
    );
    render(<ProductListing />);
    await act(async () => {
      await Promise.resolve();
    });

    // Use role selector to avoid conflict with filter chip aria-label
    const categorySelect = screen.getByRole('combobox', { name: /category/i });
    fireEvent.change(categorySelect, { target: { value: '' } });

    expect(mockPush).toHaveBeenCalledWith(
      expect.not.stringContaining('category='),
    );
  });

  // ── Sort ───────────────────────────────────────────────────

  it('updates URL with sort params when sort is changed', async () => {
    render(<ProductListing />);
    await act(async () => {
      await Promise.resolve();
    });

    const sortSelect = screen.getByLabelText(/sort by/i);
    fireEvent.change(sortSelect, { target: { value: 'price-asc' } });

    expect(mockPush).toHaveBeenCalledWith(
      expect.stringContaining('sortBy=price'),
    );
    expect(mockPush).toHaveBeenCalledWith(
      expect.stringContaining('sortDir=asc'),
    );
  });

  // ── Price Range ────────────────────────────────────────────

  it('debounces min price input and updates URL', async () => {
    render(<ProductListing />);
    await act(async () => {
      await Promise.resolve();
    });

    const minPriceInput = screen.getByLabelText(/min price/i);
    fireEvent.change(minPriceInput, { target: { value: '10' } });

    expect(mockPush).not.toHaveBeenCalled();

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(mockPush).toHaveBeenCalledWith(
      expect.stringContaining('minPrice=10'),
    );
  });

  it('debounces max price input and updates URL', async () => {
    render(<ProductListing />);
    await act(async () => {
      await Promise.resolve();
    });

    const maxPriceInput = screen.getByLabelText(/max price/i);
    fireEvent.change(maxPriceInput, { target: { value: '100' } });

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(mockPush).toHaveBeenCalledWith(
      expect.stringContaining('maxPrice=100'),
    );
  });

  // ── Filter Chips ───────────────────────────────────────────

  it('renders filter chips for active filters', async () => {
    mockUseSearchParams.mockReturnValue(
      createMockSearchParams({
        keyword: 'laptop',
        category: 'Electronics',
        minPrice: '10',
        maxPrice: '500',
      }),
    );
    render(<ProductListing />);
    await act(async () => {
      await Promise.resolve();
    });

    const chipContainer = screen.getByTestId('filter-chips');
    expect(chipContainer).toBeInTheDocument();

    expect(screen.getByText(/Search: laptop/)).toBeInTheDocument();
    expect(screen.getByText(/Category: Electronics/)).toBeInTheDocument();
    expect(screen.getByText(/Min: \$10/)).toBeInTheDocument();
    expect(screen.getByText(/Max: \$500/)).toBeInTheDocument();
  });

  it('removes filter when chip × is clicked', async () => {
    mockUseSearchParams.mockReturnValue(
      createMockSearchParams({ category: 'Electronics' }),
    );
    render(<ProductListing />);
    await act(async () => {
      await Promise.resolve();
    });

    const chip = screen.getByLabelText(/remove Category: Electronics filter/i);
    fireEvent.click(chip);

    expect(mockPush).toHaveBeenCalledWith(
      expect.not.stringContaining('category='),
    );
  });

  it('does not render filter chips container when no filters are active', async () => {
    render(<ProductListing />);
    await act(async () => {
      await Promise.resolve();
    });

    expect(screen.queryByTestId('filter-chips')).not.toBeInTheDocument();
  });

  // ── URL Params Restore ─────────────────────────────────────

  it('passes URL params to searchProducts API call', async () => {
    mockUseSearchParams.mockReturnValue(
      createMockSearchParams({
        keyword: 'phone',
        category: 'Electronics',
        minPrice: '50',
        maxPrice: '200',
        sortBy: 'price',
        sortDir: 'asc',
        page: '2',
      }),
    );
    render(<ProductListing />);
    await act(async () => {
      await Promise.resolve();
    });

    expect(mockSearchProducts).toHaveBeenCalledWith(
      expect.objectContaining({
        keyword: 'phone',
        category: 'Electronics',
        minPrice: 50,
        maxPrice: 200,
        sortBy: 'price',
        sortDir: 'asc',
        page: 2,
        size: 12,
      }),
    );
  });

  it('restores search input value from URL keyword param', async () => {
    mockUseSearchParams.mockReturnValue(
      createMockSearchParams({ keyword: 'laptop' }),
    );
    render(<ProductListing />);
    await act(async () => {
      await Promise.resolve();
    });

    // Use role selector to avoid conflict with filter chip aria-label
    expect(screen.getByRole('textbox', { name: /search/i })).toHaveValue('laptop');
  });

  it('restores category select value from URL param', async () => {
    mockUseSearchParams.mockReturnValue(
      createMockSearchParams({ category: 'Clothing' }),
    );
    render(<ProductListing />);
    await act(async () => {
      await Promise.resolve();
    });

    // Use role selector to avoid conflict with filter chip aria-label
    expect(screen.getByRole('combobox', { name: /category/i })).toHaveValue('Clothing');
  });

  // ── Pagination ─────────────────────────────────────────────

  it('renders pagination when multiple pages exist', async () => {
    const products = makeProductList(12);
    mockSearchProducts.mockResolvedValue(
      makePageResponse(products, {
        totalElements: 24,
        totalPages: 2,
        number: 0,
        first: true,
        last: false,
      }),
    );
    render(<ProductListing />);
    await act(async () => {
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(screen.getByLabelText(/next page/i)).toBeInTheDocument();
    });
  });

  it('updates page param when pagination is clicked', async () => {
    const products = makeProductList(12);
    mockSearchProducts.mockResolvedValue(
      makePageResponse(products, {
        totalElements: 24,
        totalPages: 2,
        number: 0,
        first: true,
        last: false,
      }),
    );
    render(<ProductListing />);
    await act(async () => {
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(screen.getByLabelText(/page 2/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByLabelText(/page 2/i));

    expect(mockPush).toHaveBeenCalledWith(
      expect.stringContaining('page=1'),
    );
  });

  // ── Empty State ────────────────────────────────────────────

  it('shows empty state when no products match', async () => {
    mockSearchProducts.mockResolvedValue(
      makePageResponse([], {
        totalElements: 0,
        totalPages: 0,
        number: 0,
      }),
    );
    render(<ProductListing />);
    await act(async () => {
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(screen.getByTestId('empty-state')).toBeInTheDocument();
    });
    expect(screen.getByText(/no products found/i)).toBeInTheDocument();
    expect(screen.getByText(/try adjusting your search/i)).toBeInTheDocument();
  });

  // ── Product Count ──────────────────────────────────────────

  it('shows singular "product" text when only 1 result', async () => {
    const products = [makeProduct({ id: 1, name: 'Solo Product' })];
    mockSearchProducts.mockResolvedValue(
      makePageResponse(products, { totalElements: 1 }),
    );
    render(<ProductListing />);
    await act(async () => {
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(screen.getByText('1 product found')).toBeInTheDocument();
    });
  });

  // ── Reset Page on Filter Change ────────────────────────────

  it('resets page to 0 when category filter changes', async () => {
    mockUseSearchParams.mockReturnValue(
      createMockSearchParams({ page: '3' }),
    );
    render(<ProductListing />);
    await act(async () => {
      await Promise.resolve();
    });

    const categorySelect = screen.getByLabelText(/category/i);
    fireEvent.change(categorySelect, { target: { value: 'Books' } });

    // The pushed URL should not contain page=3
    const pushedUrl = mockPush.mock.calls[0][0] as string;
    expect(pushedUrl).toContain('category=Books');
    expect(pushedUrl).not.toContain('page=3');
  });
});
