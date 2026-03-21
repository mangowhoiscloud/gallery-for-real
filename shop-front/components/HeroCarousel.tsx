'use client';

import { useState, useEffect, useCallback } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import type { Product } from '@/lib/types';

interface Props {
  products: Product[];
}

export default function HeroCarousel({ products }: Props) {
  const [current, setCurrent] = useState(0);
  const [paused, setPaused] = useState(false);
  const count = products.length;

  const next = useCallback(() => setCurrent((i) => (i + 1) % count), [count]);
  const prev = useCallback(() => setCurrent((i) => (i - 1 + count) % count), [count]);

  useEffect(() => {
    if (paused || count <= 1) return;
    const id = setInterval(next, 5000);
    return () => clearInterval(id);
  }, [paused, next, count]);

  if (count === 0) return null;

  const product = products[current];

  return (
    <div
      data-testid="hero-carousel"
      className="relative overflow-hidden rounded-2xl bg-[var(--color-primary)] text-white"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      <Link href={`/products/${product.id}`} className="block" data-testid="hero-slide-link">
        <div className="relative h-96 w-full">
          <Image
            src={product.imageUrl}
            alt={product.name}
            fill
            className="object-cover opacity-60"
          />
          <div className="absolute inset-0 flex flex-col items-start justify-end p-8">
            <span className="mb-2 rounded-full bg-[var(--color-accent)] px-3 py-1 text-sm font-medium">
              {product.category}
            </span>
            <h2 className="mb-2 text-3xl font-bold">{product.name}</h2>
            <p className="mb-4 max-w-md text-lg opacity-90">
              {product.description.length > 100
                ? `${product.description.slice(0, 100)}...`
                : product.description}
            </p>
            <span className="text-2xl font-bold">${product.price.toFixed(2)}</span>
          </div>
        </div>
      </Link>

      <button
        onClick={prev}
        aria-label="Previous slide"
        className="absolute left-4 top-1/2 -translate-y-1/2 rounded-full bg-white/20 p-2 backdrop-blur-sm hover:bg-white/40"
      >
        <ChevronLeft className="h-6 w-6" />
      </button>
      <button
        onClick={next}
        aria-label="Next slide"
        className="absolute right-4 top-1/2 -translate-y-1/2 rounded-full bg-white/20 p-2 backdrop-blur-sm hover:bg-white/40"
      >
        <ChevronRight className="h-6 w-6" />
      </button>

      <div className="absolute bottom-4 left-1/2 flex -translate-x-1/2 gap-2">
        {products.map((_, i) => (
          <button
            key={i}
            onClick={() => setCurrent(i)}
            aria-label={`Go to slide ${i + 1}`}
            aria-current={i === current ? 'true' : undefined}
            className={`h-2 rounded-full transition-all ${
              i === current ? 'w-6 bg-white' : 'w-2 bg-white/50'
            }`}
          />
        ))}
      </div>
    </div>
  );
}
