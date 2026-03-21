import type { ReactNode } from 'react';
import type { Product } from '@/lib/types';
import ProductCard from './ProductCard';

interface ProductGridProps {
  products?: Product[];
  children?: ReactNode;
  className?: string;
}

export default function ProductGrid({ products, children, className }: ProductGridProps) {
  return (
    <div
      className={`grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 ${className ?? ''}`}
    >
      {products ? products.map((p) => <ProductCard key={p.id} product={p} />) : children}
    </div>
  );
}
