# Agent Knowledge Harvester

## Overview
완료된 하네스 세션의 git diff, LEARNINGS.md, progress.txt, CLARITY_LOG.md를 분석하여
재사용 가능한 패턴/스킬/룰을 자동 추출하는 CLI 도구.
하네스가 돌수록 스스로 똑똑해지는 플라이휠을 만든다.

## 입력 소스
```
project/
├── LEARNINGS.md              # 빌드 중 발견 기록 (하네스가 자동 생성)
├── CLARITY_LOG.md            # Socratic 페이즈 Q&A 기록
├── progress.txt              # 세션별 자유 텍스트 로그
├── IMPLEMENTATION_PLAN.md    # 구현 계획 + acceptance criteria
├── CLAUDE.md                 # 스택별 규칙
├── specs/                    # 원본 스펙 파일
└── .git/                     # git log/diff
```

## 핵심 기능

### 1. Learning Extractor
- `LEARNINGS.md` 파싱: 구조화된 학습 항목 추출
  - 각 항목: `LearningEntry(id, category, description, context, applicable_stacks)`
  - 카테고리 자동 분류: `error-recovery`, `library-quirk`, `pattern`, `performance`, `testing`, `compatibility`
  - 스택 태그 자동 추출: 파일 확장자/라이브러리 언급에서 (`python`, `java`, `nextjs`, `spring` 등)
- `CLARITY_LOG.md` 파싱: Socratic 라운드별 Q&A 추출
  - `ClarityEntry(round, question, answer, decision)`
  - 반복되는 질문 패턴 → 스펙 작성 가이드라인으로 승격

### 2. Git Diff Analyzer
- `git log --stat` 파싱: 파일별 변경 빈도 분석
- 자주 수정되는 파일 = "불안정 모듈" → 스펙 보강 필요 신호
- 되돌림(revert) 패턴 감지: 같은 파일이 추가→삭제→재추가 → "시행착오" 기록
- 커밋 메시지에서 `fix:` 패턴 추출 → 에러 패턴 데이터베이스

### 3. Pattern Synthesizer
- 추출된 학습 + git 분석 결과를 종합하여 재사용 가능한 룰 생성
- 출력 포맷:

```yaml
# harvest-output/rules/python-datetime-parsing.yaml
id: python-datetime-parsing
category: library-quirk
stacks: [python]
confidence: high  # high(3+ 세션에서 반복) | medium(2회) | low(1회)
source_projects: [tistory-migrator, agent-cost-analyzer]
rule: |
  datetime.fromisoformat()는 Python 3.11+에서 timezone-aware ISO 8601을 지원.
  Python 3.10 이하에서는 strptime 폴백 필요.
  datetime.min (0001-01-01)을 기본값으로 사용하지 말 것 — 실제 파싱 실패를 숨김.
applicable_to: |
  날짜 문자열을 파싱하는 모든 Python 프로젝트의 CLAUDE.md에 추가 권장.
```

### 4. Cross-Project Analysis
- 여러 프로젝트 디렉토리를 입력 → 프로젝트 간 공통 패턴 추출
- `--projects dir1 dir2 dir3` 또는 `--gallery <gallery-dir>` (갤러리 내 모든 프로젝트 스캔)
- 동일 학습이 2개 이상 프로젝트에서 반복 → confidence=high로 승격
- 스택별 그룹핑: Python 프로젝트끼리, Java끼리, Next.js끼리

### 5. Output Formats
```
harvest-output/
├── rules/                    # 개별 룰 YAML 파일
│   ├── python-datetime-parsing.yaml
│   ├── spring-mybatis-mapper.yaml
│   └── nextjs-shiki-import.yaml
├── skills/                   # CLAUDE.md에 바로 복사 가능한 스킬 블록
│   ├── python-common.md      # Python 프로젝트 공통 룰
│   ├── java-spring.md        # Java/Spring 프로젝트 공통 룰
│   └── nextjs-common.md      # Next.js 프로젝트 공통 룰
├── spec-guide.md             # Socratic Q&A에서 추출한 "스펙 작성 시 명시해야 할 것들"
├── instability-report.md     # 자주 수정된 불안정 모듈 리포트
└── summary.json              # 전체 요약 (프로젝트 수, 룰 수, 카테고리별 분포)
```

