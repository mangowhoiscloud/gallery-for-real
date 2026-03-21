'use client';

import { useState } from 'react';
import { addToCart } from '@/lib/api';
import { useToast } from '@/components/ToastProvider';

interface AddToCartButtonProps {
  productId: number;
  productName: string;
  stockQuantity: number;
}

export default function AddToCartButton({
  productId,
  productName,
  stockQuantity,
}: AddToCartButtonProps) {
  const [quantity, setQuantity] = useState(1);
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const isOutOfStock = stockQuantity === 0;

  function decrement() {
    setQuantity((q) => Math.max(1, q - 1));
  }

  function increment() {
    setQuantity((q) => Math.min(stockQuantity, q + 1));
  }

  async function handleAddToCart() {
    if (isOutOfStock) return;
    setLoading(true);
    try {
      await addToCart(productId, quantity);
      toast({
        variant: 'success',
        title: 'Added to cart',
        description: `${productName} × ${quantity}`,
      });
    } catch {
      toast({
        variant: 'error',
        title: 'Failed to add to cart',
        description: 'Please try again.',
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Quantity Selector */}
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium text-[var(--muted)]">Quantity</span>
        <div className="flex items-center gap-2">
          <button
            aria-label="Decrease quantity"
            onClick={decrement}
            disabled={quantity <= 1 || isOutOfStock}
            className="w-8 h-8 rounded-full border border-[var(--border)] flex items-center justify-center text-lg font-bold hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            −
          </button>
          <input
            aria-label="Quantity"
            type="number"
            min={1}
            max={stockQuantity}
            value={quantity}
            readOnly
            className="w-12 text-center border border-[var(--border)] rounded-md py-1 text-sm font-semibold bg-[var(--bg)]"
          />
          <button
            aria-label="Increase quantity"
            onClick={increment}
            disabled={quantity >= stockQuantity || isOutOfStock}
            className="w-8 h-8 rounded-full border border-[var(--border)] flex items-center justify-center text-lg font-bold hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            +
          </button>
        </div>
      </div>

      {/* Add to Cart Button */}
      <button
        onClick={handleAddToCart}
        disabled={isOutOfStock || loading}
        className="w-full py-3 px-6 rounded-xl font-semibold text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
      >
        {isOutOfStock ? 'Out of Stock' : loading ? 'Adding…' : 'Add to Cart'}
      </button>
    </div>
  );
}
