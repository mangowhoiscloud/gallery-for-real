import { Suspense } from 'react';
import OrdersPage from './OrdersPage';
import LoadingSkeleton from '@/components/ui/LoadingSkeleton';

export const metadata = { title: 'My Orders' };

export default function Orders() {
  return (
    <Suspense
      fallback={
        <div className="container mx-auto px-4 py-8">
          <LoadingSkeleton count={3} />
        </div>
      }
    >
      <OrdersPage />
    </Suspense>
  );
}
