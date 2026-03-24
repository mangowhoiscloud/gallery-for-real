/**
 * Tests for lib/shiki.ts — rehype plugin + utility functions.
 *
 * shiki and unist-util-visit are ESM-only packages that cannot be required in
 * Jest's CJS mode.  We mock them with factory functions so Jest never evaluates
 * the actual ESM files.  This lets us test all observable behaviour (language
 * extraction, text extraction, plugin tree transformation) without touching the
 * real Shiki binary.
 */

// ─── Mock ESM packages BEFORE any imports from lib/shiki ────────────────────

// Minimal hast-shaped output that mirrors what Shiki's codeToHast returns.
function makeShikiPre(lang: string, code: string) {
  return {
    type: 'element',
    tagName: 'pre',
    properties: {
      class: `shiki shiki-themes github-light github-dark`,
      style: 'background-color:#fff;--shiki-dark-bg:#24292e',
    },
    children: [
      {
        type: 'element',
        tagName: 'code',
        properties: {},
        children: [
          {
            type: 'element',
            tagName: 'span',
            properties: { class: 'line' },
            children: [{ type: 'text', value: code }],
          },
        ],
      },
    ],
  }
}

const mockHighlighter = {
  codeToHast: jest.fn((code: string, opts: { lang: string }) => ({
    type: 'root',
    children: [makeShikiPre(opts.lang, code)],
  })),
}

jest.mock('shiki', () => ({
  getSingletonHighlighter: jest.fn().mockResolvedValue(mockHighlighter),
}))

// visit mock: synchronously traverse element nodes (depth-first, pre-order)
function mockVisit(tree: any, selector: string, visitor: Function) {
  function traverse(node: any, index: number | undefined, parent: any) {
    if (node.type === selector) {
      visitor(node, index, parent)
    }
    if (node.children) {
      node.children.forEach((child: any, i: number) =>
        traverse(child, i, node)
      )
    }
  }
  traverse(tree, undefined, null)
}

jest.mock('unist-util-visit', () => ({
  visit: jest.fn(mockVisit),
}))

// ─── Now import the module under test ────────────────────────────────────────

import {
  extractLang,
  extractCodeText,
  SUPPORTED_LANGS,
  LIGHT_THEME,
  DARK_THEME,
  rehypeShiki,
  getOrCreateHighlighter,
  resetHighlighterCache,
} from '../lib/shiki'
import type { Root, Element } from 'hast'

// ─── Helper ──────────────────────────────────────────────────────────────────

function makeHastTree(lang: string | null, code: string): Root {
  return {
    type: 'root',
    children: [
      {
        type: 'element',
        tagName: 'pre',
        properties: {},
        children: [
          {
            type: 'element',
            tagName: 'code',
            properties: lang ? { className: [`language-${lang}`] } : {},
            children: [{ type: 'text', value: code }],
          } as Element,
        ],
      } as Element,
    ],
  }
}

// ─── extractLang ─────────────────────────────────────────────────────────────

describe('extractLang', () => {
  it('returns the language from a language- className', () => {
    expect(extractLang(['language-typescript'])).toBe('typescript')
    expect(extractLang(['language-javascript'])).toBe('javascript')
    expect(extractLang(['language-bash'])).toBe('bash')
    expect(extractLang(['language-css'])).toBe('css')
  })

  it('returns "text" when no language- class is present', () => {
    expect(extractLang([])).toBe('text')
    expect(extractLang(['hljs', 'foo'])).toBe('text')
  })

  it('returns "text" for unsupported language', () => {
    expect(extractLang(['language-cobol'])).toBe('text')
    expect(extractLang(['language-brainfuck'])).toBe('text')
  })

  it('accepts all SUPPORTED_LANGS values', () => {
    for (const lang of SUPPORTED_LANGS) {
      expect(extractLang([`language-${lang}`])).toBe(lang)
    }
  })
})

// ─── extractCodeText ──────────────────────────────────────────────────────────

describe('extractCodeText', () => {
  it('concatenates single text node', () => {
    expect(extractCodeText([{ type: 'text', value: 'const x = 1' }])).toBe(
      'const x = 1'
    )
  })

  it('concatenates multiple text nodes', () => {
    const children = [
      { type: 'text', value: 'line 1\n' },
      { type: 'text', value: 'line 2' },
    ]
    expect(extractCodeText(children)).toBe('line 1\nline 2')
  })

  it('ignores non-text nodes', () => {
    const children = [
      { type: 'element', tagName: 'span' },
      { type: 'text', value: 'hello' },
    ]
    expect(extractCodeText(children)).toBe('hello')
  })

  it('returns empty string for no text nodes', () => {
    expect(extractCodeText([])).toBe('')
    expect(extractCodeText([{ type: 'element', tagName: 'span' }])).toBe('')
  })
})

// ─── Constants ────────────────────────────────────────────────────────────────

describe('constants', () => {
  it('LIGHT_THEME is github-light', () => {
    expect(LIGHT_THEME).toBe('github-light')
  })

  it('DARK_THEME is github-dark', () => {
    expect(DARK_THEME).toBe('github-dark')
  })

  it('SUPPORTED_LANGS includes required languages', () => {
    const required = ['typescript', 'javascript', 'bash', 'css']
    for (const lang of required) {
      expect(SUPPORTED_LANGS).toContain(lang)
    }
  })
})

