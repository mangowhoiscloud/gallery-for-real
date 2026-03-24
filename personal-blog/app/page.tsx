import Link from 'next/link';
import type { Metadata } from 'next';
import { getAllPosts, getPostBySlug, getCategories } from '@/lib/posts';
import PostCard from '@/components/PostCard';
import type { Post } from '@/lib/types';

export const metadata: Metadata = {
  title: { absolute: '개발 블로그' },
  description: '개발 경험과 기술 인사이트를 공유하는 블로그입니다.',
  openGraph: {
    title: '개발 블로그',
    description: '개발 경험과 기술 인사이트를 공유하는 블로그입니다.',
    type: 'website',
    url: '/',
  },
};

export default async function Home() {
  const allPosts = await getAllPosts();
  const recentMeta = allPosts.slice(0, 5);
  const recentPostsRaw = await Promise.all(
    recentMeta.map((meta) => getPostBySlug(meta.slug))
  );
  const recentPosts = recentPostsRaw.filter((p): p is Post => p !== null);
  const categories = await getCategories();

  return (
    <main style={{ maxWidth: '800px', margin: '0 auto', padding: '2rem 1rem' }}>
      <section
        aria-label="소개"
        style={{
          marginBottom: '3rem',
          padding: '1.5rem',
          background: 'var(--code-bg)',
          borderRadius: '0.5rem',
        }}
      >
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.75rem' }}>
          개발 블로그
        </h1>
        <p style={{ color: 'var(--text-muted)', lineHeight: 1.7, margin: 0 }}>
          프론트엔드를 중심으로 풀스택 개발을 탐구하는 공간입니다. Next.js, TypeScript,
          React 등 현대 웹 개발 기술에 대한 이야기를 나눕니다.
        </p>
      </section>

      <section aria-label="최근 게시물">
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1rem' }}>
          최근 게시물
        </h2>
        {recentPosts.map((post) => (
          <PostCard key={post.slug} post={post} />
        ))}
      </section>

      <aside
        aria-label="카테고리"
        style={{ marginTop: '3rem' }}
      >
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1rem' }}>
          카테고리
        </h2>
        <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
          {Object.entries(categories).map(([name, count]) => (
            <li key={name}>
              <Link
                href={`/category/${encodeURIComponent(name)}`}
                style={{ color: 'var(--accent)', textDecoration: 'none' }}
              >
                {name} ({count})
              </Link>
            </li>
          ))}
        </ul>
      </aside>
    </main>
  );
}
