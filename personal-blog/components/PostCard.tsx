import Link from 'next/link';
import type { Post } from '@/lib/types';
import { generateExcerpt, calculateReadingTime } from '@/lib/markdown';

interface PostCardProps {
  post: Post;
}

function formatDate(dateStr: string): string {
  const [year, month, day] = dateStr.split('-');
  return `${year}년 ${parseInt(month)}월 ${parseInt(day)}일`;
}

export default function PostCard({ post }: PostCardProps) {
  const excerpt = generateExcerpt(post.content);
  const readingTime = calculateReadingTime(post.content);

  return (
    <article
      style={{
        padding: '1.5rem 0',
        borderBottom: '1px solid var(--border)',
      }}
    >
      <h2
        style={{
          fontSize: '1.25rem',
          fontWeight: 700,
          marginBottom: '0.5rem',
        }}
      >
        <Link
          href={`/blog/${post.slug}`}
          style={{
            color: 'var(--text)',
            textDecoration: 'none',
          }}
        >
          {post.title}
        </Link>
      </h2>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          fontSize: '0.875rem',
          color: 'var(--text-muted)',
          marginBottom: '0.75rem',
          flexWrap: 'wrap',
        }}
      >
        <time dateTime={post.date}>{formatDate(post.date)}</time>
        <Link
          href={`/category/${encodeURIComponent(post.category)}`}
          style={{
            color: 'var(--accent)',
            textDecoration: 'none',
          }}
        >
          {post.category}
        </Link>
        <span>{readingTime}</span>
      </div>

      {post.tags.length > 0 && (
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '0.375rem',
            marginBottom: '0.75rem',
          }}
        >
          {post.tags.map((tag) => (
            <span
              key={tag}
              style={{
                fontSize: '0.8125rem',
                padding: '0.125rem 0.5rem',
                background: 'var(--code-bg)',
                borderRadius: '9999px',
                color: 'var(--text-muted)',
              }}
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      <p
        style={{
          fontSize: '0.9375rem',
          color: 'var(--text-muted)',
          lineHeight: 1.7,
          margin: 0,
        }}
      >
        {excerpt}
      </p>
    </article>
  );
}
