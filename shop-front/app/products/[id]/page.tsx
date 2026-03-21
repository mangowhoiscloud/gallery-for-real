import Image from 'next/image';
import { notFound } from 'next/navigation';
import type { Metadata } from 'next';
import { getProductById, searchProducts } from '@/lib/api';
import Breadcrumb from '@/components/ui/Breadcrumb';
import ProductGrid from '@/components/ui/ProductGrid';
import AddToCartButton from './AddToCartButton';

export const dynamic = 'force-dynamic';

interface ProductDetailPageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({
  params,
}: ProductDetailPageProps): Promise<Metadata> {
  const { id } = await params;
  try {
    const product = await getProductById(Number(id));
    return {
      title: `${product.name} | ShopFront`,
      description: product.description.slice(0, 160),
    };
  } catch {
    return { title: 'Product | ShopFront' };
  }
}

export default async function ProductDetailPage({ params }: ProductDetailPageProps) {
  const { id } = await params;

  let product;
  try {
    product = await getProductById(Number(id));
  } catch {
    notFound();
  }

  // Fetch related products (same category, exclude current)
  let relatedProducts: Awaited<ReturnType<typeof searchProducts>>['content'] = [];
  try {
    const page = await searchProducts({ category: product.category, size: 5 });
    relatedProducts = page.content.filter((p) => p.id !== product.id).slice(0, 4);
  } catch {
    // Non-critical — show empty section on failure
  }

  const { name, price, description, imageUrl, category, stockQuantity } = product;
  const formattedPrice = `$${price.toFixed(2)}`;

  const breadcrumbs = [
    { label: 'Home', href: '/' },
    { label: 'Products', href: '/products' },
    { label: name, href: `/products/${id}` },
  ];

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Breadcrumb */}
      <div className="mb-8">
        <Breadcrumb items={breadcrumbs} />
      </div>

      {/* Product Detail */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-12 mb-16">
        {/* Image with hover zoom */}
        <div
          data-testid="product-image-container"
          className="group relative aspect-square rounded-2xl overflow-hidden bg-gray-100 dark:bg-gray-800"
        >
          <Image
            src={imageUrl}
            alt={name}
            fill
            priority
            className="object-cover transition-transform duration-500 group-hover:scale-110"
            sizes="(max-width: 768px) 100vw, 50vw"
          />
        </div>

        {/* Product Info */}
        <div className="flex flex-col gap-6">
          <div>
            <span className="inline-block text-xs font-medium px-3 py-1 rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 mb-3">
              {category}
            </span>
            <h1 className="text-3xl font-bold leading-tight mb-3">{name}</h1>
            <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">
              {formattedPrice}
            </p>
          </div>

          {/* Stock Status */}
          <div>
            {stockQuantity === 0 ? (
              <span
                data-testid="stock-status"
                className="inline-flex items-center gap-1 text-sm font-semibold text-red-600 dark:text-red-400"
              >
                <span className="w-2 h-2 rounded-full bg-red-500 inline-block" />
                Out of Stock
              </span>
            ) : stockQuantity <= 5 ? (
              <span
                data-testid="stock-status"
                className="inline-flex items-center gap-1 text-sm font-semibold text-amber-600 dark:text-amber-400"
              >
                <span className="w-2 h-2 rounded-full bg-amber-500 inline-block" />
                Only {stockQuantity} left in stock
              </span>
            ) : (
              <span
                data-testid="stock-status"
                className="inline-flex items-center gap-1 text-sm font-semibold text-green-600 dark:text-green-400"
              >
                <span className="w-2 h-2 rounded-full bg-green-500 inline-block" />
                In Stock
              </span>
            )}
          </div>

          {/* Description */}
          <p className="text-[var(--muted)] leading-relaxed">{description}</p>

          {/* Rating (decorative) */}
          <div className="flex items-center gap-2">
            <div className="flex gap-0.5" aria-label="5 out of 5 stars">
              {[1, 2, 3, 4, 5].map((star) => (
                <svg
                  key={star}
                  className="w-5 h-5 text-amber-400 fill-current"
                  viewBox="0 0 20 20"
                  aria-hidden="true"
                >
                  <path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z" />
                </svg>
              ))}
            </div>
            <span className="text-sm text-[var(--muted)]">(Rating)</span>
          </div>

          {/* Add to Cart */}
          <AddToCartButton
            productId={product.id}
            productName={name}
            stockQuantity={stockQuantity}
          />
        </div>
      </div>

      {/* Related Products */}
      {relatedProducts.length > 0 && (
        <section aria-label="Related products">
          <h2 className="text-2xl font-bold mb-6">Related Products</h2>
          <ProductGrid products={relatedProducts} />
        </section>
      )}
    </div>
  );
}
