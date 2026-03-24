# Agent Eval Runner

## Overview
동일한 스펙을 여러 AI 코딩 에이전트에 실행시키고, 결과를 정량 비교하는 벤치마크 도구.
하네스(loop.sh)의 4페이즈 구조를 활용하여 실전 코딩 태스크 기반 평가 수행.

## 핵심 개념
- **Benchmark**: 하나의 스펙(specs/*.md) + 프로젝트 설정(pom.xml/package.json 등)
- **Agent Backend**: 에이전트 실행 방식 (claude, openai-codex, custom 등)
- **Run**: 특정 benchmark를 특정 agent backend로 실행한 단일 결과
- **Suite**: 여러 benchmark × 여러 agent backend의 전체 실행 결과

## CLI Interface
```bash
# 단일 벤치마크 실행
agent-eval run --benchmark benchmarks/word-counter --agent claude --output results/

# 여러 에이전트 비교
agent-eval compare --benchmark benchmarks/word-counter \
  --agents claude,openai \
  --output results/

# 전체 스위트 실행
agent-eval suite --config eval-config.yaml --output results/

# 결과 리포트
agent-eval report --results results/ --format html
agent-eval report --results results/ --format json
agent-eval report --results results/ --format markdown
```

## 벤치마크 구조
```
benchmarks/
├── word-counter/           # 기존 gallery 프로젝트 재사용
│   ├── specs/
│   ├── pyproject.toml
│   └── CLAUDE.md
├── employee-crud/
│   ├── specs/
│   ├── pom.xml
│   └── CLAUDE.md
└── benchmark.yaml          # 벤치마크 메타데이터
```

benchmark.yaml:
```yaml
name: word-counter
language: python
complexity: simple      # simple / medium / complex
expected_tests: 100     # 기대 테스트 수 (참고값)
expected_items: 5       # 기대 구현 항목 수
timeout: 3600           # 최대 실행 시간 (초)
```

## Agent Backend 인터페이스
```python
class AgentBackend(ABC):
    @abstractmethod
    def run(self, benchmark_dir: Path, output_dir: Path) -> RunResult:
        """벤치마크를 실행하고 결과를 반환"""
        pass
```

### 구현할 Backend
1. **ClaudeBackend**: `claude -p --model {model}` 호출 (기존 loop.sh 활용)
2. **MockBackend**: 테스트용 — 미리 준비된 결과를 반환 (실제 API 호출 없음)

참고: OpenAI/Gemini 등 추가 backend는 어댑터 패턴으로 확장 가능하도록 인터페이스만 정의

## 평가 메트릭
```python
@dataclass
class RunResult:
    agent: str                # 에이전트 이름
    benchmark: str            # 벤치마크 이름
    success: bool             # 빌드 + 테스트 전체 통과 여부

    # Correctness
    build_success: bool       # mvn compile / npm run build 성공
    test_total: int           # 총 테스트 수
    test_passed: int          # 통과 테스트 수
    test_pass_rate: float     # 통과율 (0.0 ~ 1.0)

    # Efficiency
    total_iterations: int     # 전체 반복 수
    total_time_seconds: float # 총 소요 시간
    phase_times: dict         # 페이즈별 소요 시간

    # Cost
    total_tokens_in: int      # 입력 토큰
    total_tokens_out: int     # 출력 토큰
    estimated_cost: float     # 추정 비용 ($)

    # Quality
    items_completed: int      # 완료 항목 수
    items_total: int          # 전체 항목 수
    stuck_count: int          # stuck 발생 횟수
    circuit_breaker_count: int # 회로 차단 횟수
```

## 결과 파싱
- `IMPLEMENTATION_PLAN.md` → items_completed / items_total (DONE 카운트)
- `progress.txt` → phase_times, iterations
- `cost.log` (하네스 생성) → tokens, cost
- `mvn test` / `pytest` 출력 → test_total, test_passed
- `logs/` 디렉토리 → stuck_count, circuit_breaker

## 리포트 생성
HTML 리포트:
- 에이전트별 비교 테이블 (메트릭 전체)
- 레이더 차트: correctness, speed, cost, reliability 4축
- 페이즈별 시간 분포 (stacked bar chart)
- 벤치마크별 통과/실패 히트맵

Markdown 리포트:
- 비교 테이블
- 승자 요약
- 상세 메트릭

## 프로젝트 구조
```
src/agent_eval/
├── __init__.py
├── cli.py              # argparse CLI
├── config.py           # eval-config.yaml 파싱
├── runner.py           # 벤치마크 실행 오케스트레이터
├── backends/
│   ├── __init__.py
│   ├── base.py         # AgentBackend ABC
│   ├── claude.py       # Claude Code backend
│   └── mock.py         # Mock backend (테스트용)
├── parser.py           # 결과 파싱 (plan, progress, cost, test output)
├── metrics.py          # RunResult 계산
├── report/
│   ├── __init__.py
│   ├── html.py         # HTML 리포트 생성
│   ├── markdown.py     # Markdown 리포트 생성
│   └── json_report.py  # JSON 리포트
└── models.py           # 데이터 모델 (RunResult, BenchmarkConfig 등)
```

## 의존성
- Python 3.11+ / uv
- `pyyaml` — config 파싱
- `jinja2` — HTML 리포트 템플릿
- 외부 API 없음 (에이전트 호출은 subprocess로 CLI 실행)
