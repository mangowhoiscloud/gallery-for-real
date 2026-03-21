'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { getOrderById, cancelOrder } from '@/lib/api';
import { isAuthenticated } from '@/lib/auth';
import { useToast } from '@/components/ToastProvider';
import type { Order, OrderStatus } from '@/lib/types';

const STATUS_STYLES: Record<OrderStatus, string> = {
  PENDING: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  CONFIRMED: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  SHIPPED: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
  DELIVERED: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  CANCELLED: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
};

const FLOW_STEPS: OrderStatus[] = ['PENDING', 'CONFIRMED', 'SHIPPED', 'DELIVERED'];

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatPrice(amount: number): string {
  return `$${amount.toFixed(2)}`;
}

function StatusStepper({ status }: { status: OrderStatus }) {
  if (status === 'CANCELLED') {
    return (
      <div className="flex items-center gap-3 py-2">
        <span className="px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300">
          CANCELLED
        </span>
        <span className="text-sm text-gray-500">This order has been cancelled.</span>
      </div>
    );
  }

  const currentIdx = FLOW_STEPS.indexOf(status);

  return (
    <ol className="flex items-center w-full" aria-label="Order status steps">
      {FLOW_STEPS.map((step, idx) => {
        const isDone = idx < currentIdx;
        const isCurrent = idx === currentIdx;

        return (
          <li key={step} className="flex items-center flex-1 last:flex-none">
            <div className="flex flex-col items-center">
              <div
                aria-current={isCurrent ? 'step' : undefined}
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  isDone
                    ? 'bg-green-500 text-white'
                    : isCurrent
                      ? 'bg-blue-600 text-white ring-2 ring-blue-300'
                      : 'bg-gray-200 text-gray-400 dark:bg-gray-700'
                }`}
              >
                {isDone ? '✓' : idx + 1}
              </div>
              <span
                className={`mt-1 text-xs font-medium ${
                  isCurrent
                    ? 'text-blue-600 dark:text-blue-400'
                    : isDone
                      ? 'text-green-600 dark:text-green-400'
                      : 'text-gray-400'
                }`}
              >
                {step}
              </span>
            </div>
            {idx < FLOW_STEPS.length - 1 && (
              <div
                className={`flex-1 h-0.5 mx-2 mb-5 ${
                  isDone ? 'bg-green-500' : 'bg-gray-200 dark:bg-gray-700'
                }`}
              />
            )}
          </li>
        );
      })}
    </ol>
  );
}

interface Props {
  orderId: number;
}

export default function OrderDetailPage({ orderId }: Props) {
  const router = useRouter();
  const { toast } = useToast();

  const [order, setOrder] = useState<Order | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isCancelling, setIsCancelling] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace(`/login?redirect=/orders/${orderId}`);
      return;
    }
    getOrderById(orderId)
      .then(setOrder)
      .catch(() => router.replace('/orders'))
      .finally(() => setIsLoading(false));
  }, [orderId, router]);

  async function handleCancel() {
    if (!order) return;
    setShowConfirm(false);
    setIsCancelling(true);
    try {
      const updated = await cancelOrder(order.id);
      setOrder(updated);
      toast({ variant: 'success', title: 'Order cancelled successfully' });
    } catch {
      toast({ variant: 'error', title: 'Failed to cancel order' });
    } finally {
      setIsCancelling(false);
    }
  }

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-48" />
          <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded" />
          <div className="h-48 bg-gray-200 dark:bg-gray-700 rounded" />
        </div>
      </div>
    );
  }

  if (!order) return null;

  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link href="/" className="hover:text-blue-600">
          Home
        </Link>
        <span>›</span>
        <Link href="/orders" className="hover:text-blue-600">
          Orders
        </Link>
        <span>›</span>
        <span className="text-gray-900 dark:text-gray-100">Order #{order.id}</span>
      </nav>

      <div className="flex items-center justify-between mb-2">
        <h1 className="text-3xl font-bold">Order #{order.id}</h1>
        <span
          className={`px-3 py-1 rounded-full text-sm font-medium ${STATUS_STYLES[order.status]}`}
          aria-label={`Status: ${order.status}`}
        >
          {order.status}
        </span>
      </div>

      <p className="text-sm text-gray-500 mb-8">Placed on {formatDate(order.createdAt)}</p>

      {/* Status stepper */}
      <div className="mb-8 p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
        <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">
          Order Status
        </h2>
        <StatusStepper status={order.status} />
      </div>

      {/* Items */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold mb-4">Items Ordered</h2>
        <div className="space-y-3">
          {order.items.map((item) => (
            <div
              key={item.id}
              className="flex justify-between items-center p-3 border border-gray-200 dark:border-gray-700 rounded-lg"
            >
              <div>
                <p className="font-medium text-gray-900 dark:text-gray-100">{item.productName}</p>
                <p className="text-sm text-gray-500">
                  {formatPrice(item.price)} × {item.quantity}
                </p>
              </div>
              <p className="font-semibold">{formatPrice(item.price * item.quantity)}</p>
            </div>
          ))}
        </div>
        <div className="mt-4 text-right">
          <p className="text-lg font-bold">Total: {formatPrice(order.totalAmount)}</p>
        </div>
      </div>

      {/* Shipping address */}
      <div className="mb-8 p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
        <h2 className="text-lg font-semibold mb-2">Shipping Address</h2>
        <address className="not-italic text-sm text-gray-600 dark:text-gray-400 space-y-0.5">
          <p>{order.shippingAddress.name}</p>
          <p>{order.shippingAddress.addressLine1}</p>
          {order.shippingAddress.addressLine2 && (
            <p>{order.shippingAddress.addressLine2}</p>
          )}
          <p>
            {order.shippingAddress.city}, {order.shippingAddress.state}{' '}
            {order.shippingAddress.zipCode}
          </p>
          <p>{order.shippingAddress.country}</p>
        </address>
      </div>

      {/* Cancel confirmation dialog */}
      {showConfirm && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="cancel-detail-dialog-title"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        >
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-sm w-full mx-4 shadow-xl">
            <h2 id="cancel-detail-dialog-title" className="text-xl font-bold mb-2">
              Cancel Order
            </h2>
            <p className="text-gray-600 dark:text-gray-300 mb-6">
              Are you sure you want to cancel this order? This cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowConfirm(false)}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                Keep Order
              </button>
              <button
                onClick={handleCancel}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Cancel Order
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-4">
        <Link
          href="/orders"
          className="px-6 py-3 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        >
          ← Back to Orders
        </Link>
        {order.status === 'PENDING' && (
          <button
            onClick={() => setShowConfirm(true)}
            disabled={isCancelling}
            className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
          >
            {isCancelling ? 'Cancelling...' : 'Cancel Order'}
          </button>
        )}
      </div>
    </div>
  );
}
