# Agent Cost Analyzer

## Overview
AI 에이전트 실행 로그를 파싱하여 토큰 사용량, 비용, 실패 패턴을 분석하고
대시보드 리포트를 생성하는 CLI 도구.

Ralphton Harness의 cost.log, progress.txt, logs/ 디렉토리를 입력으로 받음.

## 입력 데이터 형식

### cost.log (하네스 생성)
```
2026-03-19T14:23:45+09:00 phase=build iter=3 model=sonnet in=12500 out=3200 cost=$0.08 cumulative=$1.23 item=Item_3
2026-03-19T14:25:12+09:00 phase=build iter=4 model=opus in=45000 out=8900 cost=$0.89 cumulative=$2.12 item=Item_3
```

### progress.txt
```
=== Harness initialized: 2026-03-19T14:00:00+09:00 ===
Project type: python-uv
Completed: Item 1 - Tokenizer Module
...
```

### logs/ 디렉토리
```
logs/
├── socratic_iter1_20260319_140000.log
├── plan_iter1_20260319_140300.log
├── build_iter1_20260319_140600.log
└── ...
```

## CLI Interface
```bash
# 단일 프로젝트 분석
cost-analyze --project ./examples/word-counter --output report/

# 여러 프로젝트 비교
cost-analyze compare --projects ./examples/word-counter,./examples/asis-boot3 --output report/

# 실시간 모니터링 (tail -f 스타일)
cost-analyze watch --project ./examples/shop-boot3

# 특정 기간 필터
cost-analyze --project ./project --after 2026-03-19 --before 2026-03-21
```

## 분석 모듈

### 1. Log Parser
- cost.log 파싱 → 구조화된 데이터 (timestamp, phase, iteration, model, tokens, cost, item)
- progress.txt 파싱 → 타임라인 (phase 시작/끝, item 완료)
- logs/*.log 파싱 → 에러/경고 패턴 추출

### 2. Cost Breakdown
- **페이즈별 비용**: Socratic vs Plan vs Build vs Verify
- **모델별 비용**: Opus vs Sonnet (입력/출력 토큰 분리)
- **항목별 비용**: 어떤 구현 항목이 가장 비쌌는지
- **시간별 비용 추이**: 이터레이션 진행에 따른 누적 비용 그래프
- **비용 효율성**: 테스트 1개당 비용, 코드 1줄당 비용

### 3. Token Analysis
- 입력/출력 토큰 비율
- 페이즈별 토큰 사용 분포
- 모델 에스컬레이션 패턴 (Sonnet → Opus 전환 빈도)
- 토큰 사용 이상치 탐지 (평균 대비 3σ 초과)

### 4. Failure Pattern Detection
- **Stuck 패턴**: 같은 항목에서 반복 실패
- **Circuit Breaker 발동**: 모델 에스컬레이션 전환점
- **빌드 실패율**: 이터레이션 대비 빌드 성공률
- **에러 카테고리**: 컴파일 에러, 테스트 실패, 타임아웃 등
- **회복 시간**: stuck 발생 → 해결까지 걸린 이터레이션 수

### 5. Comparison Analysis (여러 프로젝트 비교)
- 프로젝트 간 비용/시간/테스트 수 비교 테이블
- 프로젝트 규모 대비 비용 효율성 비교
- 스택별(Java vs Python vs TypeScript) 비용 패턴

## 리포트 생성

### HTML Dashboard
- 비용 요약 카드 (총비용, 평균 이터레이션 비용, 모델 분포)
- 누적 비용 라인 차트
- 페이즈별 비용 파이 차트
- 항목별 비용 바 차트
- 실패 패턴 타임라인
- Jinja2 템플릿 + Chart.js (인라인, CDN)

### JSON Report
- 머신 리더블 분석 결과
- CI/CD 파이프라인 통합용

### Markdown Report
- 텍스트 기반 요약
- GitHub PR 코멘트 등에 활용

## 프로젝트 구조
```
src/agent_cost_analyzer/
├── __init__.py
├── cli.py               # CLI 진입점
├── parser/
│   ├── __init__.py
│   ├── cost_log.py      # cost.log 파서
│   ├── progress.py      # progress.txt 파서
│   └── build_log.py     # logs/*.log 파서
├── analyzer/
│   ├── __init__.py
│   ├── cost.py          # 비용 분석
│   ├── tokens.py        # 토큰 분석
│   ├── failures.py      # 실패 패턴 탐지
│   └── comparison.py    # 프로젝트 간 비교
├── report/
│   ├── __init__.py
│   ├── html.py          # HTML 대시보드
│   ├── json_report.py   # JSON 리포트
│   ├── markdown.py      # Markdown 리포트
│   └── templates/
│       └── dashboard.html  # Jinja2 HTML 템플릿
└── models.py            # 데이터 모델
```

## 의존성
- Python 3.11+ / uv
- `jinja2` — HTML 템플릿
- `pyyaml` — 설정 파싱 (선택)
- 외부 서비스 의존 없음
