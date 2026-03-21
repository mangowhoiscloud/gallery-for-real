import { Suspense } from 'react';
import CartPage from './CartPage';
import LoadingSkeleton from '@/components/ui/LoadingSkeleton';

export const metadata = { title: 'Shopping Cart' };

export default function Cart() {
  return (
    <Suspense
      fallback={
        <div className="container mx-auto px-4 py-8">
          <LoadingSkeleton count={3} />
        </div>
      }
    >
      <CartPage />
    </Suspense>
  );
}
