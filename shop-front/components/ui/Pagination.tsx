'use client';

interface PaginationProps {
  /** 0-indexed current page, matching Spring Boot PageResponse.number */
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

function getPageNumbers(currentPage: number, totalPages: number): (number | '...')[] {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, i) => i);
  }

  const pages: (number | '...')[] = [0];

  const left = Math.max(1, currentPage - 1);
  const right = Math.min(totalPages - 2, currentPage + 1);

  if (left > 1) pages.push('...');
  for (let i = left; i <= right; i++) pages.push(i);
  if (right < totalPages - 2) pages.push('...');

  pages.push(totalPages - 1);
  return pages;
}

export default function Pagination({ currentPage, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null;

  const pages = getPageNumbers(currentPage, totalPages);

  return (
    <nav aria-label="Pagination" className="flex items-center justify-center gap-1 flex-wrap">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 0}
        aria-label="Previous page"
        className="px-3 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-100 dark:hover:bg-gray-800"
      >
        Previous
      </button>

      {pages.map((page, idx) =>
        page === '...' ? (
          <span
            key={`ellipsis-${idx}`}
            className="px-3 py-2 text-sm text-[var(--muted)]"
            aria-hidden
          >
            &hellip;
          </span>
        ) : (
          <button
            key={page}
            onClick={() => onPageChange(page)}
            aria-label={`Page ${page + 1}`}
            aria-current={page === currentPage ? 'page' : undefined}
            className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              page === currentPage
                ? 'bg-blue-600 text-white'
                : 'hover:bg-gray-100 dark:hover:bg-gray-800'
            }`}
          >
            {page + 1}
          </button>
        ),
      )}

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages - 1}
        aria-label="Next page"
        className="px-3 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-100 dark:hover:bg-gray-800"
      >
        Next
      </button>
    </nav>
  );
}
