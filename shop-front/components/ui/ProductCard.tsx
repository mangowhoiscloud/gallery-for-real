import Image from 'next/image';
import Link from 'next/link';
import type { Product } from '@/lib/types';

interface ProductCardProps {
  product: Product;
}

function formatPrice(price: number): string {
  return `$${price.toFixed(2)}`;
}

export default function ProductCard({ product }: ProductCardProps) {
  const { id, name, price, imageUrl, category, stockQuantity } = product;

  return (
    <Link
      href={`/products/${id}`}
      className="group block rounded-xl overflow-hidden border border-[var(--border)] hover:shadow-lg transition-all duration-300"
    >
      <div className="relative aspect-square overflow-hidden bg-gray-100 dark:bg-gray-800">
        <Image
          src={imageUrl}
          alt={name}
          fill
          className="object-cover transition-transform duration-300 group-hover:scale-105"
          sizes="(max-width: 640px) 100vw, (max-width: 768px) 50vw, (max-width: 1024px) 33vw, 25vw"
        />
      </div>
      <div className="p-4">
        <span className="inline-block text-xs font-medium px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 mb-2">
          {category}
        </span>
        <h3 className="font-semibold text-base leading-snug line-clamp-2 mb-2">{name}</h3>
        {stockQuantity === 0 ? (
          <span
            data-testid="out-of-stock-badge"
            className="inline-block text-xs font-medium px-2 py-0.5 rounded-full bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
          >
            Out of Stock
          </span>
        ) : stockQuantity <= 5 ? (
          <p className="text-xs text-amber-600 dark:text-amber-400 font-medium">
            Only {stockQuantity} left
          </p>
        ) : null}
        <p className="text-lg font-bold text-blue-600 dark:text-blue-400 mt-2">
          {formatPrice(price)}
        </p>
      </div>
    </Link>
  );
}
