---
title: "TypeScript strict 모드로 버그 없는 코드 작성하기"
date: "2026-02-08"
category: "개발"
tags: ["TypeScript", "타입 시스템", "strict", "best practices"]
slug: "typescript-strict-mode"
---

# TypeScript strict 모드로 버그 없는 코드 작성하기

TypeScript의 `strict` 모드는 여러 타입 검사 옵션을 활성화하여 런타임 오류를 컴파일 시점에 잡아냅니다. 이 글에서는 strict 모드의 각 옵션과 실제 적용 방법을 살펴봅니다.

## strict 모드가 활성화하는 옵션들

```json
{
  "compilerOptions": {
    "strict": true,
    // strict: true는 다음 옵션들을 모두 활성화합니다:
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "alwaysStrict": true
  }
}
```

## strictNullChecks

가장 중요한 옵션입니다. `null`과 `undefined`를 명시적으로 처리해야 합니다.

```typescript
// 오류 발생
function getLength(str: string | null): number {
  return str.length; // Error: 'str' is possibly 'null'
}

// 올바른 처리
function getLength(str: string | null): number {
  if (str === null) return 0;
  return str.length;
}

// 옵셔널 체이닝 활용
function getUserName(user: { name?: string } | null): string {
  return user?.name ?? '익명';
}
```

## noImplicitAny

암시적 `any` 타입 사용을 금지합니다.

```typescript
// 오류 발생
function processData(data) { // Error: Parameter 'data' implicitly has an 'any' type
  return data.value;
}

// 올바른 타입 명시
interface DataItem {
  value: string;
  count: number;
}

function processData(data: DataItem): string {
  return data.value;
}
```

## 실용적인 타입 패턴

### 결과 타입 (Result Type)

```typescript
type Result<T, E = Error> =
  | { success: true; data: T }
  | { success: false; error: E };

async function fetchPost(slug: string): Promise<Result<Post>> {
  try {
    const post = await getPostBySlug(slug);
    if (!post) {
      return { success: false, error: new Error(`Post not found: ${slug}`) };
    }
    return { success: true, data: post };
  } catch (error) {
    return { success: false, error: error instanceof Error ? error : new Error(String(error)) };
  }
}

// 사용
const result = await fetchPost('my-post');
if (result.success) {
  console.log(result.data.title); // 타입 안전
} else {
  console.error(result.error.message);
}
```

### 유니온 타입 내로잉

```typescript
type Shape =
  | { kind: 'circle'; radius: number }
  | { kind: 'rectangle'; width: number; height: number };

function getArea(shape: Shape): number {
  switch (shape.kind) {
    case 'circle':
      return Math.PI * shape.radius ** 2;
    case 'rectangle':
      return shape.width * shape.height;
  }
}
```

## 타입 안전한 환경 변수

```typescript
// lib/env.ts
function getEnvVar(key: string): string {
  const value = process.env[key];
  if (!value) {
    throw new Error(`Missing required environment variable: ${key}`);
  }
  return value;
}

export const config = {
  siteUrl: process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000',
  apiKey: getEnvVar('API_KEY'), // 빌드 시 오류 발생
} as const;
```

## 컴파일러 옵션 권장 설정

| 옵션 | 용도 |
|------|------|
| `noUnusedLocals` | 미사용 변수 오류 |
| `noUnusedParameters` | 미사용 매개변수 오류 |
| `noFallthroughCasesInSwitch` | switch 폴스루 방지 |
| `exactOptionalPropertyTypes` | 옵셔널 프로퍼티 엄격 검사 |

## 결론

TypeScript strict 모드는 초기 설정이 다소 번거롭지만, 런타임 오류를 크게 줄여줍니다. 프로젝트 초기부터 적용하면 안전한 코드베이스를 유지할 수 있습니다.
