import { notFound } from 'next/navigation';
import Link from 'next/link';
import type { Metadata } from 'next';
import { MDXRemote } from 'next-mdx-remote/rsc';
import { getAllPosts, getPostBySlug } from '@/lib/posts';
import { extractHeadings, calculateReadingTime, generateExcerpt } from '@/lib/markdown';
import { rehypeShiki } from '@/lib/shiki';
import TableOfContents from '@/components/TableOfContents';
import CodeBlock from '@/components/CodeBlock';

type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const post = await getPostBySlug(slug);
  if (!post) return { title: '게시물을 찾을 수 없습니다' };

  const description = generateExcerpt(post.content, 160);
  return {
    title: post.title,
    description,
    openGraph: {
      title: post.title,
      description,
      type: 'article',
      url: `/blog/${slug}`,
      publishedTime: `${post.date}T00:00:00Z`,
      tags: post.tags,
    },
  };
}

export async function generateStaticParams() {
  const posts = await getAllPosts();
  return posts.map((post) => ({ slug: post.slug }));
}

function formatDate(dateStr: string): string {
  const [year, month, day] = dateStr.split('-');
  return `${year}년 ${parseInt(month, 10)}월 ${parseInt(day, 10)}일`;
}

export default async function PostPage({ params }: Props) {
  const { slug } = await params;
  const post = await getPostBySlug(slug);
  if (!post) notFound();

  const allPosts = await getAllPosts();
  const currentIndex = allPosts.findIndex((p) => p.slug === post.slug);
  // allPosts sorted newest first → prevPost = older (higher index), nextPost = newer (lower index)
  const prevPost = currentIndex < allPosts.length - 1 ? allPosts[currentIndex + 1] : null;
  const nextPost = currentIndex > 0 ? allPosts[currentIndex - 1] : null;

  const headings = extractHeadings(post.content);
  const readingTime = calculateReadingTime(post.content);

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '2rem 1rem' }}>
      <div style={{ display: 'flex', gap: '3rem', alignItems: 'flex-start' }}>
        <article style={{ flex: 1, minWidth: 0 }}>
          <header style={{ marginBottom: '2rem' }}>
            <h1
              style={{
                fontSize: '1.875rem',
                fontWeight: 700,
                lineHeight: 1.3,
                marginBottom: '1rem',
              }}
            >
              {post.title}
            </h1>

            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '0.75rem',
                fontSize: '0.875rem',
                color: 'var(--text-muted)',
                marginBottom: '0.75rem',
              }}
            >
              <time dateTime={post.date}>{formatDate(post.date)}</time>
              <Link
                href={`/category/${encodeURIComponent(post.category)}`}
                style={{ color: 'var(--accent)', textDecoration: 'none' }}
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

            {post.original_url && (
              <a
                href={post.original_url}
                target="_blank"
                rel="noopener noreferrer"
                style={{ fontSize: '0.875rem', color: 'var(--accent)' }}
              >
                원문 Tistory에서 보기
              </a>
            )}
          </header>

          <div className="prose">
            <MDXRemote
              source={post.content}
              options={{ mdxOptions: { rehypePlugins: [rehypeShiki] } }}
              components={{ pre: CodeBlock }}
            />
          </div>

          <nav
            aria-label="이전/다음 글"
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              marginTop: '3rem',
              paddingTop: '2rem',
              borderTop: '1px solid var(--border)',
            }}
          >
            <div>
              {prevPost && (
                <Link
                  href={`/blog/${prevPost.slug}`}
                  style={{ color: 'var(--accent)', textDecoration: 'none' }}
                >
                  ← 이전 글: {prevPost.title}
                </Link>
              )}
            </div>
            <div>
              {nextPost && (
                <Link
                  href={`/blog/${nextPost.slug}`}
                  style={{ color: 'var(--accent)', textDecoration: 'none' }}
                >
                  다음 글: {nextPost.title} →
                </Link>
              )}
            </div>
          </nav>
        </article>

        <aside style={{ width: '260px', flexShrink: 0 }}>
          <TableOfContents headings={headings} />
        </aside>
      </div>
    </div>
  );
}
