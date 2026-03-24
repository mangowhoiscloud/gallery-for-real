'use client';

import React from 'react';

interface PaginationProps {
  totalItems: number;
  itemsPerPage?: number;
  currentPage: number;
  onPageChange: (page: number) => void;
}

export default function Pagination({
  totalItems,
  itemsPerPage = 10,
  currentPage,
  onPageChange,
}: PaginationProps) {
  const totalPages = itemsPerPage > 0 ? Math.ceil(totalItems / itemsPerPage) : 0;

  if (totalPages <= 0) {
    return (
      <nav aria-label="Pagination">
        <button aria-label="Previous" disabled>이전</button>
        <button aria-label="Next" disabled>다음</button>
      </nav>
    );
  }

  const pages = Array.from({ length: totalPages }, (_, i) => i + 1);

  return (
    <nav aria-label="Pagination">
      <button
        aria-label="Previous"
        onClick={() => {
          if (currentPage > 1) onPageChange(currentPage - 1);
        }}
        disabled={currentPage <= 1}
      >
        이전
      </button>

      {pages.map((page) => (
        <button
          key={page}
          aria-label={String(page)}
          aria-current={page === currentPage ? 'page' : undefined}
          onClick={() => onPageChange(page)}
        >
          {page}
        </button>
      ))}

      <button
        aria-label="Next"
        onClick={() => {
          if (currentPage < totalPages) onPageChange(currentPage + 1);
        }}
        disabled={currentPage >= totalPages}
      >
        다음
      </button>
    </nav>
  );
}
