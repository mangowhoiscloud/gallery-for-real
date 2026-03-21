'use client';

import { useState, useEffect, useRef } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { getCart, updateCartItemQuantity, removeCartItem } from '@/lib/api';
import { isAuthenticated } from '@/lib/auth';
import { useToast } from '@/components/ToastProvider';
import type { CartItem, CartResponse } from '@/lib/types';

const SHIPPING_THRESHOLD = 50;
const SHIPPING_COST = 5;

function formatPrice(amount: number): string {
  return `$${amount.toFixed(2)}`;
}

function calcSubtotal(items: CartItem[]): number {
  return items.reduce((sum, item) => sum + item.product.price * item.quantity, 0);
}

interface PendingRemoval {
  item: CartItem;
  timerId: ReturnType<typeof setTimeout>;
  toastId: string;
}

export default function CartPage() {
  const router = useRouter();
  const { toast, dismiss } = useToast();

  const [items, setItems] = useState<CartItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [updatingIds, setUpdatingIds] = useState<Set<number>>(new Set());

  const pendingRemovals = useRef<Map<number, PendingRemoval>>(new Map());

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace('/login?redirect=/cart');
      return;
    }
    getCart()
      .then((cart: CartResponse) => setItems(cart.items))
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, [router]);

  async function handleQuantityChange(itemId: number, newQuantity: number) {
    if (newQuantity < 1) return;
    setUpdatingIds((prev) => new Set(prev).add(itemId));
    try {
      const updated = await updateCartItemQuantity(itemId, newQuantity);
      setItems(updated.items);
    } catch {
      toast({ variant: 'error', title: 'Failed to update quantity' });
    } finally {
      setUpdatingIds((prev) => {
        const next = new Set(prev);
        next.delete(itemId);
        return next;
      });
    }
  }

  function handleRemove(item: CartItem) {
    // Optimistically remove from display
    setItems((prev) => prev.filter((i) => i.id !== item.id));

    // Schedule API removal after 5s (cancelled if undo is clicked)
    const timerId = setTimeout(() => {
      pendingRemovals.current.delete(item.id);
      removeCartItem(item.id).catch(() => {});
    }, 5000);

    const toastId = toast({
      variant: 'info',
      title: `${item.product.name} removed`,
      description: 'Item removed from cart',
      action: {
        label: 'Undo',
        onClick: () => handleUndo(item.id),
      },
    });

    pendingRemovals.current.set(item.id, { item, timerId, toastId });
  }

  function handleUndo(itemId: number) {
    const pending = pendingRemovals.current.get(itemId);
    if (!pending) return;

    clearTimeout(pending.timerId);
    pendingRemovals.current.delete(itemId);
    dismiss(pending.toastId);

    // Restore item to the list
    setItems((prev) => [...prev, pending.item]);
  }

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="animate-pulse space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 bg-gray-200 dark:bg-gray-700 rounded" />
          ))}
        </div>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="container mx-auto px-4 py-16 text-center">
        <div className="text-6xl mb-4" aria-hidden="true">
          🛒
        </div>
        <h1 className="text-2xl font-bold mb-2">Your cart is empty</h1>
        <p className="text-gray-500 mb-6">Add some products to get started.</p>
        <Link
          href="/products"
          className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Start Shopping
        </Link>
      </div>
    );
  }

  const subtotal = calcSubtotal(items);
  const shipping = subtotal > SHIPPING_THRESHOLD ? 0 : SHIPPING_COST;
  const total = subtotal + shipping;

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Shopping Cart</h1>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Cart items */}
        <div className="flex-1 space-y-4">
          {items.map((item) => {
            const isUpdating = updatingIds.has(item.id);
            return (
              <div
                key={item.id}
                className="flex gap-4 p-4 border border-gray-200 dark:border-gray-700 rounded-lg"
              >
                {/* Thumbnail */}
                <div className="relative w-20 h-20 flex-shrink-0">
                  <Image
                    src={item.product.imageUrl || '/placeholder.png'}
                    alt={item.product.name}
                    fill
                    className="object-cover rounded"
                    sizes="80px"
                  />
                </div>

                {/* Product info */}
                <div className="flex-1 min-w-0">
                  <Link
                    href={`/products/${item.product.id}`}
                    className="font-semibold text-gray-900 dark:text-gray-100 hover:text-blue-600 transition-colors line-clamp-2"
                  >
                    {item.product.name}
                  </Link>
                  <p className="text-sm text-gray-500">{item.product.category}</p>
                  <p className="text-sm font-medium mt-1">
                    {formatPrice(item.product.price)} each
                  </p>
                </div>

                {/* Quantity stepper */}
                <div className="flex items-center gap-2">
                  <button
                    aria-label="Decrease quantity"
                    disabled={isUpdating || item.quantity <= 1}
                    onClick={() => handleQuantityChange(item.id, item.quantity - 1)}
                    className="w-8 h-8 flex items-center justify-center border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    −
                  </button>
                  <span className="w-8 text-center font-medium" aria-label="quantity">
                    {item.quantity}
                  </span>
                  <button
                    aria-label="Increase quantity"
                    disabled={isUpdating}
                    onClick={() => handleQuantityChange(item.id, item.quantity + 1)}
                    className="w-8 h-8 flex items-center justify-center border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    +
                  </button>
                </div>

                {/* Line total + remove */}
                <div className="flex flex-col items-end justify-between">
                  <p className="font-bold text-gray-900 dark:text-gray-100">
                    {formatPrice(item.product.price * item.quantity)}
                  </p>
                  <button
                    aria-label={`Remove ${item.product.name}`}
                    onClick={() => handleRemove(item)}
                    className="text-gray-400 hover:text-red-500 transition-colors text-xl leading-none"
                  >
                    ×
                  </button>
                </div>
              </div>
            );
          })}

          <Link
            href="/products"
            className="inline-block text-blue-600 hover:underline mt-2"
          >
            ← Continue Shopping
          </Link>
        </div>

        {/* Order summary */}
        <div className="lg:w-80">
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-6 space-y-3">
            <h2 className="text-xl font-bold">Order Summary</h2>

            <div className="flex justify-between text-gray-600 dark:text-gray-400">
              <span>Subtotal</span>
              <span>{formatPrice(subtotal)}</span>
            </div>

            <div className="flex justify-between text-gray-600 dark:text-gray-400">
              <span>Estimated Shipping</span>
              <span>{shipping === 0 ? 'Free' : formatPrice(shipping)}</span>
            </div>

            {shipping === 0 && (
              <p className="text-xs text-green-600">You qualify for free shipping!</p>
            )}

            <div className="border-t border-gray-200 dark:border-gray-700 pt-3 flex justify-between font-bold text-lg">
              <span>Total</span>
              <span>{formatPrice(total)}</span>
            </div>

            <Link
              href="/checkout"
              className="block w-full text-center bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors mt-2"
            >
              Proceed to Checkout
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
