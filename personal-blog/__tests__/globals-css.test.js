const fs = require('fs')
const path = require('path')

const cssPath = path.join(__dirname, '..', 'app', 'globals.css')
const css = fs.readFileSync(cssPath, 'utf8')

describe('globals.css — Tailwind v4 CSS-first configuration', () => {
  test('imports tailwindcss', () => {
    expect(css).toMatch(/@import "tailwindcss"/)
  })

  test('registers @tailwindcss/typography plugin', () => {
    expect(css).toMatch(/@plugin "@tailwindcss\/typography"/)
  })
})

describe('globals.css — CSS custom properties', () => {
  const lightVars = ['--bg', '--bg-secondary', '--text', '--text-muted', '--accent', '--accent-hover', '--border', '--code-bg', '--code-text', '--prose-headings', '--prose-links', '--prose-hr', '--prose-quote-border', '--prose-quote-text']
  const darkVars = [...lightVars]

  test.each(lightVars)(':root defines %s', (varName) => {
    const rootBlock = css.match(/:root\s*\{([^}]+)\}/s)?.[1] ?? ''
    expect(rootBlock).toContain(varName)
  })

  test('.dark class overrides all theme variables', () => {
    const darkBlock = css.match(/\.dark\s*\{([^}]+)\}/s)?.[1] ?? ''
    for (const varName of darkVars) {
      expect(darkBlock).toContain(varName)
    }
  })

  test(':root --bg is white (#ffffff)', () => {
    const rootBlock = css.match(/:root\s*\{([^}]+)\}/s)?.[1] ?? ''
    expect(rootBlock).toContain('--bg: #ffffff')
  })

  test('.dark --bg is dark (#0f0f0f)', () => {
    const darkBlock = css.match(/\.dark\s*\{([^}]+)\}/s)?.[1] ?? ''
    expect(darkBlock).toContain('--bg: #0f0f0f')
  })
})

describe('globals.css — base body styles', () => {
  test('body has background-color using --bg variable', () => {
    expect(css).toMatch(/body\s*\{[^}]*background-color:\s*var\(--bg\)/s)
  })

  test('body has line-height of 1.8', () => {
    expect(css).toMatch(/body\s*\{[^}]*line-height:\s*1\.8/s)
  })

  test('body font-family includes Pretendard', () => {
    expect(css).toMatch(/body\s*\{[^}]*font-family:[^}]*Pretendard/s)
  })
})

describe('globals.css — prose typography', () => {
  test('.prose max-width is 680px', () => {
    expect(css).toMatch(/\.prose\s*\{[^}]*max-width:\s*680px/s)
  })

  test('.prose line-height is 1.8', () => {
    expect(css).toMatch(/\.prose\s*\{[^}]*line-height:\s*1\.8/s)
  })

  test('.prose has heading color using --prose-headings variable', () => {
    expect(css).toContain('--prose-headings')
    expect(css).toMatch(/color:\s*var\(--prose-headings\)/)
  })

  test('.prose blockquote uses --prose-quote-border variable', () => {
    expect(css).toMatch(/border-left:[^;]*var\(--prose-quote-border\)/)
  })

  test('.prose pre has overflow-x: auto (scrollable code blocks)', () => {
    expect(css).toContain('overflow-x: auto')
  })

  test('.prose table has border-collapse: collapse', () => {
    expect(css).toContain('border-collapse: collapse')
  })
})
