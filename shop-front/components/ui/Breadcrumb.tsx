import Link from 'next/link';

export interface BreadcrumbItem {
  label: string;
  href: string;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
}

export default function Breadcrumb({ items }: BreadcrumbProps) {
  return (
    <nav aria-label="Breadcrumb">
      <ol className="flex items-center gap-1 text-sm text-[var(--muted)] flex-wrap">
        {items.map((item, index) => {
          const isLast = index === items.length - 1;
          return (
            <li key={item.href} className="flex items-center gap-1">
              {index > 0 && (
                <svg
                  aria-hidden
                  className="h-3 w-3 flex-shrink-0"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              )}
              {isLast ? (
                <span aria-current="page" className="font-medium text-[var(--fg)]">
                  {item.label}
                </span>
              ) : (
                <Link href={item.href} className="hover:text-blue-600 transition-colors">
                  {item.label}
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
