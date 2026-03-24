import { Feed } from 'feed';
import { getAllPosts } from '@/lib/posts';

export async function GET() {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000';
  const posts = await getAllPosts();

  const feed = new Feed({
    id: baseUrl,
    title: '개발 블로그',
    description: '개발, 디자인, 회고에 관한 이야기를 나눕니다.',
    link: baseUrl,
    language: 'ko',
    copyright: `© ${new Date().getFullYear()} 개발 블로그`,
    author: {
      name: '블로그 작성자',
      link: baseUrl,
    },
    feedLinks: {
      rss2: `${baseUrl}/feed.xml`,
    },
  });

  for (const post of posts) {
    const postUrl = `${baseUrl}/blog/${post.slug}`;
    feed.addItem({
      id: postUrl,
      title: post.title,
      link: postUrl,
      date: new Date(post.date),
      description: post.title,
      category: [{ name: post.category }],
      author: [{ name: '블로그 작성자', link: baseUrl }],
    });
  }

  return new Response(feed.rss2(), {
    headers: {
      'Content-Type': 'application/rss+xml; charset=utf-8',
      'Cache-Control': 'public, max-age=3600',
    },
  });
}
