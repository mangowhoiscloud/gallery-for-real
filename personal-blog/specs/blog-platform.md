# Personal Blog Platform

## Overview
Tistory에서 마이그레이션한 Markdown 글을 소비하는 개인 블로그.
Next.js 15 App Router 기반, MDX 지원, 정적 생성(SSG) 우선.
깔끔하고 읽기 좋은 기술 블로그 스타일 (참고: Dan Abramov's overreacted.io, Lee Robinson's leerob.io).

## Tech Stack
- Next.js 15 (App Router, SSG with `generateStaticParams`)
- TypeScript
- Tailwind CSS 4
- MDX (`next-mdx-remote` or `@next/mdx`)
- gray-matter (frontmatter 파싱)
- Vercel deployment target

## 콘텐츠 구조
`tistory-migrator`가 생성한 출력물을 `content/` 디렉토리에 배치:
```
content/
├── posts/
│   ├── 2024-01-15-post-title.md
│   └── 2024-01-20-another-post.md
└── images/
    ├── post-title/
    │   └── image1.jpg
    └── another-post/
        └── screenshot.png
```

Frontmatter 형식:
```yaml
---
title: "글 제목"
date: "2024-01-15"
category: "개발"
tags: ["JavaScript", "React"]
slug: "post-title"
original_url: "https://xxx.tistory.com/123"
---
```

## Pages & Routes

### 1. Home `/`
- 최근 글 목록 (최신순, 5~10개)
- 간단한 자기소개 섹션
- 카테고리별 글 수 표시

### 2. Blog List `/blog`
- 전체 글 목록 (최신순)
- 카테고리 필터 (사이드바 또는 탭)
- 태그 필터 (클릭 가능한 태그 클라우드)
- 날짜별 그룹핑 옵션
- 페이지네이션 (10개씩)
- 검색 (제목 + 본문 텍스트 매칭, 클라이언트 사이드)

### 3. Post Detail `/blog/[slug]`
- Markdown 렌더링 (코드 하이라이팅 포함)
- 목차 (TOC) 자동 생성 (h2, h3 기반)
- 발행일, 카테고리, 태그 표시
- 이전/다음 글 네비게이션
- 원본 Tistory URL 링크 (마이그레이션 출처)
- 예상 읽기 시간 표시

### 4. Category `/category/[name]`
- 해당 카테고리의 글 목록
- 카테고리 설명 (선택)

### 5. Tags `/tags`
- 전체 태그 목록 (사용 빈도순)
- 태그 클릭 → 해당 태그의 글 목록

### 6. About `/about`
- 자기소개 페이지
- 마크다운 파일(`content/about.md`)에서 로드

## Design Requirements

### Visual Direction
- 미니멀 기술 블로그 스타일
- 넉넉한 line-height (1.8~2.0)와 max-width (680px) 본문
- 코드 블록: syntax highlighting (Prism.js 또는 Shiki)
- 다크/라이트 모드 토글
- 부드러운 페이지 전환

### Typography
- 본문: Pretendard 또는 system-ui (한글 최적화)
- 코드: JetBrains Mono 또는 Fira Code
- 제목: 굵고 큰 사이즈, 명확한 위계

### Components
- PostCard: 제목, 날짜, 카테고리, 요약 (첫 150자), 태그
- TOC: 우측 사이드바, 스크롤 추적 하이라이팅
- CodeBlock: 복사 버튼, 언어 표시, 라인 넘버
- SearchBar: 실시간 필터링
- ThemeToggle: 다크/라이트 전환 (localStorage 유지)
- Pagination: 이전/다음 + 페이지 번호

### SEO
- 글별 `<title>`, `<meta description>` (첫 160자)
- Open Graph 태그
- sitemap.xml 자동 생성
- RSS feed (`/feed.xml`)

## 샘플 콘텐츠
빌드/테스트를 위해 `content/posts/`에 3~5개 샘플 마크다운 파일 포함:
- 다양한 마크다운 요소 (코드블록, 이미지, 테이블, 리스트)
- 한글 제목/본문
- 여러 카테고리/태그

## Testing
- 글 로딩/파싱 유틸 테스트
- 컴포넌트 렌더링 테스트 (React Testing Library)
- 빌드 성공 검증 (`next build`)
- 목표: 30개 이상 테스트

## Build & Deploy
```bash
npm run dev      # 로컬 개발 서버
npm run build    # 정적 빌드
npm run test     # 테스트
vercel deploy    # Vercel 배포
```
