import { Suspense } from 'react';
import ProductListing from './ProductListing';
import LoadingSkeleton from '@/components/ui/LoadingSkeleton';

export const dynamic = 'force-dynamic';

export default function ProductsPage() {
  return (
    <Suspense fallback={<LoadingSkeleton count={12} />}>
      <ProductListing />
    </Suspense>
  );
}
