# Tistory Extractor

## Overview
Tistory 블로그에서 글을 추출하는 모듈.
3단계 fallback 전략: Open API → 백업 XML → 웹 스크래핑

## Strategy 1: Tistory Open API (Primary)
- Base URL: `https://www.tistory.com/apis`
- 인증: Access Token (OAuth 2.0 또는 앱 등록 후 발급)
- 엔드포인트:
  - `GET /post/list` — 글 목록 (blogName, page)
  - `GET /post/read` — 글 상세 (blogName, postId)
  - `GET /category/list` — 카테고리 목록
- 응답: JSON (title, content(HTML), categoryId, tags, date, url)
- Rate limit 존재 — 요청 간 딜레이 (1초)
- 실패 조건: 401 (토큰 만료), API 종료/변경 시 → Strategy 2로 fallback

## Strategy 2: Backup XML Parsing (Fallback)
- Tistory 관리자 → 블로그 관리 → 데이터 관리 → 백업 → XML 파일 다운로드
- XML 파싱: Python `xml.etree.ElementTree` 또는 `lxml`
- 입력: 사용자가 수동으로 다운로드한 XML 파일 경로
- XML 구조 (정확히 이 형태를 파싱해야 함):
```xml
<blog>
  <posts>
    <post>
      <id>1</id>
      <title>글 제목</title>
      <content><![CDATA[<h2>본문</h2>]]></content>
      <category>카테고리명</category>
      <tags>
        <tag>Python</tag>
        <tag>Flask</tag>
      </tags>
      <published>2024-06-15T10:30:00+09:00</published>
      <url>https://blog.tistory.com/1</url>
    </post>
  </posts>
</blog>
```
- **필수 파싱 규칙**:
  - `<published>` → ISO 8601 datetime 파싱 (`datetime.fromisoformat()` 사용). 반드시 `published_at` 필드에 날짜가 들어가야 함. `0001-01-01` 같은 기본값은 허용하지 않음
  - `<tags>` 내부의 각 `<tag>` 엘리먼트 → `tags: list[str]`에 개별 추가. 빈 리스트가 되면 안 됨 (태그가 XML에 존재할 경우)
  - `<category>` → `category` 필드에 텍스트 그대로 저장
  - `<content>` → CDATA 내부 HTML을 `content_html`에 저장

## Strategy 3: Web Scraping (Last Resort)
- 블로그 URL 패턴: `https://{blogname}.tistory.com/{postId}`
- sitemap.xml 또는 아카이브 페이지에서 글 URL 수집
- BeautifulSoup으로 본문 추출 (article 태그 또는 .entry-content 클래스)
- 카테고리/태그: 페이지 메타데이터 또는 사이드바에서 추출
- 이미지 URL 수집
- Rate limit: 요청 간 2초 딜레이, robots.txt 준수

## 추출 결과 데이터 모델
```python
@dataclass
class TistoryPost:
    id: str                    # 원본 post ID
    title: str                 # 제목
    content_html: str          # HTML 본문
    category: str              # 카테고리명
    tags: list[str]            # 태그 목록
    published_at: datetime     # 발행일
    url: str                   # 원본 URL
    images: list[str]          # 이미지 URL 목록
```

## 에러 처리
- API 인증 실패 → Strategy 2 자동 전환 (로그 출력)
- 백업 파일 없음/파싱 실패 → Strategy 3 자동 전환
- 스크래핑 차단(403) → 에러 리포트 + 부분 결과 저장
- 네트워크 오류 → 3회 재시도 후 skip (로그 기록)