// ─── getOrCreateHighlighter ───────────────────────────────────────────────────

describe('getOrCreateHighlighter', () => {
  beforeEach(() => {
    resetHighlighterCache()
    mockHighlighter.codeToHast.mockClear()
  })

  it('returns a highlighter with codeToHast method', async () => {
    const h = await getOrCreateHighlighter()
    expect(typeof h.codeToHast).toBe('function')
  })

  it('returns the same instance on subsequent calls (cached)', async () => {
    const h1 = await getOrCreateHighlighter()
    const h2 = await getOrCreateHighlighter()
    expect(h1).toBe(h2)
  })
})

// ─── rehypeShiki plugin ───────────────────────────────────────────────────────

describe('rehypeShiki', () => {
  beforeEach(() => {
    resetHighlighterCache()
    mockHighlighter.codeToHast.mockClear()
  })

  it('transforms a TypeScript code block', async () => {
    const tree = makeHastTree('typescript', 'const x: number = 1')
    const transformer = rehypeShiki()
    await transformer(tree, {} as any, () => {})

    const pre = tree.children[0] as Element
    const className = pre.properties?.class as string
    expect(className).toContain('shiki')
    expect(className).toContain('github-light')
    expect(className).toContain('github-dark')
  })

  it('calls codeToHast with correct lang and dual themes', async () => {
    const tree = makeHastTree('javascript', 'console.log("hi")')
    const transformer = rehypeShiki()
    await transformer(tree, {} as any, () => {})

    expect(mockHighlighter.codeToHast).toHaveBeenCalledWith(
      'console.log("hi")',
      expect.objectContaining({
        lang: 'javascript',
        themes: { light: 'github-light', dark: 'github-dark' },
      })
    )
  })

  it('falls back to "text" lang when no language class is present', async () => {
    const tree = makeHastTree(null, 'some plain text')
    const transformer = rehypeShiki()
    await transformer(tree, {} as any, () => {})

    expect(mockHighlighter.codeToHast).toHaveBeenCalledWith(
      'some plain text',
      expect.objectContaining({ lang: 'text' })
    )
  })

  it('falls back to "text" for unsupported language', async () => {
    const tree = makeHastTree('cobol', 'IDENTIFICATION DIVISION.')
    const transformer = rehypeShiki()
    await transformer(tree, {} as any, () => {})

    expect(mockHighlighter.codeToHast).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({ lang: 'text' })
    )
  })

  it('replaces the pre node with Shiki output', async () => {
    const tree = makeHastTree('typescript', 'const x = 1')
    const transformer = rehypeShiki()
    await transformer(tree, {} as any, () => {})

    // Original pre had no class; Shiki output pre has the shiki class
    const pre = tree.children[0] as Element
    expect(pre.properties?.class).toContain('shiki')
  })

  it('trims trailing whitespace before highlighting', async () => {
    const tree = makeHastTree('typescript', 'const x = 1\n\n')
    const transformer = rehypeShiki()
    await transformer(tree, {} as any, () => {})

    expect(mockHighlighter.codeToHast).toHaveBeenCalledWith(
      'const x = 1',
      expect.any(Object)
    )
  })

  it('handles multiple code blocks in the same document', async () => {
    const tree: Root = {
      type: 'root',
      children: [
        {
          type: 'element',
          tagName: 'pre',
          properties: {},
          children: [
            {
              type: 'element',
              tagName: 'code',
              properties: { className: ['language-typescript'] },
              children: [{ type: 'text', value: 'const a = 1' }],
            } as Element,
          ],
        } as Element,
        {
          type: 'element',
          tagName: 'pre',
          properties: {},
          children: [
            {
              type: 'element',
              tagName: 'code',
              properties: { className: ['language-bash'] },
              children: [{ type: 'text', value: 'npm install' }],
            } as Element,
          ],
        } as Element,
      ],
    }

    const transformer = rehypeShiki()
    await transformer(tree, {} as any, () => {})

    expect(mockHighlighter.codeToHast).toHaveBeenCalledTimes(2)
    // Both nodes replaced — each should now carry the shiki class
    const pres = tree.children as Element[]
    for (const pre of pres) {
      expect((pre.properties?.class as string)).toContain('shiki')
    }
  })

  it('does not process elements that are not pre>code', async () => {
    const tree: Root = {
      type: 'root',
      children: [
        {
          type: 'element',
          tagName: 'div',
          properties: {},
          children: [
            {
              type: 'element',
              tagName: 'code',
              properties: { className: ['language-typescript'] },
              children: [{ type: 'text', value: 'inline code' }],
            } as Element,
          ],
        } as Element,
      ],
    }

    const transformer = rehypeShiki()
    await transformer(tree, {} as any, () => {})

    // Should not be called — only pre>code blocks are highlighted
    expect(mockHighlighter.codeToHast).not.toHaveBeenCalled()
  })
})
