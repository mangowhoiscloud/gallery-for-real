'use client';

import React, { useState, useRef, useMemo, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import type { PostMeta } from '@/lib/types';

interface SearchBarProps {
  posts: PostMeta[];
  onFilter?: (filtered: PostMeta[]) => void;
}

function filterPosts(posts: PostMeta[], query: string): PostMeta[] {
  const lower = query.toLowerCase().trim();
  if (!lower) return posts;
  return posts.filter(
    (post) =>
      post.title.toLowerCase().includes(lower) ||
      post.category.toLowerCase().includes(lower) ||
      post.tags.some((tag) => tag.toLowerCase().includes(lower))
  );
}

export { filterPosts };

export default function SearchBar({ posts, onFilter }: SearchBarProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [query, setQuery] = useState(() => searchParams.get('q') ?? '');
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const filtered = useMemo(() => filterPosts(posts, query), [posts, query]);

  useEffect(() => {
    onFilter?.(filtered);
  }, [filtered, onFilter]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      const params = new URLSearchParams(searchParams.toString());
      if (val.trim()) {
        params.set('q', val);
      } else {
        params.delete('q');
      }
      router.replace(`?${params.toString()}`);
    }, 300);
  };

  return (
    <div>
      <input
        type="search"
        placeholder="검색..."
        value={query}
        onChange={handleChange}
        aria-label="검색"
      />
      <span data-testid="results-count">{filtered.length}개 결과</span>
    </div>
  );
}
