---
title: "Next.js 15 App Router 완전 가이드"
date: "2026-01-10"
category: "개발"
tags: ["Next.js", "React", "TypeScript", "App Router"]
slug: "nextjs-app-router-guide"
original_url: "https://example.tistory.com/nextjs-app-router"
---

# Next.js 15 App Router 완전 가이드

Next.js 15의 App Router는 React Server Components를 기반으로 한 새로운 라우팅 시스템입니다. 이 가이드에서는 App Router의 핵심 개념과 실제 사용법을 살펴보겠습니다.

## 주요 변경사항

App Router에서는 파일 시스템 기반 라우팅이 더욱 강력해졌습니다. `app/` 디렉토리 내의 모든 컴포넌트는 기본적으로 Server Component로 동작합니다.

### 파일 구조

```
app/
├── layout.tsx        # 루트 레이아웃
├── page.tsx          # 홈 페이지
├── loading.tsx       # 로딩 UI
├── error.tsx         # 에러 UI
├── not-found.tsx     # 404 페이지
└── blog/
    ├── page.tsx      # 블로그 목록
    └── [slug]/
        └── page.tsx  # 블로그 상세
```

## Server Components vs Client Components

Server Components는 서버에서 렌더링되며 클라이언트로 HTML을 전송합니다. 반면 Client Components는 `'use client'` 지시어를 사용합니다.

```typescript
// Server Component (기본값)
async function BlogPost({ slug }: { slug: string }) {
  const post = await getPost(slug); // 직접 DB 접근 가능
  return <article>{post.content}</article>;
}

// Client Component
'use client';
function ThemeToggle() {
  const [dark, setDark] = useState(false);
  return <button onClick={() => setDark(!dark)}>테마 전환</button>;
}
```

## 데이터 페칭

App Router에서는 `fetch`를 확장하여 캐싱과 재검증을 지원합니다.

```typescript
// 정적 데이터 (빌드 시 캐시)
const data = await fetch('/api/posts', { cache: 'force-cache' });

// 동적 데이터 (매 요청마다)
const data = await fetch('/api/posts', { cache: 'no-store' });

// 주기적 재검증 (ISR)
const data = await fetch('/api/posts', {
  next: { revalidate: 3600 }
});
```

## generateStaticParams

정적 생성(SSG)을 위해 `generateStaticParams`를 사용합니다.

```typescript
export async function generateStaticParams() {
  const posts = await getAllPosts();
  return posts.map((post) => ({
    slug: post.slug,
  }));
}
```

## 성능 비교

| 방식 | 초기 로드 | SEO | 데이터 신선도 |
|------|-----------|-----|--------------|
| SSG | 빠름 | 좋음 | 빌드 시점 |
| SSR | 보통 | 좋음 | 매 요청 |
| ISR | 빠름 | 좋음 | 주기적 |
| CSR | 느림 | 나쁨 | 실시간 |

## 결론

App Router는 성능과 DX(개발자 경험) 모두를 개선한 강력한 기능입니다. Server Components를 적극 활용하여 번들 크기를 줄이고 초기 로드 성능을 최적화하세요.
