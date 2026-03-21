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
