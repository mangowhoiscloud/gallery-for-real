import React from 'react'
import { metadata } from '@/app/layout'
import RootLayout from '@/app/layout'
import { THEME_SCRIPT } from '@/lib/theme-script'

// jsdom doesn't implement matchMedia — provide a controllable mock
function mockMatchMedia(prefersDark: boolean) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation(() => ({
      matches: prefersDark,
    })),
  })
}

describe('metadata', () => {
  it('has the correct default title', () => {
    const title = metadata.title as { default: string; template: string }
    expect(title.default).toBe('개발 블로그')
  })

  it('title template includes %s placeholder', () => {
    const title = metadata.title as { default: string; template: string }
    expect(title.template).toContain('%s')
  })

  it('has a Korean description mentioning 블로그', () => {
    expect(metadata.description).toContain('블로그')
  })
})

describe('THEME_SCRIPT', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.classList.remove('dark')
    mockMatchMedia(false)
  })

  it('is a non-empty string', () => {
    expect(typeof THEME_SCRIPT).toBe('string')
    expect(THEME_SCRIPT.length).toBeGreaterThan(0)
  })

  it('adds dark class when localStorage theme is "dark"', () => {
    localStorage.setItem('theme', 'dark')
    // eslint-disable-next-line no-eval
    eval(THEME_SCRIPT)
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('does not add dark class when localStorage theme is "light"', () => {
    localStorage.setItem('theme', 'light')
    eval(THEME_SCRIPT) // eslint-disable-line no-eval
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('adds dark class when system prefers dark and localStorage is unset', () => {
    mockMatchMedia(true)
    eval(THEME_SCRIPT) // eslint-disable-line no-eval
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('does not add dark class when system prefers light and localStorage is unset', () => {
    mockMatchMedia(false)
    eval(THEME_SCRIPT) // eslint-disable-line no-eval
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('does not throw when localStorage access throws', () => {
    const originalGetItem = Storage.prototype.getItem
    Storage.prototype.getItem = () => { throw new Error('blocked') }
    expect(() => eval(THEME_SCRIPT)).not.toThrow() // eslint-disable-line no-eval
    Storage.prototype.getItem = originalGetItem
  })
})

describe('RootLayout', () => {
  it('renders with lang="ko"', () => {
    const element = RootLayout({ children: <div>test</div> })
    expect(element.props.lang).toBe('ko')
  })

  it('has suppressHydrationWarning on html element', () => {
    const element = RootLayout({ children: <div>test</div> })
    expect(element.props.suppressHydrationWarning).toBe(true)
  })
})
