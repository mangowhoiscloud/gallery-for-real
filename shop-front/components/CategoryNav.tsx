import Link from 'next/link';

export const FALLBACK_CATEGORIES = ['Electronics', 'Clothing', 'Home', 'Books', 'Sports'];

interface Props {
  categories?: string[];
}

export default function CategoryNav({ categories = FALLBACK_CATEGORIES }: Props) {
  return (
    <nav aria-label="Product categories" className="flex gap-3 overflow-x-auto pb-2">
      {categories.map((cat) => (
        <Link
          key={cat}
          href={`/products?category=${encodeURIComponent(cat)}`}
          className="whitespace-nowrap rounded-full border border-[var(--color-border)] px-4 py-2 text-sm font-medium transition-colors hover:border-[var(--color-accent)] hover:bg-[var(--color-accent)] hover:text-white"
        >
          {cat}
        </Link>
      ))}
    </nav>
  );
}
