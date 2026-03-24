# Prompt Version Control

## Overview
AI 에이전트용 프롬프트(PROMPT_*.md) 파일의 버전 관리, A/B 테스트, 성능 추적 도구.
프롬프트 변경이 에이전트 실행 결과에 미치는 영향을 정량화.

## 핵심 개념
- **Prompt Set**: 관련 프롬프트 파일 묶음 (예: PROMPT_socratic.md + PROMPT_plan.md + PROMPT_build.md + PROMPT_verify.md)
- **Version**: Prompt Set의 특정 시점 스냅샷 (해시 기반 ID)
- **Experiment**: 두 Version을 같은 벤치마크에 실행하여 비교
- **Metric Binding**: 프롬프트 버전 ↔ 실행 결과(비용, 시간, 테스트 수) 연결

## CLI Interface
```bash
# 프롬프트 셋 초기화
prompt-vc init --dir ./prompts

# 현재 프롬프트 스냅샷 저장
prompt-vc snapshot --dir ./prompts --message "Socratic 질문 개선"

# 스냅샷 목록
prompt-vc log
# v3  2026-03-20  "Socratic 질문 개선"
# v2  2026-03-19  "Build 프롬프트 병렬 빌드 지시 추가"
# v1  2026-03-18  "초기 버전"

# 두 버전 diff
prompt-vc diff v2 v3

# 특정 버전 복원
prompt-vc checkout v2 --dir ./prompts

# 실행 결과 바인딩
prompt-vc bind v3 --result results/run_20260320.json

# A/B 비교 리포트
prompt-vc compare v2 v3

# 전체 버전별 성능 추이
prompt-vc trend
```

## 저장 구조
```
.prompt-vc/
├── config.yaml           # 설정 (추적 대상 파일 패턴 등)
├── snapshots/
│   ├── v1/
│   │   ├── metadata.yaml # 버전 정보 (hash, message, timestamp)
│   │   ├── PROMPT_socratic.md
│   │   ├── PROMPT_plan.md
│   │   ├── PROMPT_build.md
│   │   └── PROMPT_verify.md
│   ├── v2/
│   │   └── ...
│   └── v3/
│       └── ...
├── bindings/
│   ├── v1_run1.json      # 버전 ↔ 결과 바인딩
│   ├── v3_run1.json
│   └── v3_run2.json
└── index.yaml            # 전체 버전 인덱스
```

## Snapshot (스냅샷)
```yaml
# metadata.yaml
version: "v3"
hash: "a1b2c3d4"          # 전체 프롬프트 파일의 SHA256 해시
message: "Socratic 질문 개선"
timestamp: "2026-03-20T14:30:00+09:00"
files:
  - name: PROMPT_socratic.md
    hash: "e5f6g7h8"
    size: 2345
  - name: PROMPT_build.md
    hash: "i9j0k1l2"
    size: 4567
parent: "v2"               # 이전 버전
```

## Binding (결과 바인딩)
```yaml
# v3_run1.json
version: "v3"
benchmark: "word-counter"
agent: "claude"
timestamp: "2026-03-20T15:00:00+09:00"
metrics:
  success: true
  test_pass_rate: 1.0
  total_tests: 144
  total_iterations: 11
  total_time_seconds: 2220
  estimated_cost: 3.06
  items_completed: 5
  stuck_count: 1
```

## Diff (버전 비교)
- 파일별 unified diff (git diff 스타일)
- 변경된 파일 수, 추가/삭제 라인 수
- 변경 요약 (어떤 프롬프트의 어떤 섹션이 바뀌었는지)

## Compare (A/B 리포트)
두 버전의 바인딩된 결과를 비교:
```
=== Prompt A/B Comparison: v2 vs v3 ===

Benchmark: word-counter
                    v2          v3          Δ
Test Pass Rate:    0.95        1.00       +5.3%  ✅
Total Iterations:  14          11         -21.4% ✅
Total Time:       45m         37m        -17.8% ✅
Cost:             $3.82       $3.06      -19.9% ✅
Stuck Count:       2           1         -50.0% ✅

Winner: v3 (5/5 metrics improved)
Key Change: "Socratic 질문 개선" — reduced ambiguity, fewer build retries
```

## Trend (성능 추이)
모든 버전의 바인딩된 결과를 시계열로:
- 버전별 test_pass_rate 추이 (라인 차트)
- 버전별 cost 추이
- 버전별 iterations 추이
- ASCII 차트 (터미널) 또는 HTML 차트

## 프로젝트 구조
```
src/prompt_vc/
├── __init__.py
├── cli.py               # CLI 진입점
├── snapshot.py          # 스냅샷 생성/관리
├── binding.py           # 결과 바인딩
├── diff.py              # 버전 diff
├── compare.py           # A/B 비교
├── trend.py             # 성능 추이
├── storage.py           # .prompt-vc/ 디렉토리 관리
├── report/
│   ├── __init__.py
│   ├── terminal.py      # 터미널 출력 (테이블, ASCII 차트)
│   ├── html.py          # HTML 리포트
│   └── markdown.py      # Markdown 리포트
└── models.py            # 데이터 모델
```

## 의존성
- Python 3.11+ / uv
- `pyyaml` — YAML 설정/메타데이터
- `jinja2` — HTML 리포트 (선택)
- 외부 서비스 의존 없음 — 모든 데이터 로컬 파일
