import { Suspense } from 'react';
import type { Metadata } from 'next';
import { getAllPosts, getPostBySlug, getCategories, getAllTags } from '@/lib/posts';
import type { Post } from '@/lib/types';
import BlogListClient from '@/components/BlogListClient';

export const metadata: Metadata = {
  title: '블로그',
  description: '개발, 디자인, 회고에 대한 모든 게시물을 볼 수 있습니다.',
  openGraph: {
    title: '블로그',
    description: '개발, 디자인, 회고에 대한 모든 게시물을 볼 수 있습니다.',
    type: 'website',
    url: '/blog',
  },
};

export default async function BlogPage() {
  const allMeta = await getAllPosts();
  const postsRaw = await Promise.all(allMeta.map((m) => getPostBySlug(m.slug)));
  const posts = postsRaw.filter((p): p is Post => p !== null);
  const categoryCounts = await getCategories();
  const tagCounts = await getAllTags();
  const categories = Object.keys(categoryCounts);
  const allTags = Object.keys(tagCounts);

  return (
    <main style={{ maxWidth: '800px', margin: '0 auto', padding: '2rem 1rem' }}>
      <h1 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '1.5rem' }}>블로그</h1>
      <Suspense fallback={<p>로딩 중...</p>}>
        <BlogListClient posts={posts} categories={categories} allTags={allTags} />
      </Suspense>
    </main>
  );
}
