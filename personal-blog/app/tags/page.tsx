import Link from 'next/link';
import type { Metadata } from 'next';
import { getAllTags } from '@/lib/posts';

export const metadata: Metadata = {
  title: '태그',
  description: '블로그의 모든 태그 목록입니다.',
  openGraph: {
    title: '태그',
    description: '블로그의 모든 태그 목록입니다.',
    type: 'website',
    url: '/tags',
  },
};

export default async function TagsPage() {
  const tags = await getAllTags();
  const sortedTags = Object.entries(tags).sort(([, a], [, b]) => b - a);

  return (
    <main style={{ maxWidth: '800px', margin: '0 auto', padding: '2rem 1rem' }}>
      <h1 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '1.5rem' }}>태그</h1>
      <ul
        style={{
          listStyle: 'none',
          padding: 0,
          display: 'flex',
          flexWrap: 'wrap',
          gap: '0.75rem',
        }}
      >
        {sortedTags.map(([tag, count]) => (
          <li key={tag}>
            <Link
              href={`/blog?tag=${encodeURIComponent(tag)}`}
              style={{
                display: 'inline-block',
                padding: '0.25rem 0.75rem',
                background: 'var(--code-bg)',
                borderRadius: '9999px',
                color: 'var(--text-muted)',
                textDecoration: 'none',
                fontSize: '0.875rem',
              }}
            >
              {tag} ({count})
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
