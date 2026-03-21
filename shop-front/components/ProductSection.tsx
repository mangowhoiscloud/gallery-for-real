import type { Product } from '@/lib/types';
import ProductGrid from '@/components/ui/ProductGrid';

interface Props {
  title: string;
  products: Product[];
}

export default function ProductSection({ title, products }: Props) {
  return (
    <section>
      <h2 className="mb-6 text-2xl font-bold">{title}</h2>
      <ProductGrid products={products} />
    </section>
  );
}
