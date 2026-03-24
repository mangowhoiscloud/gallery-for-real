import { validatePosts } from '../lib/validation';
import { generateExcerpt, extractHeadings, calculateReadingTime } from '../lib/markdown';
import type { PostMeta } from '../lib/types';

// ── Helpers ──────────────────────────────────────────────────────────────────

function makePost(overrides: Partial<PostMeta> = {}): PostMeta {
  return {
    title: '제목',
    date: '2026-01-15',
    category: '개발',
    tags: ['TypeScript'],
    slug: 'my-post',
    ...overrides,
  };
}

// ── validatePosts ─────────────────────────────────────────────────────────────

describe('validatePosts', () => {
  it('accepts valid posts and returns no warnings', () => {
    const posts = [makePost({ slug: 'a' }), makePost({ slug: 'b' })];
    const { valid, warnings } = validatePosts(posts);
    expect(valid).toHaveLength(2);
    expect(warnings).toHaveLength(0);
  });

  it('rejects post missing title', () => {
    const { valid, warnings } = validatePosts([makePost({ title: '' })]);
    expect(valid).toHaveLength(0);
    expect(warnings[0]).toMatch(/title/);
  });

  it('rejects post missing date', () => {
    const { valid, warnings } = validatePosts([makePost({ date: '' })]);
    expect(valid).toHaveLength(0);
    expect(warnings[0]).toMatch(/date/);
  });

  it('rejects post missing slug', () => {
    const { valid, warnings } = validatePosts([makePost({ slug: '' })]);
    expect(valid).toHaveLength(0);
    expect(warnings[0]).toMatch(/slug/);
  });

  it('rejects post with multiple missing fields', () => {
    const { valid, warnings } = validatePosts([makePost({ title: '', slug: '' })]);
    expect(valid).toHaveLength(0);
    expect(warnings[0]).toMatch(/title/);
    expect(warnings[0]).toMatch(/slug/);
  });

  it('rejects post with non-ISO date (YYYY/MM/DD)', () => {
    const { valid, warnings } = validatePosts([makePost({ date: '2026/01/15' })]);
    expect(valid).toHaveLength(0);
    expect(warnings[0]).toMatch(/invalid date/i);
  });

  it('rejects post with invalid date value (2026-02-30)', () => {
    const { valid, warnings } = validatePosts([makePost({ date: '2026-02-30' })]);
    expect(valid).toHaveLength(0);
    expect(warnings[0]).toMatch(/invalid date/i);
  });

  it('rejects duplicate slugs — second occurrence is skipped', () => {
    const posts = [makePost({ slug: 'dup' }), makePost({ slug: 'dup', title: '다른 제목' })];
    const { valid, warnings } = validatePosts(posts);
    expect(valid).toHaveLength(1);
    expect(warnings[0]).toMatch(/duplicate slug/i);
  });

  it('returns empty arrays for empty input', () => {
    const { valid, warnings } = validatePosts([]);
    expect(valid).toHaveLength(0);
    expect(warnings).toHaveLength(0);
  });

  it('accepts post with empty tags array (tags not required for validation)', () => {
    const { valid, warnings } = validatePosts([makePost({ tags: [] })]);
    expect(valid).toHaveLength(1);
    expect(warnings).toHaveLength(0);
  });
});

// ── generateExcerpt ───────────────────────────────────────────────────────────

