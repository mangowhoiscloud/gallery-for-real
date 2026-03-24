'use client';

import { useState, useEffect } from 'react';
import type { Heading } from '@/lib/markdown';

interface TableOfContentsProps {
  headings: Heading[];
}

export default function TableOfContents({ headings }: TableOfContentsProps) {
  const [activeId, setActiveId] = useState<string>('');
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    if (headings.length === 0) return;

    const elements = headings
      .map(h => document.getElementById(h.id))
      .filter((el): el is HTMLElement => el !== null);

    if (elements.length === 0) return;

    const observer = new IntersectionObserver(
      entries => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id);
            break;
          }
        }
      },
      { rootMargin: '0px 0px -80% 0px', threshold: 0 },
    );

    elements.forEach(el => observer.observe(el));
    return () => observer.disconnect();
  }, [headings]);

  if (headings.length === 0) return null;

  const tocList = (
    <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
      {headings.map(heading => (
        <li
          key={heading.id}
          style={heading.level === 3 ? { paddingLeft: '1rem' } : undefined}
        >
          <a
            href={`#${heading.id}`}
            aria-current={activeId === heading.id ? 'location' : undefined}
            style={{
              display: 'block',
              padding: '0.25rem 0',
              color: activeId === heading.id ? 'var(--accent)' : 'inherit',
              textDecoration: 'none',
              fontSize: '0.875rem',
            }}
          >
            {heading.text}
          </a>
        </li>
      ))}
    </ul>
  );

  return (
    <nav aria-label="Table of contents">
      {/* Mobile: expandable via toggle button */}
      <div className="lg:hidden">
        <button
          onClick={() => setIsOpen(prev => !prev)}
          aria-expanded={isOpen}
          style={{ cursor: 'pointer', marginBottom: '0.5rem' }}
        >
          {isOpen ? '목차 닫기' : '목차 열기'}
        </button>
        {isOpen && tocList}
      </div>

      {/* Desktop: always visible, sticky */}
      <div
        className="hidden lg:block"
        data-testid="toc-desktop"
        style={{ position: 'sticky', top: '5rem' }}
      >
        {tocList}
      </div>
    </nav>
  );
}
