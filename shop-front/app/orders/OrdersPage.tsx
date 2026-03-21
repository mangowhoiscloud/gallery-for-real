'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { getOrders, cancelOrder } from '@/lib/api';
import { isAuthenticated } from '@/lib/auth';
import { useToast } from '@/components/ToastProvider';
import Pagination from '@/components/ui/Pagination';
import type { Order, OrderStatus, PageResponse } from '@/lib/types';

const STATUS_STYLES: Record<OrderStatus, string> = {
  PENDING: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  CONFIRMED: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  SHIPPED: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
  DELIVERED: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  CANCELLED: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function formatPrice(amount: number): string {
  return `$${amount.toFixed(2)}`;
}

export default function OrdersPage() {
  const router = useRouter();
  const { toast } = useToast();

  const [page, setPage] = useState(0);
  const [pageData, setPageData] = useState<PageResponse<Order> | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [cancellingId, setCancellingId] = useState<number | null>(null);
  const [confirmCancelId, setConfirmCancelId] = useState<number | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace('/login?redirect=/orders');
      return;
    }
    setIsLoading(true);
    getOrders(page, 10)
      .then(setPageData)
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, [page, router]);

  function toggleExpand(orderId: number) {
    setExpandedId((prev) => (prev === orderId ? null : orderId));
  }

  async function handleCancel(orderId: number) {
    setConfirmCancelId(null);
    setCancellingId(orderId);
    try {
      const updated = await cancelOrder(orderId);
      setPageData((prev) =>
        prev
          ? {
              ...prev,
              content: prev.content.map((o) => (o.id === orderId ? updated : o)),
            }
          : prev,
      );
      toast({ variant: 'success', title: 'Order cancelled successfully' });
    } catch {
      toast({ variant: 'error', title: 'Failed to cancel order' });
    } finally {
      setCancellingId(null);
    }
  }

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="animate-pulse space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-gray-200 dark:bg-gray-700 rounded" />
          ))}
        </div>
      </div>
    );
  }

  const orders = pageData?.content ?? [];

  if (orders.length === 0) {
    return (
      <div className="container mx-auto px-4 py-16 text-center">
        <div className="text-6xl mb-4" aria-hidden="true">
          📦
        </div>
        <h1 className="text-2xl font-bold mb-2">No orders yet</h1>
        <p className="text-gray-500 mb-6">When you place an order, it will appear here.</p>
        <Link
          href="/products"
          className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Start Shopping
        </Link>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">My Orders</h1>

      {/* Cancel confirmation dialog */}
      {confirmCancelId !== null && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="cancel-dialog-title"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        >
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-sm w-full mx-4 shadow-xl">
            <h2 id="cancel-dialog-title" className="text-xl font-bold mb-2">
              Cancel Order
            </h2>
            <p className="text-gray-600 dark:text-gray-300 mb-6">
              Are you sure you want to cancel order #{confirmCancelId}? This cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setConfirmCancelId(null)}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                Keep Order
              </button>
              <button
                onClick={() => handleCancel(confirmCancelId)}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Cancel Order
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-4">
        {orders.map((order) => {
          const isExpanded = expandedId === order.id;
          const isCancelling = cancellingId === order.id;

          return (
            <div
              key={order.id}
              className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
            >
              {/* Order header row */}
              <button
                className="w-full flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 p-4 text-left hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                onClick={() => toggleExpand(order.id)}
                aria-expanded={isExpanded}
                aria-controls={`order-details-${order.id}`}
              >
                <div className="flex items-center gap-4 flex-1">
                  <div>
                    <span className="font-semibold text-gray-900 dark:text-gray-100">
                      Order #{order.id}
                    </span>
                    <p className="text-sm text-gray-500">{formatDate(order.createdAt)}</p>
                  </div>
                  <div className="ml-auto sm:ml-0 sm:flex-1 text-right sm:text-left">
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {order.items.length} item{order.items.length !== 1 ? 's' : ''}
                    </p>
                    <p className="font-semibold">{formatPrice(order.totalAmount)}</p>
                  </div>
                </div>
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[order.status]}`}
                  aria-label={`Status: ${order.status}`}
                >
                  {order.status}
                </span>
              </button>

              {/* Expanded details */}
              {isExpanded && (
                <div
                  id={`order-details-${order.id}`}
                  className="border-t border-gray-200 dark:border-gray-700 p-4 bg-gray-50/50 dark:bg-gray-800/30 space-y-4"
                >
                  {/* Items */}
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                      Items
                    </h3>
                    <div className="space-y-1">
                      {order.items.map((item) => (
                        <div key={item.id} className="flex justify-between text-sm">
                          <span className="text-gray-700 dark:text-gray-300">
                            {item.productName} × {item.quantity}
                          </span>
                          <span className="text-gray-900 dark:text-gray-100">
                            {formatPrice(item.price * item.quantity)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Shipping address */}
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
                      Shipping Address
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {order.shippingAddress.name}, {order.shippingAddress.addressLine1},{' '}
                      {order.shippingAddress.city}, {order.shippingAddress.state}{' '}
                      {order.shippingAddress.zipCode}
                    </p>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-3">
                    <Link
                      href={`/orders/${order.id}`}
                      className="text-sm text-blue-600 hover:underline"
                    >
                      View Details →
                    </Link>
                    {order.status === 'PENDING' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setConfirmCancelId(order.id);
                        }}
                        disabled={isCancelling}
                        className="text-sm text-red-600 hover:underline disabled:opacity-50"
                      >
                        {isCancelling ? 'Cancelling...' : 'Cancel Order'}
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Pagination */}
      {pageData && pageData.totalPages > 1 && (
        <div className="mt-8 flex justify-center">
          <Pagination
            currentPage={page}
            totalPages={pageData.totalPages}
            onPageChange={setPage}
          />
        </div>
      )}
    </div>
  );
}
