# Gallery for Real

[harness-for-real](https://github.com/mangowhoiscloud/harness-for-real)가 자율 생성한 프로젝트 갤러리.

사람이 스펙만 제공하면, 하네스가 Socratic → Plan → Build → Verify 4페이즈를 거쳐 전체 코드를 자율 생성합니다.

## 프로젝트 목록

| 프로젝트 | 스택 | 도메인 | 입력 | 출력 | 테스트 |
|----------|------|--------|------|------|--------|
| [word-counter](word-counter/) | Python 3 + uv | 단어 빈도 분석 CLI | 스펙 2개 | 5모듈 + 5테스트 | 144 passed |
| [asis-boot3](asis-boot3/) | Java 21 + Spring Boot 3.3.7 | Employee CRUD REST API | 스펙 1개 + pom.xml + CLAUDE.md | 14항목 | 73 tests, BUILD SUCCESS |
| [asis-legacy](asis-legacy/) | Java 1.8 + Spring 4.3.4 | Employee CRUD REST API | 스펙 1개 + pom.xml + CLAUDE.md | 19항목 | 106 tests, BUILD SUCCESS |
| [shop-boot3](shop-boot3/) | Java 21 + Spring Boot 3.3.7 | 쇼핑몰 MVP (4 CRUD + 프론트) | 스펙 5개 + pom.xml + CLAUDE.md | 14항목 | 106 tests, BUILD SUCCESS |
| [shop-legacy](shop-legacy/) | Java 1.8 + Spring 4.3.4 | 쇼핑몰 MVP (4 CRUD + 프론트) | 스펙 5개 + pom.xml + CLAUDE.md | 15항목 | 138 tests, BUILD SUCCESS |
| [shop-front](shop-front/) | Next.js 15 + TypeScript + Tailwind 4 | 쇼핑몰 프론트엔드 (Shopify급 UI) | 스펙 1개 + package.json + CLAUDE.md | 15항목 (39 파일) | 364 tests passed |
| [tistory-migrator](tistory-migrator/) | Python 3.11 + uv | 티스토리 블로그 마이그레이션 CLI | 스펙 3개 + pyproject.toml + CLAUDE.md | 9항목 | 428 tests passed |
| [personal-blog](personal-blog/) | Next.js 15 + MDX + Shiki + Tailwind 4 | 개인 블로그 플랫폼 (SSG) | 스펙 1개 + package.json + CLAUDE.md | 25항목 | 415 tests passed |
| [agent-eval-suite](agent-eval-suite/) | Python 3.11 + uv | AI 에이전트 벤치마크 러너 | 스펙 1개 + pyproject.toml + CLAUDE.md | 17항목 | 283 tests passed |
| [agent-cost-analyzer](agent-cost-analyzer/) | Python 3.11 + uv | 하네스 실행 비용 분석 대시보드 | 스펙 1개 + pyproject.toml + CLAUDE.md | 14항목 | 335 tests passed |
| [prompt-version-control](prompt-version-control/) | Python 3.11 + uv | 프롬프트 버전 관리 + A/B 비교 | 스펙 1개 + pyproject.toml + CLAUDE.md | 14항목 | 248 tests passed |
| [agent-replay-debugger](agent-replay-debugger/) | Python 3.11 + uv + Textual TUI | 에이전트 세션 리플레이 디버거 | 스펙 1개 + pyproject.toml + CLAUDE.md | 19항목 | 618 tests passed |
| [agent-knowledge-harvester](agent-knowledge-harvester/) | Python 3.11 + uv + pyyaml | 세션 패턴/스킬 자동 추출 CLI | 스펙 1개 + pyproject.toml + CLAUDE.md | 16항목 | 577 tests passed |

**총 테스트: 3,835 passed** (13개 프로젝트)

## 이 프로젝트들은 어떤 자연어 지시로 만들어졌나?

사람이 하네스에 전달한 것은 자연어 요청 + 스펙 파일뿐입니다. 코드는 한 줄도 직접 작성하지 않았습니다.

### 1단계: word-counter
> "Python 단어 빈도 분석 CLI 도구를 만들어줘. 파일 입력, 정렬 옵션, CSV 내보내기 기능이 있으면 돼."

### 2단계: asis-boot3 / asis-legacy
> "기존 AS-IS 스프링 프로젝트의 Employee CRUD API를 하네스로 생성해봐. Boot3랑 레거시(Spring 4) 둘 다 만들어."

### 3단계: shop-boot3 / shop-legacy / shop-front
> "AS-IS 스펙으로 쇼핑몰 MVP를 만들 수 있도록 지시해봐. CRUD가 포함된 쇼핑몰 스펙별로 만드는 거야. 회원, 상품, 장바구니, 주문. 프론트도 만들어. Shopify 같은 프론티어 이커머스 참고해서 양질의 프론트 생성하고 백엔드 연결해."

### 4단계: tistory-migrator
> "티스토리에 몰린 블로그들을 내 개인 블로그로 옮기는 툴도 만들 수 있겠어? OpenAPI, fallback으로 백업 XML → 웹 스크래핑. 글 원문 전체 + 카테고리 + 태그."

### 5단계: personal-blog
> "마이그레이션한 글을 올릴 직접 만든 블로그. Next.js + MDX + SSG로."

### 6단계: agent-eval-suite / agent-cost-analyzer / prompt-version-control
> "하네스 엔지니어로서 에이전트 관련 프로젝트에 도움이 될만한 생산 아이디어가 있을까?" → 3가지 제안 → "세 가지 모두 진행해봐."

### 7단계: agent-replay-debugger / agent-knowledge-harvester
> "최근 모델/하네스 리서치를 참고해서 더 구현해볼 사안 있을까? 허깅 페이스 등을 참고해서 조사해볼래?" → 15가지 조사 → "1, 2번 진행하자. 프로덕션급 완성도와 가벼움, 심플함을 우선가치로. 코드엔 직접 손대지 말고."

## 진행 과정 (Step by Step)

```
1. 자연어 요청
   사람: "쇼핑몰 MVP 만들어줘"

2. 스펙 작성
   사람이 specs/ 폴더에 마크다운 스펙 작성 (기능, 엔드포인트, 데이터 모델)
   + CLAUDE.md (스택별 규칙)
   + pyproject.toml / pom.xml / package.json (프로젝트 설정)

3. 하네스 실행 (자동)
   $ bash run-demo.sh

   Phase 1: Socratic (스펙 모호성 질의응답, 최대 5라운드)
   → CLARITY_LOG.md 생성

   Phase 2: Plan (구현 계획 생성, 최대 3라운드)
   → IMPLEMENTATION_PLAN.md 생성 (항목별 의존성, 우선순위, acceptance criteria)

   Phase 3: Build (코드 자율 생성, 최대 20~30라운드)
   → src/ + tests/ 생성 (항목별 구현 + 테스트 → 커밋)

   Phase 4: Verify (검증, 최대 3라운드)
   → 스펙 준수 26개 기준 체크, 통합 검증, 배포 준비 체크

4. 결과 검증
   사람이 E2E 테스트로 실제 동작 확인
   → 버그 발견 시 코드를 직접 고치지 않고 스펙을 강화해서 하네스 재실행
   (예: tistory-migrator 4개 버그 → 스펙에 acceptance criteria 추가 → 재빌드 → 전부 해결)

5. 갤러리 등록
   결과물을 gallery-for-real에 복사 + 커밋
```

## 핵심 원칙

**코드를 직접 고치지 않는다.** 버그가 발견되면 스펙/프롬프트/하네스를 수정하고 재실행한다.
이 갤러리의 모든 코드는 하네스가 자율 생성한 것이며, 사람의 코드 수정은 0줄입니다.

## 구조

각 프로젝트 폴더에는 다음이 포함됩니다:

```
project-name/
├── specs/                  ← 사람이 작성한 스펙 (입력)
├── src/                    ← 하네스가 생성한 코드 (출력)
├── pom.xml / pyproject.toml ← 프로젝트 설정
├── CLAUDE.md               ← 스택별 룰
├── CLARITY_LOG.md           ← Socratic 페이즈 결과
├── IMPLEMENTATION_PLAN.md   ← Plan 페이즈 결과
└── LEARNINGS.md            ← 빌드 중 학습 기록
```

## 하네스란?

[harness-for-real](https://github.com/mangowhoiscloud/harness-for-real) — Claude Code를 비대화형(`claude -p`)으로 호출하여 4페이즈 자율 코딩 루프를 실행하는 셸 기반 하네스입니다.

## 라이선스

Apache 2.0
