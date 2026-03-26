# Agent Loop Replay Debugger

## Overview
자율 코딩 하네스(harness-for-real 등)의 실행 세션을 파싱하여
iteration별로 step-through 할 수 있는 TUI(Terminal UI) 디버거.
"에이전트 비행기록장치" — 200회 이터레이션 후 어디서 잘못됐는지 즉시 추적 가능.

## 입력 소스 (하네스 세션 디렉토리 구조)
```
project/
├── .harness-logs/
│   ├── cost.log              # 라인별: timestamp phase=X iter=N model=M in=N out=N cost=$X cumulative=$X item="..."
│   ├── phase.log             # 라인별: timestamp PHASE iter=N status=OK|FAIL
│   ├── metrics.log           # 라인별: timestamp metric=X value=Y
│   └── harness-state.json    # {"current_phase":"build","iteration":15,"stuck_count":2,...}
├── progress.txt              # 세션별 자유 텍스트 로그 (=== Session ... === 구분)
├── IMPLEMENTATION_PLAN.md    # status: DONE/TODO 항목
├── LEARNINGS.md              # 빌드 중 발견한 학습 기록
└── .git/                     # git log로 iteration별 커밋 추적
```

## 핵심 기능

### 1. Session Parser
- `cost.log` 파싱: 각 라인을 `CostEntry` 데이터클래스로 변환
  - 필드: timestamp(datetime), phase(str), iteration(int), model(str), tokens_in(int), tokens_out(int), cost(Decimal), cumulative_cost(Decimal), item(str)
  - 파싱 실패 라인은 skip + warning (절대 크래시하지 않음)
- `phase.log` 파싱: `PhaseEntry(timestamp, phase, iteration, status)`
- `progress.txt` 파싱: `=== Session ... ===` 블록 단위로 분리 → `SessionBlock(timestamp, content, items_completed)`
  - `Completed: Item N - ...` 패턴에서 완료 항목 추출
- `harness-state.json` 파싱: 현재 상태 로드
- `IMPLEMENTATION_PLAN.md` 파싱: 항목별 status 추출 → `PlanItem(number, title, status, priority)`
- `git log --oneline` 파싱: `GitCommit(hash, message, timestamp)` — iteration과 매칭

### 2. Session Timeline 구성
- 모든 파싱 결과를 시간순으로 병합 → `TimelineEvent` 리스트
- `TimelineEvent`: timestamp, event_type(cost|phase|commit|session), phase, iteration, data(Union[CostEntry, PhaseEntry, GitCommit, SessionBlock])
- iteration 단위로 그룹핑 → `Iteration` 객체 (events, cost_total, tokens_total, items_done, git_commits)

### 3. TUI (Textual 기반)
- **Header**: 프로젝트명, 총 이터레이션 수, 총 비용, 총 시간
- **Left Panel**: iteration 리스트 (번호, phase, 비용, pass/fail 아이콘)
  - 키보드 위/아래로 탐색, Enter로 선택
- **Right Panel**: 선택된 iteration 상세
  - 탭 1: Overview (phase, model, tokens in/out, cost, duration, items completed)
  - 탭 2: Progress Log (progress.txt에서 해당 세션 블록)
  - 탭 3: Git Diff (해당 iteration의 커밋들 — `git show --stat` 출력)
  - 탭 4: Cost Chart (누적 비용 ASCII 차트 — iteration별)
- **Footer**: 단축키 안내 (q=quit, j/k=up/down, 1-4=tab switch, /=search)
- **Search**: `/keyword`로 progress.txt 내 텍스트 검색 → 해당 iteration으로 점프

### 4. CLI 인터페이스
```
agent-replay <project-dir>                    # TUI 모드
agent-replay <project-dir> --summary          # 텍스트 요약만 출력 (no TUI)
agent-replay <project-dir> --iteration 15     # 특정 iteration 상세 출력
agent-replay <project-dir> --failures         # 실패한 iteration만 필터
agent-replay <project-dir> --export report.json  # JSON 내보내기
```

## 데이터 모델
```python
@dataclass
class CostEntry:
    timestamp: datetime
    phase: str
    iteration: int
    model: str
    tokens_in: int
    tokens_out: int
    cost: Decimal
    cumulative_cost: Decimal
    item: str

@dataclass
class PhaseEntry:
    timestamp: datetime
    phase: str
    iteration: int
    status: str  # "OK" | "FAIL"

@dataclass
class GitCommit:
    hash: str
    message: str
    timestamp: datetime

@dataclass
class SessionBlock:
    timestamp: datetime
    content: str
    items_completed: list[str]  # ["Item 3 - Content converter", ...]

@dataclass
class PlanItem:
    number: int
    title: str
    status: str  # "DONE" | "TODO"
    priority: str

@dataclass
class TimelineEvent:
    timestamp: datetime
    event_type: str  # "cost" | "phase" | "commit" | "session"
    phase: str
    iteration: int
    data: CostEntry | PhaseEntry | GitCommit | SessionBlock

@dataclass
class Iteration:
    number: int
    phase: str
    events: list[TimelineEvent]
    cost_total: Decimal
    tokens_in: int
    tokens_out: int
    items_done: list[str]
    git_commits: list[GitCommit]
    status: str  # "OK" | "FAIL" | "STUCK"
```

## 에러 처리
- 프로젝트 디렉토리에 `.harness-logs/`가 없으면 → "Not a harness project" 에러 + 종료코드 1
- 개별 로그 파일 없음 → 해당 데이터 없이 진행 (graceful degradation)
- 파싱 실패 라인 → skip + stderr warning (절대 전체 중단 아님)
- git 없는 프로젝트 → git 관련 탭 비활성화
- 빈 세션 (0 iterations) → "Empty session" 메시지

## 비기능 요구사항
- 1,000 iteration 세션도 1초 이내 로드
- 외부 API 호출 없음 (순수 로컬 파일 파싱)
- Python 3.11+ 표준 라이브러리 + textual + rich만 의존
- 단일 `pip install`로 설치 가능
