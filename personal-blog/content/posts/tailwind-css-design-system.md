---
title: "Tailwind CSS로 디자인 시스템 구축하기"
date: "2026-01-25"
category: "디자인"
tags: ["Tailwind CSS", "Design System", "CSS", "UI"]
slug: "tailwind-css-design-system"
---

# Tailwind CSS로 디자인 시스템 구축하기

디자인 시스템은 일관된 사용자 경험을 위한 핵심 기반입니다. Tailwind CSS를 활용하면 유지보수 가능한 디자인 시스템을 효율적으로 구축할 수 있습니다.

## CSS 커스텀 프로퍼티로 테마 정의

Tailwind 4에서는 CSS-first 설정 방식을 채택했습니다. `@theme` 지시어로 디자인 토큰을 정의합니다.

```css
@import "tailwindcss";

@theme {
  --color-primary: #3b82f6;
  --color-primary-hover: #2563eb;
  --color-secondary: #8b5cf6;
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --spacing-section: 4rem;
  --border-radius-card: 0.75rem;
}
```

## 다크 모드 구현

CSS 변수를 활용한 다크 모드는 JavaScript 없이도 완벽하게 동작합니다.

```css
:root {
  --bg: #ffffff;
  --text: #1a1a1a;
  --accent: #3b82f6;
  --border: #e5e7eb;
}

.dark {
  --bg: #0f172a;
  --text: #e2e8f0;
  --accent: #60a5fa;
  --border: #334155;
}
```

## 컴포넌트 패턴

### 버튼 컴포넌트

```typescript
type ButtonVariant = 'primary' | 'secondary' | 'ghost';

interface ButtonProps {
  variant?: ButtonVariant;
  children: React.ReactNode;
  onClick?: () => void;
}

export function Button({ variant = 'primary', children, onClick }: ButtonProps) {
  const variants = {
    primary: 'bg-blue-500 hover:bg-blue-600 text-white',
    secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-800',
    ghost: 'hover:bg-gray-100 text-gray-700',
  };

  return (
    <button
      className={`px-4 py-2 rounded-lg transition-colors ${variants[variant]}`}
      onClick={onClick}
    >
      {children}
    </button>
  );
}
```

## 타이포그래피 스케일

일관된 타이포그래피를 위한 스케일을 정의합니다.

| 클래스 | 크기 | 용도 |
|--------|------|------|
| `text-xs` | 12px | 레이블, 메타 |
| `text-sm` | 14px | 보조 텍스트 |
| `text-base` | 16px | 본문 |
| `text-lg` | 18px | 부제목 |
| `text-xl` | 20px | 소제목 |
| `text-2xl` | 24px | 제목 |
| `text-4xl` | 36px | 대제목 |

## 간격 시스템

Tailwind의 기본 4px 그리드를 기반으로 한 간격 시스템:

- **xs**: 4px (p-1)
- **sm**: 8px (p-2)
- **md**: 16px (p-4)
- **lg**: 24px (p-6)
- **xl**: 32px (p-8)
- **2xl**: 48px (p-12)

## 결론

Tailwind CSS의 유틸리티 우선 접근법은 디자인 시스템 구축에 매우 효과적입니다. CSS 커스텀 프로퍼티와 결합하면 테마 전환이 간편하고, 컴포넌트 재사용성이 높아집니다.
