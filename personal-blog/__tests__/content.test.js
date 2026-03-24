const fs = require('fs');
const path = require('path');
const matter = require('gray-matter');

const POSTS_DIR = path.join(__dirname, '..', 'content', 'posts');
const ABOUT_FILE = path.join(__dirname, '..', 'content', 'about.md');

function readPost(filename) {
  const raw = fs.readFileSync(path.join(POSTS_DIR, filename), 'utf-8');
  return matter(raw);
}

const POST_FILES = fs.readdirSync(POSTS_DIR).filter((f) => f.endsWith('.md'));

describe('content/posts — file count', () => {
  test('has exactly 5 sample posts', () => {
    expect(POST_FILES.length).toBe(5);
  });
});

describe('content/posts — required frontmatter fields', () => {
  const REQUIRED_FIELDS = ['title', 'date', 'category', 'tags', 'slug'];

  POST_FILES.forEach((filename) => {
    describe(filename, () => {
      let parsed;
      beforeAll(() => {
        parsed = readPost(filename);
      });

      REQUIRED_FIELDS.forEach((field) => {
        test(`has required field: ${field}`, () => {
          expect(parsed.data[field]).toBeDefined();
        });
      });

      test('date matches YYYY-MM-DD format', () => {
        expect(parsed.data.date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      });

      test('tags is an array', () => {
        expect(Array.isArray(parsed.data.tags)).toBe(true);
        expect(parsed.data.tags.length).toBeGreaterThan(0);
      });

      test('slug matches filename (without .md)', () => {
        const expectedSlug = filename.replace(/\.md$/, '');
        expect(parsed.data.slug).toBe(expectedSlug);
      });

      test('has non-empty body content', () => {
        expect(parsed.content.trim().length).toBeGreaterThan(100);
      });
    });
  });
});

describe('content/posts — date range', () => {
  test('dates span at least 2 months', () => {
    const dates = POST_FILES.map((f) => {
      const { data } = readPost(f);
      return new Date(data.date).getTime();
    });
    const minDate = Math.min(...dates);
    const maxDate = Math.max(...dates);
    const diffDays = (maxDate - minDate) / (1000 * 60 * 60 * 24);
    expect(diffDays).toBeGreaterThanOrEqual(60); // at least 2 months
  });
});

describe('content/posts — category coverage', () => {
  test('has posts in 개발 category', () => {
    const categories = POST_FILES.map((f) => readPost(f).data.category);
    expect(categories).toContain('개발');
  });

  test('has posts in 디자인 category', () => {
    const categories = POST_FILES.map((f) => readPost(f).data.category);
    expect(categories).toContain('디자인');
  });

  test('has posts in 회고 category', () => {
    const categories = POST_FILES.map((f) => readPost(f).data.category);
    expect(categories).toContain('회고');
  });
});

describe('content/posts — markdown elements', () => {
  test('at least one post has a code block', () => {
    const hasCode = POST_FILES.some((f) => {
      const { content } = readPost(f);
      return content.includes('```');
    });
    expect(hasCode).toBe(true);
  });

  test('at least one post has a markdown table', () => {
    const hasTable = POST_FILES.some((f) => {
      const { content } = readPost(f);
      return content.includes('| ');
    });
    expect(hasTable).toBe(true);
  });

  test('at least one post has h2 heading', () => {
    const hasH2 = POST_FILES.some((f) => {
      const { content } = readPost(f);
      return /^## /m.test(content);
    });
    expect(hasH2).toBe(true);
  });

  test('at least one post has h3 heading', () => {
    const hasH3 = POST_FILES.some((f) => {
      const { content } = readPost(f);
      return /^### /m.test(content);
    });
    expect(hasH3).toBe(true);
  });
});

describe('content/posts — original_url', () => {
  test('at least one post has original_url', () => {
    const hasOriginalUrl = POST_FILES.some((f) => {
      const { data } = readPost(f);
      return Boolean(data.original_url);
    });
    expect(hasOriginalUrl).toBe(true);
  });
});

describe('content/about.md', () => {
  let parsed;
  beforeAll(() => {
    const raw = fs.readFileSync(ABOUT_FILE, 'utf-8');
    parsed = matter(raw);
  });

  test('file exists', () => {
    expect(fs.existsSync(ABOUT_FILE)).toBe(true);
  });

  test('has title field', () => {
    expect(parsed.data.title).toBeDefined();
  });

  test('has non-empty body content', () => {
    expect(parsed.content.trim().length).toBeGreaterThan(50);
  });
});

describe('public/images/', () => {
  const IMAGES_DIR = path.join(__dirname, '..', 'public', 'images');

  test('images directory exists', () => {
    expect(fs.existsSync(IMAGES_DIR)).toBe(true);
  });

  test('has at least one image file', () => {
    const files = fs.readdirSync(IMAGES_DIR).filter((f) =>
      /\.(png|jpg|jpeg|gif|svg|webp)$/i.test(f)
    );
    expect(files.length).toBeGreaterThan(0);
  });
});
