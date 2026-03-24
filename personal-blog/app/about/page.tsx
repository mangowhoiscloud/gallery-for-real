import fs from 'fs';
import path from 'path';
import type { Metadata } from 'next';
import matter from 'gray-matter';
import { MDXRemote } from 'next-mdx-remote/rsc';
import CodeBlock from '@/components/CodeBlock';

export const metadata: Metadata = {
  title: '소개',
  description: '블로그 작성자 소개 페이지입니다.',
  openGraph: {
    title: '소개',
    description: '블로그 작성자 소개 페이지입니다.',
    type: 'website',
    url: '/about',
  },
};

export default async function AboutPage() {
  const aboutPath = path.join(process.cwd(), 'content/about.md');
  let content: string;

  try {
    const fileContent = await fs.promises.readFile(aboutPath, 'utf-8');
    const parsed = matter(fileContent);
    content = parsed.content;
  } catch {
    content = '소개 페이지 콘텐츠를 불러올 수 없습니다.';
  }

  return (
    <main style={{ maxWidth: '800px', margin: '0 auto', padding: '2rem 1rem' }}>
      <div className="prose">
        <MDXRemote source={content} components={{ pre: CodeBlock }} />
      </div>
    </main>
  );
}
