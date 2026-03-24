import React from 'react'
import { render, screen, act, fireEvent } from '@testing-library/react'
import CodeBlock from '../components/CodeBlock'

// Mock clipboard API
const mockWriteText = jest.fn().mockResolvedValue(undefined)
Object.defineProperty(navigator, 'clipboard', {
  value: { writeText: mockWriteText },
  writable: true,
})

beforeEach(() => {
  mockWriteText.mockClear()
  jest.useFakeTimers()
})

afterEach(() => {
  jest.runOnlyPendingTimers()
  jest.useRealTimers()
})

describe('CodeBlock', () => {
  it('renders language label when lang prop is provided', () => {
    render(<CodeBlock lang="typescript">const x = 1</CodeBlock>)
    expect(screen.getByText('typescript')).toBeInTheDocument()
  })

  it('does not render language label when lang is absent', () => {
    render(<CodeBlock>const x = 1</CodeBlock>)
    expect(screen.queryByTestId('code-lang')).not.toBeInTheDocument()
  })

  it('renders copy button with "Copy" text initially', () => {
    render(<CodeBlock lang="js">const x = 1</CodeBlock>)
    expect(screen.getByRole('button', { name: /copy/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /copy/i })).toHaveTextContent('Copy')
  })

  it('calls navigator.clipboard.writeText with code text on copy click', async () => {
    render(<CodeBlock lang="js">{'const hello = "world"'}</CodeBlock>)
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /copy/i }))
    })
    expect(mockWriteText).toHaveBeenCalledTimes(1)
    expect(mockWriteText).toHaveBeenCalledWith(expect.stringContaining('hello'))
  })

  it('shows "Copied!" text after clicking copy', async () => {
    render(<CodeBlock lang="ts">let y = 2</CodeBlock>)
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /copy/i }))
    })
    expect(screen.getByRole('button')).toHaveTextContent('Copied!')
  })

  it('reverts to "Copy" after 2 seconds', async () => {
    render(<CodeBlock lang="ts">let y = 2</CodeBlock>)
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /copy/i }))
    })
    expect(screen.getByRole('button')).toHaveTextContent('Copied!')
    act(() => { jest.advanceTimersByTime(2000) })
    expect(screen.getByRole('button')).toHaveTextContent('Copy')
  })

  it('renders children inside a pre element', () => {
    render(<CodeBlock lang="bash">echo hello</CodeBlock>)
    const pre = document.querySelector('pre')
    expect(pre).toBeInTheDocument()
    expect(pre?.textContent).toContain('echo hello')
  })

  it('pre element uses monospace font via CSS variable', () => {
    render(<CodeBlock lang="css">{'.foo { color: red }'}</CodeBlock>)
    const pre = document.querySelector('pre')!
    expect(pre.style.fontFamily).toContain('var(--font-mono)')
  })
})
