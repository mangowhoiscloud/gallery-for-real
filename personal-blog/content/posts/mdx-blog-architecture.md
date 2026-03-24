---
title: "MDX 기반 블로그 아키텍처 설계"
date: "2026-02-20"
category: "개발"
tags: ["MDX", "Architecture", "블로그", "Next.js", "gray-matter"]
slug: "mdx-blog-architecture"
original_url: "https://example.tistory.com/mdx-blog-architecture"
---

# MDX 기반 블로그 아키텍처 설계

MDX는 Markdown에 JSX를 결합한 포맷입니다. 블로그 콘텐츠를 MDX로 관리하면 일반 마크다운의 단순함과 React 컴포넌트의 강력함을 동시에 활용할 수 있습니다.

## 아키텍처 개요

```
content/
└── posts/
    ├── my-post.md       # gray-matter 파싱
    └── interactive.mdx  # MDX 컴포넌트 포함

lib/
├── posts.ts             # 파일 시스템 접근
├── markdown.ts          # 유틸리티 함수
├── shiki.ts             # 코드 하이라이팅
└── validation.ts        # 빌드 시 검증

app/
└── blog/
    └── [slug]/
        └── page.tsx     # MDXRemote 렌더링
```

## gray-matter로 프론트매터 파싱

```typescript
import matter from 'gray-matter';
import { readFile } from 'fs/promises';
import path from 'path';

const POSTS_DIR = path.join(process.cwd(), 'content', 'posts');

export interface PostMeta {
  title: string;
  date: string;
  category: string;
  tags: string[];
  slug: string;
  original_url?: string;
}

export interface Post extends PostMeta {
  content: string;
}

export async function getPostBySlug(slug: string): Promise<Post | null> {
  try {
    const filePath = path.join(POSTS_DIR, `${slug}.md`);
    const raw = await readFile(filePath, 'utf-8');
    const { data, content } = matter(raw);

    return {
      title: data.title,
      date: data.date,
      category: data.category,
      tags: data.tags ?? [],
      slug,
      original_url: data.original_url,
      content,
    };
  } catch {
    return null;
  }
}
```

## next-mdx-remote로 렌더링

`next-mdx-remote`는 Next.js의 서버 컴포넌트와 완벽하게 통합됩니다.

```typescript
import { MDXRemote } from 'next-mdx-remote/rsc';
import type { MDXRemoteProps } from 'next-mdx-remote/rsc';

const mdxOptions: MDXRemoteProps['options'] = {
  mdxOptions: {
    rehypePlugins: [
      [rehypeShiki, { theme: 'github-dark' }],
    ],
    remarkPlugins: [remarkGfm],
  },
};

export default async function PostPage({ params }: { params: { slug: string } }) {
  const post = await getPostBySlug(params.slug);

  if (!post) notFound();

  return (
    <article className="prose max-w-2xl mx-auto">
      <h1>{post.title}</h1>
      <MDXRemote source={post.content} options={mdxOptions} />
    </article>
  );
}
```

## Shiki 코드 하이라이팅

Shiki는 VSCode와 동일한 문법 강조를 제공합니다.

```typescript
import { createHighlighter } from 'shiki';
import type { Plugin } from 'unified';
import type { Root } from 'hast';

let highlighterPromise: ReturnType<typeof createHighlighter> | null = null;

async function getHighlighter() {
  if (!highlighterPromise) {
    highlighterPromise = createHighlighter({
      themes: ['github-light', 'github-dark'],
      langs: ['typescript', 'javascript', 'bash', 'css', 'json', 'markdown'],
    });
  }
  return highlighterPromise;
}

export const rehypeShikiPlugin: Plugin<[], Root> = () => {
  return async (tree) => {
    const highlighter = await getHighlighter();
    // 코드 블록 변환 로직...
  };
};
```

## 빌드 시 검증

콘텐츠 유효성 검사를 빌드 시 수행하여 잘못된 포스트가 배포되지 않도록 합니다.

```typescript
export function validatePost(data: unknown, filename: string): string[] {
  const errors: string[] = [];
  const required = ['title', 'date', 'slug', 'category'];

  for (const field of required) {
    if (!data || typeof data !== 'object' || !(field in data)) {
      errors.push(`${filename}: 필수 필드 '${field}' 누락`);
    }
  }

  // ISO 날짜 형식 검사
  if (data && typeof data === 'object' && 'date' in data) {
    const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
    if (!dateRegex.test(String((data as { date: unknown }).date))) {
      errors.push(`${filename}: 날짜 형식이 올바르지 않음 (YYYY-MM-DD 필요)`);
    }
  }

  return errors;
}
```

## 성능 고려사항

### 정적 생성

모든 블로그 포스트를 빌드 시 정적으로 생성합니다.

```typescript
export async function generateStaticParams() {
  const slugs = await getPostSlugs();
  return slugs.map((slug) => ({ slug }));
}

// Next.js 15에서 기본값은 static
export const dynamic = 'force-static';
```

### 하이라이터 캐싱

Shiki 하이라이터 인스턴스를 싱글톤으로 관리하여 초기화 비용을 절약합니다.

## 결론

MDX 기반 블로그 아키텍처의 핵심은 **콘텐츠와 코드의 분리**입니다. `content/` 디렉토리의 마크다운 파일은 순수 콘텐츠로 유지하고, `lib/` 모듈이 파싱과 변환을 담당합니다. 이 구조로 콘텐츠 작성자와 개발자 모두 최적의 경험을 누릴 수 있습니다.
