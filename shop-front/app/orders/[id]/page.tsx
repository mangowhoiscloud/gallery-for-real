import { Suspense } from 'react';
import OrderDetailPage from './OrderDetailPage';
import LoadingSkeleton from '@/components/ui/LoadingSkeleton';

export const dynamic = 'force-dynamic';

interface Props {
  params: Promise<{ id: string }>;
}

export default async function OrderDetail({ params }: Props) {
  const { id } = await params;
  const orderId = parseInt(id, 10);

  return (
    <Suspense
      fallback={
        <div className="container mx-auto px-4 py-8">
          <LoadingSkeleton count={3} />
        </div>
      }
    >
      <OrderDetailPage orderId={orderId} />
    </Suspense>
  );
}
