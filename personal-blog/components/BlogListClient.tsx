'use client';

import React, { useMemo } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import type { Post } from '@/lib/types';
import { filterPosts } from '@/components/SearchBar';
import SearchBar from '@/components/SearchBar';
import PostCard from '@/components/PostCard';
import Pagination from '@/components/Pagination';

const POSTS_PER_PAGE = 10;

interface BlogListClientProps {
  posts: Post[];
  categories: string[];
  allTags: string[];
}

export default function BlogListClient({ posts, categories, allTags }: BlogListClientProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const q = searchParams.get('q') ?? '';
  const selectedCategory = searchParams.get('category') ?? '';
  const selectedTag = searchParams.get('tag') ?? '';
  const rawPage = parseInt(searchParams.get('page') ?? '1', 10);

  const filtered: Post[] = useMemo(() => {
    const qFiltered = filterPosts(posts, q);
    const qSlugs = new Set(qFiltered.map((p) => p.slug));
    let result = posts.filter((p) => qSlugs.has(p.slug));
    if (selectedCategory) {
      result = result.filter((p) => p.category === selectedCategory);
    }
    if (selectedTag) {
      result = result.filter((p) => p.tags.includes(selectedTag));
    }
    return result;
  }, [posts, q, selectedCategory, selectedTag]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / POSTS_PER_PAGE));
  const currentPage = Math.max(1, Math.min(rawPage, totalPages));
  const paginatedPosts = filtered.slice(
    (currentPage - 1) * POSTS_PER_PAGE,
    currentPage * POSTS_PER_PAGE
  );

  const setParam = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    params.delete('page');
    router.replace(`?${params.toString()}`);
  };

  const handlePageChange = (newPage: number) => {
    const params = new URLSearchParams(searchParams.toString());
    if (newPage === 1) {
      params.delete('page');
    } else {
      params.set('page', String(newPage));
    }
    router.replace(`?${params.toString()}`);
  };

  return (
    <div>
      <SearchBar posts={posts} />

      <div
        style={{
          display: 'flex',
          gap: '0.75rem',
          margin: '1rem 0',
          flexWrap: 'wrap',
        }}
      >
        <select
          aria-label="카테고리 필터"
          value={selectedCategory}
          onChange={(e) => setParam('category', e.target.value)}
        >
          <option value="">모든 카테고리</option>
          {categories.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>

        <select
          aria-label="태그 필터"
          value={selectedTag}
          onChange={(e) => setParam('tag', e.target.value)}
        >
          <option value="">모든 태그</option>
          {allTags.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>

      <p data-testid="filtered-count">{filtered.length}개 게시물</p>

      {paginatedPosts.length === 0 ? (
        <p>검색 결과가 없습니다.</p>
      ) : (
        paginatedPosts.map((post) => <PostCard key={post.slug} post={post} />)
      )}

      <Pagination
        totalItems={filtered.length}
        itemsPerPage={POSTS_PER_PAGE}
        currentPage={currentPage}
        onPageChange={handlePageChange}
      />
    </div>
  );
}
