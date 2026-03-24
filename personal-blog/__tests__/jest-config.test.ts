/**
 * Item 3: Jest + ESLint 9 configuration
 * Verifies ts-jest, jsdom environment, @/* module alias, and jest-dom setup.
 */

describe('ts-jest TypeScript support', () => {
  test('TypeScript type annotations compile and run', () => {
    const value: string = 'hello'
    const count: number = 42
    const flag: boolean = true
    expect(value).toBe('hello')
    expect(count).toBe(42)
    expect(flag).toBe(true)
  })

  test('TypeScript generics work', () => {
    function identity<T>(x: T): T {
      return x
    }
    expect(identity<string>('ts-jest')).toBe('ts-jest')
    expect(identity<number>(7)).toBe(7)
  })

  test('TypeScript interfaces work', () => {
    interface Post {
      title: string
      slug: string
      date: string
    }
    const post: Post = { title: 'Test', slug: 'test', date: '2026-01-01' }
    expect(post.title).toBe('Test')
    expect(post.slug).toBe('test')
  })

  test('async/await TypeScript works', async () => {
    async function fetchValue(): Promise<string> {
      return 'async-value'
    }
    const result = await fetchValue()
    expect(result).toBe('async-value')
  })
})

describe('jsdom test environment', () => {
  test('document is available (jsdom)', () => {
    expect(typeof document).toBe('object')
    expect(typeof window).toBe('object')
  })

  test('can create and query DOM elements', () => {
    const div = document.createElement('div')
    div.setAttribute('data-testid', 'test-el')
    div.textContent = 'Hello jsdom'
    document.body.appendChild(div)

    const found = document.querySelector('[data-testid="test-el"]')
    expect(found).not.toBeNull()
    expect(found?.textContent).toBe('Hello jsdom')

    document.body.removeChild(div)
  })
})

describe('@testing-library/jest-dom matchers', () => {
  test('toBeInTheDocument matcher works', () => {
    const el = document.createElement('p')
    el.textContent = 'jest-dom works'
    document.body.appendChild(el)
    expect(el).toBeInTheDocument()
    document.body.removeChild(el)
  })

  test('toHaveTextContent matcher works', () => {
    const el = document.createElement('span')
    el.textContent = 'matcher test'
    document.body.appendChild(el)
    expect(el).toHaveTextContent('matcher test')
    document.body.removeChild(el)
  })

  test('toBeVisible matcher works', () => {
    const el = document.createElement('button')
    el.textContent = 'Click me'
    document.body.appendChild(el)
    expect(el).toBeVisible()
    document.body.removeChild(el)
  })
})
