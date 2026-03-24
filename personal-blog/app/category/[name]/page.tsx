import { notFound } from 'next/navigation';
import type { Metadata } from 'next';
import { getAllPosts, getPostBySlug, getCategories } from '@/lib/posts';
import PostCard from '@/components/PostCard';
import type { Post } from '@/lib/types';

type Props = { params: Promise<{ name: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { name } = await params;
  const categoryName = decodeURIComponent(name);
  const allMeta = await getAllPosts();
  const count = allMeta.filter((p) => p.category === categoryName).length;
  const description = `${categoryName} 카테고리의 게시물 ${count}개`;

  return {
    title: categoryName,
    description,
    openGraph: {
      title: `${categoryName} | 카테고리`,
      description,
      type: 'website',
      url: `/category/${name}`,
    },
  };
}

export async function generateStaticParams() {
  const categories = await getCategories();
  return Object.keys(categories).map((name) => ({ name: encodeURIComponent(name) }));
}

export default async function CategoryPage({ params }: Props) {
  const { name } = await params;
  const categoryName = decodeURIComponent(name);

  const allMeta = await getAllPosts();
  const categoryMeta = allMeta.filter((p) => p.category === categoryName);

  if (categoryMeta.length === 0) {
    notFound();
  }

  const postsRaw = await Promise.all(categoryMeta.map((m) => getPostBySlug(m.slug)));
  const posts = postsRaw.filter((p): p is Post => p !== null);

  return (
    <main style={{ maxWidth: '800px', margin: '0 auto', padding: '2rem 1rem' }}>
      <h1 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem' }}>
        {categoryName}
      </h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: '2rem', fontSize: '0.875rem' }}>
        {posts.length}개의 게시물
      </p>
      {posts.map((post) => (
        <PostCard key={post.slug} post={post} />
      ))}
    </main>
  );
}
