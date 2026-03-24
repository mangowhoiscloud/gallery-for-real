'use client'

import { useRef, useState } from 'react'

interface CodeBlockProps extends React.HTMLAttributes<HTMLPreElement> {
  children?: React.ReactNode
  lang?: string
  'data-lang'?: string
}

export default function CodeBlock({
  children,
  lang,
  'data-lang': dataLang,
  className,
  style,
  ...rest
}: CodeBlockProps) {
  const [copied, setCopied] = useState(false)
  const preRef = useRef<HTMLPreElement>(null)
  const resolvedLang = lang ?? dataLang

  async function handleCopy() {
    const text = preRef.current?.textContent ?? ''
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // No language detected — render as plain <pre>
  if (!resolvedLang) {
    return (
      <pre className={className} style={style} {...rest}>
        {children}
      </pre>
    )
  }

  return (
    <div
      style={{
        position: 'relative',
        borderRadius: '6px',
        overflow: 'hidden',
        marginBottom: '1.5rem',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '4px 12px',
          backgroundColor: 'var(--code-bg)',
          borderBottom: '1px solid var(--border)',
        }}
      >
        <span
          data-testid="code-lang"
          style={{
            fontSize: '0.75rem',
            color: 'var(--text-muted, #666)',
            fontFamily: 'var(--font-mono)',
          }}
        >
          {resolvedLang}
        </span>
        <button
          onClick={handleCopy}
          aria-label={copied ? 'Copied' : 'Copy code'}
          style={{
            padding: '2px 8px',
            fontSize: '0.75rem',
            border: '1px solid var(--border)',
            borderRadius: '4px',
            backgroundColor: 'transparent',
            color: 'var(--text)',
            cursor: 'pointer',
          }}
        >
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
      <pre
        ref={preRef}
        className={className}
        style={{
          margin: 0,
          padding: '1rem',
          overflowX: 'auto',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.875rem',
          lineHeight: 1.6,
          ...(style || {}),
        }}
        {...rest}
      >
        {children}
      </pre>
    </div>
  )
}
