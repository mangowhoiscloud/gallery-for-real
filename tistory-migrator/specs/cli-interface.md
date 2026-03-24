# CLI Interface

## Overview
마이그레이션 도구의 CLI 인터페이스. 단일 커맨드로 전체 파이프라인 실행.

## 사용법
```bash
# Open API 방식 (기본)
tistory-migrate --blog myblog --token ACCESS_TOKEN --output ./output

# 백업 XML 방식
tistory-migrate --backup ./tistory-backup.xml --output ./output

# 웹 스크래핑 방식 (명시적)
tistory-migrate --blog myblog --scrape --output ./output

# 옵션
tistory-migrate --blog myblog --token TOKEN --output ./output \
  --category "개발"          # 특정 카테고리만 추출
  --after 2023-01-01         # 특정 날짜 이후 글만
  --before 2024-12-31        # 특정 날짜 이전 글만
  --dry-run                  # 추출만, 파일 생성 안 함
  --no-images                # 이미지 다운로드 스킵
  --verbose                  # 상세 로그
```

## CLI 인자
| 인자 | 필수 | 기본값 | 설명 |
|------|------|--------|------|
| `--blog` | API/스크래핑 시 | - | Tistory 블로그명 |
| `--token` | API 시 | - | Tistory Access Token |
| `--backup` | 백업 시 | - | 백업 XML 파일 경로 |
| `--scrape` | No | false | 강제 스크래핑 모드 |
| `--output` | Yes | `./output` | 출력 디렉토리 |
| `--category` | No | 전체 | 특정 카테고리 필터 |
| `--after` | No | - | 시작일 필터 (YYYY-MM-DD) |
| `--before` | No | - | 종료일 필터 (YYYY-MM-DD) |
| `--dry-run` | No | false | 미리보기 모드 |
| `--no-images` | No | false | 이미지 다운로드 스킵 |
| `--verbose` | No | false | 상세 로그 |

## 실행 흐름
1. 인자 파싱 + 유효성 검사
2. 추출 전략 결정 (token → API, backup → XML, scrape → 스크래핑)
3. 글 목록 추출 (필터 적용)
4. 진행률 표시 (`[23/150] Converting: 글 제목...`)
5. 각 글: HTML 추출 → Markdown 변환 → 이미지 다운로드 → 파일 저장
6. metadata.json 생성
7. 요약 출력

## 요약 출력 예시
```
=== Tistory Migration Complete ===
  Blog:       myblog.tistory.com
  Strategy:   Open API
  Posts:      150 extracted, 148 converted, 2 failed
  Categories: 8
  Tags:       45 unique
  Images:     312 downloaded, 3 failed
  Output:     ./output (23.4 MB)
  Duration:   2m 34s

  Failed posts:
    - [#45] 제목 (reason: image download timeout)
    - [#89] 제목 (reason: empty content)
```

## 프로젝트 구조
```
tistory_migrator/
├── __init__.py
├── cli.py              # argparse CLI 진입점
├── extractor/
│   ├── __init__.py
│   ├── base.py         # Extractor 인터페이스
│   ├── api.py          # Tistory Open API
│   ├── backup.py       # XML 백업 파싱
│   └── scraper.py      # 웹 스크래핑
├── converter.py        # HTML → Markdown 변환
├── image_downloader.py # 이미지 다운로드
├── models.py           # TistoryPost 데이터 모델
└── writer.py           # Markdown 파일 + metadata 출력
```

## 의존성
- `requests` — HTTP 클라이언트
- `beautifulsoup4` + `lxml` — HTML 파싱 / 스크래핑
- `markdownify` — HTML→Markdown 변환
- `pyyaml` — frontmatter 생성
- Python 3.11+ / uv 패키지 매니저
