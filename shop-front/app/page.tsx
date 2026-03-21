import { Suspense } from 'react';
import { getProducts, searchProducts } from '@/lib/api';
import HeroCarousel from '@/components/HeroCarousel';

// Always render at request time — page shows live product data
export const dynamic = 'force-dynamic';
import CategoryNav, { FALLBACK_CATEGORIES } from '@/components/CategoryNav';
import ProductSection from '@/components/ProductSection';
import LoadingSkeleton from '@/components/ui/LoadingSkeleton';

async function FeaturedHero() {
  const data = await getProducts({ page: 0, size: 5 });
  return <HeroCarousel products={data.content} />;
}

async function Categories() {
  const data = await getProducts({ page: 0, size: 20 });
  const cats = [...new Set(data.content.map((p) => p.category))];
  return <CategoryNav categories={cats.length ? cats : FALLBACK_CATEGORIES} />;
}

async function NewArrivals() {
  const data = await searchProducts({ sortBy: 'createdAt', sortDir: 'desc', page: 0, size: 6 });
  return <ProductSection title="New Arrivals" products={data.content} />;
}

async function BestSellers() {
  const data = await searchProducts({ sortBy: 'price', sortDir: 'desc', page: 0, size: 6 });
  return <ProductSection title="Best Sellers" products={data.content} />;
}

export default function HomePage() {
  return (
    <main className="mx-auto max-w-7xl space-y-12 px-4 py-8">
      <Suspense fallback={<LoadingSkeleton count={3} />}>
        <FeaturedHero />
      </Suspense>

      <section>
        <h2 className="mb-4 text-xl font-semibold text-[var(--color-muted)]">Shop by Category</h2>
        <Suspense
          fallback={
            <div className="flex gap-3">
              {FALLBACK_CATEGORIES.map((c) => (
                <div
                  key={c}
                  className="h-10 w-24 animate-pulse rounded-full bg-[var(--color-border)]"
                />
              ))}
            </div>
          }
        >
          <Categories />
        </Suspense>
      </section>

      <Suspense fallback={<LoadingSkeleton count={6} />}>
        <NewArrivals />
      </Suspense>

      <Suspense fallback={<LoadingSkeleton count={6} />}>
        <BestSellers />
      </Suspense>
    </main>
  );
}
