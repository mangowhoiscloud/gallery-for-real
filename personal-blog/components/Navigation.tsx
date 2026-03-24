'use client';

import Link from 'next/link';
import { useState } from 'react';
import ThemeToggle from './ThemeToggle';

const NAV_LINKS = [
  { href: '/', label: '홈' },
  { href: '/blog', label: '블로그' },
  { href: '/tags', label: '태그' },
  { href: '/about', label: '소개' },
] as const;

function MenuIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <line x1="3" y1="6" x2="21" y2="6" />
      <line x1="3" y1="12" x2="21" y2="12" />
      <line x1="3" y1="18" x2="21" y2="18" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}

export default function Navigation() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <nav
      aria-label="메인 내비게이션"
      style={{
        borderBottom: '1px solid var(--border)',
        background: 'var(--bg)',
        position: 'sticky',
        top: 0,
        zIndex: 50,
      }}
    >
      <div
        style={{
          maxWidth: '720px',
          margin: '0 auto',
          padding: '0 1rem',
          height: '56px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        {/* Site title / logo */}
        <Link
          href="/"
          style={{
            fontWeight: 700,
            fontSize: '1.125rem',
            color: 'var(--text)',
            textDecoration: 'none',
          }}
        >
          개발 블로그
        </Link>

        {/* Desktop links */}
        <div
          data-testid="desktop-nav"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '1.5rem',
          }}
          className="desktop-nav"
        >
          {NAV_LINKS.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              style={{
                color: 'var(--text-muted)',
                textDecoration: 'none',
                fontSize: '0.9375rem',
              }}
            >
              {label}
            </Link>
          ))}
          <ThemeToggle />
        </div>

        {/* Mobile: ThemeToggle + hamburger button */}
        <div
          style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          className="mobile-controls"
        >
          <button
            type="button"
            aria-label={menuOpen ? '메뉴 닫기' : '메뉴 열기'}
            aria-expanded={menuOpen}
            aria-controls="mobile-menu"
            onClick={() => setMenuOpen((prev) => !prev)}
            data-testid="hamburger-button"
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text)',
              padding: '0.25rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {menuOpen ? <CloseIcon /> : <MenuIcon />}
          </button>
        </div>
      </div>

      {/* Mobile menu drawer */}
      {menuOpen && (
        <div
          id="mobile-menu"
          data-testid="mobile-menu"
          style={{
            borderTop: '1px solid var(--border)',
            background: 'var(--bg)',
            padding: '0.75rem 1rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
          }}
        >
          {NAV_LINKS.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              onClick={() => setMenuOpen(false)}
              style={{
                color: 'var(--text-muted)',
                textDecoration: 'none',
                fontSize: '1rem',
                padding: '0.25rem 0',
              }}
            >
              {label}
            </Link>
          ))}
          <ThemeToggle />
        </div>
      )}
    </nav>
  );
}
