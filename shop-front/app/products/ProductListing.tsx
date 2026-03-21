'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { searchProducts } from '@/lib/api';
import type { Product, PageResponse, SortField, SortDir } from '@/lib/types';
import ProductGrid from '@/components/ui/ProductGrid';
import LoadingSkeleton from '@/components/ui/LoadingSkeleton';
import Pagination from '@/components/ui/Pagination';

const SORT_OPTIONS: { label: string; sortBy: SortField; sortDir: SortDir }[] = [
  { label: 'Name A-Z', sortBy: 'name', sortDir: 'asc' },
  { label: 'Name Z-A', sortBy: 'name', sortDir: 'desc' },
  { label: 'Price Low-High', sortBy: 'price', sortDir: 'asc' },
  { label: 'Price High-Low', sortBy: 'price', sortDir: 'desc' },
  { label: 'Newest', sortBy: 'createdAt', sortDir: 'desc' },
];

const CATEGORIES = ['Electronics', 'Clothing', 'Home', 'Books', 'Sports'];

const PAGE_SIZE = 12;

function sortKey(sortBy: string, sortDir: string): string {
  return `${sortBy}-${sortDir}`;
}

export default function ProductListing() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Read filters from URL
  const keyword = searchParams.get('keyword') ?? '';
  const category = searchParams.get('category') ?? '';
  const minPrice = searchParams.get('minPrice') ?? '';
  const maxPrice = searchParams.get('maxPrice') ?? '';
  const sortBy = (searchParams.get('sortBy') as SortField) ?? 'createdAt';
  const sortDir = (searchParams.get('sortDir') as SortDir) ?? 'desc';
  const page = parseInt(searchParams.get('page') ?? '0', 10);

  // Local state for debounced search input
  const [searchInput, setSearchInput] = useState(keyword);
  const [minPriceInput, setMinPriceInput] = useState(minPrice);
  const [maxPriceInput, setMaxPriceInput] = useState(maxPrice);

  // Data state
  const [data, setData] = useState<PageResponse<Product> | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Debounce timer refs
  const searchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const priceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Sync search input when URL changes externally
  useEffect(() => {
    setSearchInput(keyword);
  }, [keyword]);

  useEffect(() => {
    setMinPriceInput(minPrice);
  }, [minPrice]);

  useEffect(() => {
    setMaxPriceInput(maxPrice);
  }, [maxPrice]);

  // Build new URL from params
  const buildUrl = useCallback(
    (overrides: Record<string, string | undefined>) => {
      const params = new URLSearchParams();
      const merged: Record<string, string> = {
        keyword,
        category,
        minPrice,
        maxPrice,
        sortBy,
        sortDir,
        page: String(page),
        ...overrides,
      };
      for (const [k, v] of Object.entries(merged)) {
        if (v && v !== '0' && !(k === 'page' && v === '0')) {
          // Keep page=0 out of URL (it's the default)
          if (k === 'page' && v === '0') continue;
          if (k === 'sortBy' && v === 'createdAt' && merged.sortDir === 'desc') continue;
          if (k === 'sortDir' && v === 'desc' && merged.sortBy === 'createdAt') continue;
          params.set(k, v);
        }
      }
      const qs = params.toString();
      return `/products${qs ? `?${qs}` : ''}`;
    },
    [keyword, category, minPrice, maxPrice, sortBy, sortDir, page],
  );

  // Navigate with new params (resets page to 0 unless explicitly set)
  const updateFilters = useCallback(
    (overrides: Record<string, string | undefined>) => {
      // Reset to page 0 when filter changes (unless page is explicitly set)
      if (!('page' in overrides)) {
        overrides.page = '0';
      }
      router.push(buildUrl(overrides));
    },
    [router, buildUrl],
  );

  // Debounced search input handler
  const handleSearchChange = useCallback(
    (value: string) => {
      setSearchInput(value);
      if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
      searchTimerRef.current = setTimeout(() => {
        updateFilters({ keyword: value || undefined });
      }, 300);
    },
    [updateFilters],
  );

  // Debounced price input handlers
  const handleMinPriceChange = useCallback(
    (value: string) => {
      setMinPriceInput(value);
      if (priceTimerRef.current) clearTimeout(priceTimerRef.current);
      priceTimerRef.current = setTimeout(() => {
        updateFilters({ minPrice: value || undefined });
      }, 300);
    },
    [updateFilters],
  );

  const handleMaxPriceChange = useCallback(
    (value: string) => {
      setMaxPriceInput(value);
      if (priceTimerRef.current) clearTimeout(priceTimerRef.current);
      priceTimerRef.current = setTimeout(() => {
        updateFilters({ maxPrice: value || undefined });
      }, 300);
    },
    [updateFilters],
  );

  // Cleanup timers
  useEffect(() => {
    return () => {
      if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
      if (priceTimerRef.current) clearTimeout(priceTimerRef.current);
    };
  }, []);

  // Fetch products when URL params change
  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);

    const params: Record<string, unknown> = {
      page,
      size: PAGE_SIZE,
      sortBy,
      sortDir,
    };
    if (keyword) params.keyword = keyword;
    if (category) params.category = category;
    if (minPrice) params.minPrice = Number(minPrice);
    if (maxPrice) params.maxPrice = Number(maxPrice);

    searchProducts(params as Parameters<typeof searchProducts>[0])
      .then((result) => {
        if (!cancelled) {
          setData(result);
          setIsLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setData(null);
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [keyword, category, minPrice, maxPrice, sortBy, sortDir, page]);

  // Active filter chips
  const activeFilters: { key: string; label: string }[] = [];
  if (keyword) activeFilters.push({ key: 'keyword', label: `Search: ${keyword}` });
  if (category) activeFilters.push({ key: 'category', label: `Category: ${category}` });
  if (minPrice) activeFilters.push({ key: 'minPrice', label: `Min: $${minPrice}` });
  if (maxPrice) activeFilters.push({ key: 'maxPrice', label: `Max: $${maxPrice}` });

  const removeFilter = (key: string) => {
    updateFilters({ [key]: undefined });
  };

  const currentSortKey = sortKey(sortBy, sortDir);

  return (
    <main className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Products</h1>

      {/* Filters */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* Search */}
        <div>
          <label htmlFor="search" className="block text-sm font-medium mb-1">
            Search
          </label>
          <input
            id="search"
            type="text"
            placeholder="Search products..."
            value={searchInput}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
          />
        </div>

        {/* Category */}
        <div>
          <label htmlFor="category" className="block text-sm font-medium mb-1">
            Category
          </label>
          <select
            id="category"
            value={category}
            onChange={(e) => updateFilters({ category: e.target.value || undefined })}
            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent bg-transparent"
          >
            <option value="">All Categories</option>
            {CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>

        {/* Price Range */}
        <div className="flex gap-2">
          <div className="flex-1">
            <label htmlFor="minPrice" className="block text-sm font-medium mb-1">
              Min Price
            </label>
            <input
              id="minPrice"
              type="number"
              min="0"
              placeholder="$0"
              value={minPriceInput}
              onChange={(e) => handleMinPriceChange(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
          <div className="flex-1">
            <label htmlFor="maxPrice" className="block text-sm font-medium mb-1">
              Max Price
            </label>
            <input
              id="maxPrice"
              type="number"
              min="0"
              placeholder="$999"
              value={maxPriceInput}
              onChange={(e) => handleMaxPriceChange(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
        </div>

        {/* Sort */}
        <div>
          <label htmlFor="sort" className="block text-sm font-medium mb-1">
            Sort By
          </label>
          <select
            id="sort"
            value={currentSortKey}
            onChange={(e) => {
              const opt = SORT_OPTIONS.find(
                (o) => sortKey(o.sortBy, o.sortDir) === e.target.value,
              );
              if (opt) updateFilters({ sortBy: opt.sortBy, sortDir: opt.sortDir });
            }}
            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent bg-transparent"
          >
            {SORT_OPTIONS.map((opt) => (
              <option key={sortKey(opt.sortBy, opt.sortDir)} value={sortKey(opt.sortBy, opt.sortDir)}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Filter Chips */}
      {activeFilters.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-6" data-testid="filter-chips">
          {activeFilters.map((f) => (
            <button
              key={f.key}
              onClick={() => removeFilter(f.key)}
              className="inline-flex items-center gap-1 text-sm px-3 py-1 rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors"
              aria-label={`Remove ${f.label} filter`}
            >
              {f.label}
              <span aria-hidden="true">&times;</span>
            </button>
          ))}
        </div>
      )}

      {/* Results */}
      {isLoading ? (
        <LoadingSkeleton count={PAGE_SIZE} />
      ) : data && data.content.length > 0 ? (
        <>
          <p className="text-sm text-[var(--muted)] mb-4">
            {data.totalElements} product{data.totalElements !== 1 ? 's' : ''} found
          </p>
          <ProductGrid products={data.content} />
          <div className="mt-8">
            <Pagination
              currentPage={data.number}
              totalPages={data.totalPages}
              onPageChange={(p) => updateFilters({ page: String(p) })}
            />
          </div>
        </>
      ) : (
        <div className="text-center py-16" data-testid="empty-state">
          <p className="text-lg font-medium text-[var(--muted)] mb-2">No products found</p>
          <p className="text-sm text-[var(--muted)]">
            Try adjusting your search or filters.
          </p>
        </div>
      )}
    </main>
  );
}
