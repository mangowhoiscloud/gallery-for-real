---
title: "2025년 개발자로서의 회고"
date: "2025-12-15"
category: "회고"
tags: ["회고", "2025", "성장", "개발자"]
slug: "2025-year-review"
---

# 2025년 개발자로서의 회고

2025년이 마무리되는 시점에서 올 한 해를 돌아보았습니다. 기술적인 성장과 함께 많은 것을 배웠고, 때로는 실패도 경험했습니다.

## 올해 배운 기술들

### 프론트엔드

올해는 특히 React 19와 Next.js 15의 새로운 기능들을 깊이 공부했습니다. Server Components의 개념을 처음 이해했을 때의 그 "아하!" 모멘트가 아직도 생생합니다.

React 19의 Actions API는 폼 처리를 혁신적으로 간소화해 주었습니다:

```typescript
// React 19 이전
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);

async function handleSubmit(e: FormEvent) {
  e.preventDefault();
  setLoading(true);
  try {
    await submitForm(formData);
  } catch (err) {
    setError('제출 실패');
  } finally {
    setLoading(false);
  }
}

// React 19 Actions
async function submitAction(formData: FormData) {
  'use server';
  await submitForm(formData);
}
```

### 백엔드

Node.js 22의 ESM 지원과 내장 `fetch`를 활용한 서버 개발이 훨씬 편리해졌습니다. TypeScript strict 모드를 처음 도입했을 때는 수백 개의 오류가 쏟아졌지만, 이제는 없어서는 안 될 도구가 되었습니다.

## 올해의 프로젝트들

### 성공한 프로젝트

이 블로그를 직접 개발한 것이 가장 보람 있는 프로젝트였습니다. MDX, Shiki 코드 하이라이팅, 다크 모드를 모두 직접 구현했습니다.

주요 기술 스택:

- **프레임워크**: Next.js 15 (App Router)
- **스타일링**: Tailwind CSS 4
- **콘텐츠**: MDX + gray-matter
- **코드 하이라이팅**: Shiki
- **배포**: Vercel

### 실패에서 배운 것

올해 초에는 지나치게 복잡한 상태 관리 라이브러리를 도입했다가 오버엔지니어링으로 팀원들을 힘들게 한 적이 있습니다. 그 경험에서 "YAGNI(You Aren't Gonna Need It)" 원칙의 중요성을 배웠습니다.

## 독서 목록

올해 읽은 기술 서적들:

1. **Clean Architecture** - Robert C. Martin
2. **A Philosophy of Software Design** - John Ousterhout
3. **TypeScript Deep Dive** - Basarat Ali Syed (온라인 무료)

## 수치로 보는 2025년

| 지표 | 수치 |
|------|------|
| 커밋 수 | 1,247개 |
| PR 리뷰 | 89개 |
| 블로그 포스트 | 24개 |
| 읽은 기술 서적 | 5권 |
| 오픈소스 기여 | 3개 프로젝트 |

## 2026년 목표

- Rust 언어 기초 학습
- 오픈소스 프로젝트 적극적으로 기여
- 기술 블로그 월 2회 이상 포스팅
- 사이드 프로젝트 하나를 실제 서비스로 런칭

## 마치며

개발자로서의 성장은 선형적이지 않습니다. 때로는 막막함을 느끼기도 하고, 때로는 모든 것이 연결되는 경험을 하기도 합니다. 중요한 것은 꾸준히 학습하고 적용하는 것입니다.

2025년 한 해 동안 이 블로그를 읽어주신 모든 분들께 감사드립니다.
