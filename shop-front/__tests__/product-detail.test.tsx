import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import AddToCartButton from '@/app/products/[id]/AddToCartButton';
import { makeProduct, makeCartResponse } from '@/lib/test-factories';

jest.mock('@/lib/api', () => ({
  addToCart: jest.fn(),
}));

jest.mock('@/components/ToastProvider', () => ({
  useToast: jest.fn(),
}));

import { addToCart } from '@/lib/api';
import { useToast } from '@/components/ToastProvider';

const mockAddToCart = addToCart as jest.Mock;
const mockUseToast = useToast as jest.Mock;

describe('AddToCartButton', () => {
  const mockToast = jest.fn();
  const product = makeProduct({ id: 5, name: 'Cool Widget', stockQuantity: 10 });

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseToast.mockReturnValue({ toast: mockToast });
    mockAddToCart.mockResolvedValue(makeCartResponse());
  });

  function renderButton(overrides: Partial<ReturnType<typeof makeProduct>> = {}) {
    const p = { ...product, ...overrides };
    return render(
      <AddToCartButton
        productId={p.id}
        productName={p.name}
        stockQuantity={p.stockQuantity}
      />,
    );
  }

  // ── Quantity Selector ────────────────────────────────────────

  it('renders quantity input starting at 1', () => {
    renderButton();
    expect(screen.getByLabelText('Quantity')).toHaveValue(1);
  });

  it('decrement button is disabled when quantity is 1', () => {
    renderButton();
    expect(screen.getByLabelText('Decrease quantity')).toBeDisabled();
  });

  it('increment button is disabled when quantity equals stockQuantity', () => {
    renderButton({ stockQuantity: 3 });
    const inc = screen.getByLabelText('Increase quantity');
    fireEvent.click(inc); // qty=2
    fireEvent.click(inc); // qty=3
    expect(inc).toBeDisabled();
  });

  it('clicking increment increases displayed quantity', () => {
    renderButton();
    fireEvent.click(screen.getByLabelText('Increase quantity'));
    expect(screen.getByLabelText('Quantity')).toHaveValue(2);
  });

  it('clicking decrement after increment restores quantity to 1', () => {
    renderButton();
    fireEvent.click(screen.getByLabelText('Increase quantity'));
    fireEvent.click(screen.getByLabelText('Decrease quantity'));
    expect(screen.getByLabelText('Quantity')).toHaveValue(1);
  });

  // ── Add to Cart ──────────────────────────────────────────────

  it('calls addToCart with correct productId and quantity on click', async () => {
    renderButton();
    fireEvent.click(screen.getByLabelText('Increase quantity')); // qty=2
    fireEvent.click(screen.getByRole('button', { name: /add to cart/i }));
    await waitFor(() => expect(mockAddToCart).toHaveBeenCalledWith(5, 2));
  });

  it('shows success toast after successful add to cart', async () => {
    renderButton();
    fireEvent.click(screen.getByRole('button', { name: /add to cart/i }));
    await waitFor(() =>
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: 'success' }),
      ),
    );
  });

  it('shows error toast when add to cart fails', async () => {
    mockAddToCart.mockRejectedValue(new Error('Network error'));
    renderButton();
    fireEvent.click(screen.getByRole('button', { name: /add to cart/i }));
    await waitFor(() =>
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: 'error' }),
      ),
    );
  });

  // ── Out of Stock ─────────────────────────────────────────────

  it('shows "Out of Stock" text on button when stockQuantity is 0', () => {
    renderButton({ stockQuantity: 0 });
    expect(screen.getByRole('button', { name: /out of stock/i })).toBeInTheDocument();
  });

  it('disables add to cart button when stockQuantity is 0', () => {
    renderButton({ stockQuantity: 0 });
    expect(screen.getByRole('button', { name: /out of stock/i })).toBeDisabled();
  });

  it('disables increment and decrement buttons when out of stock', () => {
    renderButton({ stockQuantity: 0 });
    expect(screen.getByLabelText('Decrease quantity')).toBeDisabled();
    expect(screen.getByLabelText('Increase quantity')).toBeDisabled();
  });

  it('does not call addToCart when out of stock button is clicked', async () => {
    renderButton({ stockQuantity: 0 });
    // Button is disabled — click event will not fire; verify via no API call
    fireEvent.click(screen.getByRole('button', { name: /out of stock/i }));
    await act(async () => {
      await Promise.resolve();
    });
    expect(mockAddToCart).not.toHaveBeenCalled();
  });
});
