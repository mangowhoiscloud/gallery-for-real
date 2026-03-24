/**
 * Shiki rehype plugin for syntax-highlighted code blocks.
 *
 * Uses dual themes (github-light / github-dark) via CSS custom properties so
 * the light↔dark toggle in Item 9/10 works without a page reload.
 *
 * The highlighter is cached in a module-level singleton so it is created once
 * per Next.js build worker, not once per page.
 */
import { getSingletonHighlighter, type Highlighter } from 'shiki'
import { visit } from 'unist-util-visit'
import type { Plugin } from 'unified'
import type { Root, Element, Text } from 'hast'

// ─── Constants (exported so tests can import without re-declaring) ──────────

export const SUPPORTED_LANGS = [
  'typescript',
  'javascript',
  'tsx',
  'jsx',
  'bash',
  'shell',
  'css',
  'html',
  'json',
  'markdown',
  'python',
  'yaml',
  'text',
] as const

export const LIGHT_THEME = 'github-light' as const
export const DARK_THEME = 'github-dark' as const

// ─── Pure utilities (testable without ESM deps) ─────────────────────────────

/**
 * Extracts a resolved language name from a code element's className array.
 * Falls back to 'text' when the language is absent or unsupported.
 */
export function extractLang(classNames: string[]): string {
  const raw = classNames
    .find((c) => c.startsWith('language-'))
    ?.slice('language-'.length)

  if (!raw) return 'text'
  return (SUPPORTED_LANGS as readonly string[]).includes(raw) ? raw : 'text'
}

/**
 * Concatenates text nodes inside a hast element (handles split text nodes).
 */
export function extractCodeText(
  children: Array<{ type: string; value?: string }>
): string {
  return children
    .filter((c): c is Text => c.type === 'text')
    .map((c) => c.value)
    .join('')
}

// ─── Highlighter singleton ───────────────────────────────────────────────────

let _highlighterPromise: Promise<Highlighter> | null = null

/**
 * Returns the cached Shiki highlighter, creating it once on first call.
 * Exported for use in tests / other lib modules.
 */
export function getOrCreateHighlighter(): Promise<Highlighter> {
  if (!_highlighterPromise) {
    _highlighterPromise = getSingletonHighlighter({
      themes: [LIGHT_THEME, DARK_THEME],
      langs: [...SUPPORTED_LANGS],
    })
  }
  return _highlighterPromise
}

/** Reset the cached singleton (used in tests to isolate state). */
export function resetHighlighterCache(): void {
  _highlighterPromise = null
}

// ─── Rehype plugin ───────────────────────────────────────────────────────────

type NodeEntry = {
  node: Element
  parent: Root | Element
  index: number
}

/**
 * A rehype plugin that replaces every `<pre><code class="language-*">` block
 * with Shiki-highlighted HTML carrying dual-theme CSS custom properties.
 *
 * Usage (next-mdx-remote):
 *   const mdxSource = await serialize(content, {
 *     mdxOptions: { rehypePlugins: [rehypeShiki] }
 *   })
 */
export const rehypeShiki: Plugin<[], Root> = () => {
  return async (tree: Root) => {
    const highlighter = await getOrCreateHighlighter()

    const nodes: NodeEntry[] = []

    visit(tree, 'element', (node: Element, index, parent) => {
      if (node.tagName !== 'pre') return
      if (typeof index !== 'number' || !parent) return

      const firstChild = node.children[0]
      if (!firstChild || firstChild.type !== 'element') return
      if ((firstChild as Element).tagName !== 'code') return

      nodes.push({ node, parent: parent as Root | Element, index })
    })

    // Compute all highlights in parallel, then apply in reverse index order
    // (reverse avoids shifting indices when multiple siblings are replaced).
    const results = await Promise.all(
      nodes.map(async ({ node, parent, index }) => {
        const codeEl = node.children[0] as Element

        const classNames =
          (codeEl.properties?.className as string[] | undefined) ?? []
        const lang = extractLang(classNames)
        const text = extractCodeText(codeEl.children as Array<{ type: string; value?: string }>)

        const hastOut = highlighter.codeToHast(text.trimEnd(), {
          lang,
          themes: {
            light: LIGHT_THEME,
            dark: DARK_THEME,
          },
        })

        const preElement = hastOut.children[0] as Element
        if (preElement && preElement.type === 'element') {
          preElement.properties = { ...(preElement.properties || {}), 'data-lang': lang }
        }
        return { parent, index, replacement: preElement }
      })
    )

    for (const { parent, index, replacement } of results.reverse()) {
      if (replacement) {
        parent.children.splice(index, 1, replacement)
      }
    }
  }
}
