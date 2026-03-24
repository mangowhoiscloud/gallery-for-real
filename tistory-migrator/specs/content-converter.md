# Content Converter

## Overview
Tistory HTML 본문을 Markdown + frontmatter 형식으로 변환하고,
이미지를 로컬로 다운로드하여 경로를 교체하는 모듈.

## HTML → Markdown 변환
- 라이브러리: `markdownify` 또는 직접 구현
- 변환 대상:
  - `<h1>`~`<h6>` → `#`~`######`
  - `<p>` → 줄바꿈
  - `<strong>`, `<em>` → `**`, `*`
  - `<a href>` → `[text](url)`
  - `<img src>` → `![alt](local_path)`
  - `<pre><code>` → 코드 블록. **반드시 `class="language-xxx"` 속성에서 언어를 감지**하여 ` ```python`, ` ```bash` 등으로 변환. `class` 속성이 없으면 ` ``` `(언어 없음)으로 처리. 예: `<code class="language-python">` → ` ```python`
  - `<ul>/<ol>/<li>` → 마크다운 리스트
  - `<blockquote>` → `>`
  - `<table>` → 마크다운 테이블
  - `<br>` → 줄바꿈
- Tistory 특수 처리:
  - `[##_Image|filename.jpg|..._##]` 커스텀 태그 → 이미지 마크다운
  - `[##_Code|..._##]` 커스텀 태그 → 코드 블록
  - 빈 `<p>&nbsp;</p>` 제거
  - 연속 빈 줄 2개 이상 → 2개로 정리

## 이미지 다운로드
- Tistory 이미지 URL 패턴: `https://img1.daumcdn.net/thumb/...` 또는 `https://{blog}.tistory.com/image/...`
- 다운로드 디렉토리: `output/images/{post-slug}/`
- 파일명: 원본 파일명 유지, 충돌 시 `-1`, `-2` 접미사
- HTML 내 이미지 경로를 상대경로로 교체: `/images/{post-slug}/filename.jpg`
- 실패 시: 원본 URL 유지 + 경고 로그

## Frontmatter 생성
```yaml
---
title: "글 제목"
date: "2024-01-15"
category: "카테고리명"
tags: ["태그1", "태그2"]
slug: "post-slug-from-title"
original_url: "https://xxx.tistory.com/123"
---
```
- slug: 제목에서 생성 (한글은 음절 유지, 특수문자 제거, 공백→하이픈)
- date: ISO 8601 형식

## 출력 구조
```
output/
├── posts/
│   ├── 2024-06-15-post-title.md       ← 반드시 날짜 접두사 포함
│   ├── 2024-07-20-another-post.md     ← 형식: YYYY-MM-DD-slug.md
│   └── ...
├── images/
│   ├── post-title/
│   │   ├── image1.jpg
│   │   └── image2.png
│   └── another-post/
│       └── screenshot.png
└── metadata.json            # 전체 마이그레이션 요약 (글 수, 카테고리 목록, 태그 목록)
```
- **파일명 규칙**: `{YYYY-MM-DD}-{slug}.md` 형식 필수. published_at에서 날짜를 추출하여 접두사로 사용. 날짜 없이 `slug.md`만 출력하면 안 됨