## CLI 인터페이스
```
agent-harvest <project-dir>                     # 단일 프로젝트 분석
agent-harvest --gallery <gallery-dir>           # 갤러리 전체 분석
agent-harvest --gallery <dir> --output <dir>    # 출력 디렉토리 지정
agent-harvest --gallery <dir> --stack python    # 특정 스택만 필터
agent-harvest --gallery <dir> --min-confidence medium  # confidence 필터
agent-harvest <dir> --format json               # JSON 출력 (기본: yaml+md)
agent-harvest <dir> --dry-run                   # 파싱만 하고 파일 생성 안 함
```

## 데이터 모델
```python
@dataclass
class LearningEntry:
    id: str                          # 자동 생성 (slugified)
    category: str                    # error-recovery | library-quirk | pattern | performance | testing | compatibility
    description: str                 # 한 줄 요약
    context: str                     # 상세 내용
    applicable_stacks: list[str]     # ["python", "java", ...]
    source_project: str              # 프로젝트명
    source_file: str                 # "LEARNINGS.md" | "progress.txt" | ...

@dataclass
class ClarityEntry:
    round: int
    question: str
    answer: str
    decision: str                    # 최종 결정 사항

@dataclass
class FileChurn:
    path: str
    add_count: int                   # 추가된 횟수
    modify_count: int                # 수정된 횟수
    delete_count: int                # 삭제된 횟수
    revert_count: int                # 되돌림 횟수
    net_changes: int                 # 총 변경 라인 수

@dataclass
class HarvestRule:
    id: str
    category: str
    stacks: list[str]
    confidence: str                  # "high" | "medium" | "low"
    source_projects: list[str]
    rule: str
    applicable_to: str

@dataclass
class HarvestResult:
    projects_analyzed: int
    total_learnings: int
    total_rules: int
    categories: dict[str, int]       # 카테고리별 룰 수
    stacks: dict[str, int]           # 스택별 룰 수
    high_confidence_rules: int
    unstable_files: list[FileChurn]
```

## 스택 자동 감지
프로젝트 디렉토리에서 자동으로 스택을 감지:
- `pyproject.toml` 또는 `setup.py` → python
- `pom.xml` → java, spring (pom 내용에서 spring-boot 의존성 확인)
- `package.json` → nodejs (next 의존성 → nextjs, react → react)
- `Cargo.toml` → rust
- `go.mod` → go

## 필수 동작 규칙

### Gallery 모드 파일 경로 네임스페이싱
- `--gallery` 모드에서 `instability-report.md`에 기록되는 파일 경로는 **반드시 프로젝트명을 접두사로 포함**해야 함
  - 예: `README.md` → `personal-blog/README.md`, `tistory-migrator/src/main.py`
  - 동일 파일명이 여러 프로젝트에 존재할 때 구분 불가능해지는 것을 방지
- `all_file_churns` 수집 시 각 프로젝트의 churn 항목에 프로젝트명 접두사 추가 (예: `FileChurn.path = f"{project_name}/{original_path}"`)
- 단일 프로젝트 모드에서는 접두사 없이 원본 경로 유지

### --dry-run 필터 반영
- `--dry-run` 모드에서도 `--stack`과 `--min-confidence` 필터가 **반드시 적용된 결과**를 표시해야 함
  - 필터 적용 전 전체 룰 수가 아닌, 필터 적용 후 실제로 기록될 룰 수를 출력
  - 예: "Would write 78 rules (filtered by stack=python)" — 전체 225개가 아닌 78개

## 에러 처리
- 프로젝트 디렉토리 없음 → 에러 + 종료코드 1
- LEARNINGS.md 없음 → 해당 소스 skip (다른 소스로 계속)
- git 없음 → git 분석 skip
- 파싱 실패 → skip + warning (graceful degradation)
- 빈 결과 (룰 0개) → "No patterns found" 메시지 + 종료코드 0

## 비기능 요구사항
- 외부 API 호출 없음 (LLM 없이 규칙 기반 추출)
- Python 3.11+ 표준 라이브러리 + pyyaml만 의존
- 갤러리 20개 프로젝트도 5초 이내 분석
- 단일 `pip install`로 설치 가능