describe('generateExcerpt', () => {
  it('returns content unchanged when under 150 chars', () => {
    const result = generateExcerpt('짧은 내용입니다.');
    expect(result).toBe('짧은 내용입니다.');
  });

  it('truncates to 150 chars and appends "..."', () => {
    const long = 'a'.repeat(200);
    const result = generateExcerpt(long);
    expect(result).toHaveLength(153); // 150 + "..."
    expect(result.endsWith('...')).toBe(true);
  });

  it('strips heading markers', () => {
    const result = generateExcerpt('## 섹션 제목\n내용');
    expect(result).not.toMatch(/^##/);
    expect(result).toContain('섹션 제목');
  });

  it('strips bold and italic markers', () => {
    const result = generateExcerpt('**굵은** 텍스트와 *이탤릭* 텍스트');
    expect(result).not.toContain('**');
    expect(result).not.toContain('*');
    expect(result).toContain('굵은');
    expect(result).toContain('이탤릭');
  });

  it('strips inline code', () => {
    const result = generateExcerpt('`const x = 1`을 사용하세요.');
    expect(result).not.toContain('`');
  });

  it('strips fenced code blocks', () => {
    const content = '설명\n```typescript\nconst x = 1;\n```\n이후';
    const result = generateExcerpt(content);
    expect(result).not.toContain('```');
    expect(result).not.toContain('const x');
    expect(result).toContain('이후');
  });

  it('strips markdown links and keeps link text', () => {
    const result = generateExcerpt('[Next.js 공식 문서](https://nextjs.org)를 참고하세요.');
    expect(result).not.toContain('https://');
    expect(result).toContain('Next.js 공식 문서');
  });

  it('strips images', () => {
    const result = generateExcerpt('![대체 텍스트](https://example.com/img.png) 이후 텍스트');
    expect(result).not.toContain('![');
    expect(result).not.toContain('example.com');
  });

  it('strips blockquote markers', () => {
    const result = generateExcerpt('> 인용문 내용');
    expect(result).not.toMatch(/^>/);
    expect(result).toContain('인용문 내용');
  });

  it('strips HTML tags', () => {
    const result = generateExcerpt('<p>단락 내용</p>과 <strong>강조</strong> 텍스트');
    expect(result).not.toContain('<p>');
    expect(result).not.toContain('<strong>');
    expect(result).toContain('단락 내용');
    expect(result).toContain('강조');
  });

  it('strips horizontal rules', () => {
    const result = generateExcerpt('앞 내용\n---\n뒤 내용');
    expect(result).not.toMatch(/---/);
    expect(result).toContain('앞 내용');
    expect(result).toContain('뒤 내용');
  });

  it('returns content as-is when exactly 150 chars (no ellipsis)', () => {
    const exact = 'a'.repeat(150);
    const result = generateExcerpt(exact);
    expect(result).toHaveLength(150);
    expect(result.endsWith('...')).toBe(false);
  });
});

// ── extractHeadings ───────────────────────────────────────────────────────────

describe('extractHeadings', () => {
  it('extracts h2 headings with level 2', () => {
    const headings = extractHeadings('## 설치 방법');
    expect(headings).toHaveLength(1);
    expect(headings[0].level).toBe(2);
    expect(headings[0].text).toBe('설치 방법');
  });

  it('extracts h3 headings with level 3', () => {
    const headings = extractHeadings('### 세부 설정');
    expect(headings).toHaveLength(1);
    expect(headings[0].level).toBe(3);
  });

  it('does not extract h1 headings', () => {
    const headings = extractHeadings('# 제목\n## 소제목');
    expect(headings).toHaveLength(1);
    expect(headings[0].level).toBe(2);
  });

  it('extracts multiple headings preserving order', () => {
    const content = '## 첫 번째\n내용\n### 하위 항목\n내용\n## 두 번째';
    const headings = extractHeadings(content);
    expect(headings).toHaveLength(3);
    expect(headings[0].text).toBe('첫 번째');
    expect(headings[1].level).toBe(3);
    expect(headings[2].text).toBe('두 번째');
  });

  it('generates id from heading text', () => {
    const headings = extractHeadings('## Hello World');
    expect(headings[0].id).toBe('hello-world');
  });

  it('generates id for Korean headings', () => {
    const headings = extractHeadings('## 설치 방법');
    expect(headings[0].id).toBe('설치-방법');
  });

  it('does not extract headings inside code blocks', () => {
    const content = '```\n## not a heading\n```\n## 실제 제목';
    const headings = extractHeadings(content);
    expect(headings).toHaveLength(1);
    expect(headings[0].text).toBe('실제 제목');
  });

  it('returns empty array for content with no h2/h3', () => {
    const headings = extractHeadings('# 제목만\n본문 내용');
    expect(headings).toHaveLength(0);
  });

  it('does not extract h4 or deeper headings', () => {
    const headings = extractHeadings('#### 깊은 제목\n## 정상 제목');
    expect(headings).toHaveLength(1);
    expect(headings[0].level).toBe(2);
  });

  it('strips special chars from heading id', () => {
    const headings = extractHeadings('## 어떻게? 사용하나!');
    // ? and ! should be stripped from the id
    expect(headings[0].id).not.toContain('?');
    expect(headings[0].id).not.toContain('!');
    expect(headings[0].id).toContain('어떻게');
  });
});

// ── calculateReadingTime ──────────────────────────────────────────────────────

describe('calculateReadingTime', () => {
  it('returns "N분 소요" format', () => {
    const result = calculateReadingTime('가'.repeat(500));
    expect(result).toMatch(/^\d+분 소요$/);
  });

  it('calculates 1분 소요 for exactly 500 Korean chars', () => {
    const result = calculateReadingTime('가'.repeat(500));
    expect(result).toBe('1분 소요');
  });

  it('calculates 2분 소요 for ~1000 Korean chars', () => {
    const result = calculateReadingTime('가'.repeat(1000));
    expect(result).toBe('2분 소요');
  });

  it('rounds up to nearest minute', () => {
    // 501 chars → ceil(501/500) = 2
    const result = calculateReadingTime('가'.repeat(501));
    expect(result).toBe('2분 소요');
  });

  it('excludes code blocks from character count', () => {
    // 500 chars of Korean + a code block
    const content = '가'.repeat(500) + '\n```\n' + 'x'.repeat(5000) + '\n```';
    const result = calculateReadingTime(content);
    expect(result).toBe('1분 소요');
  });

  it('returns at least 1분 소요 for any non-empty content', () => {
    const result = calculateReadingTime('짧다');
    expect(result).toBe('1분 소요');
  });
});
