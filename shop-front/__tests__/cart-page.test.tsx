import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import CartPage from '@/app/cart/CartPage';
import {
  makeCartItem,
  makeProduct,
  makeCartResponse,
} from '@/lib/test-factories';

const mockReplace = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn(), replace: mockReplace }),
}));

const mockToast = jest.fn(() => 'toast-id-1');
const mockDismiss = jest.fn();

jest.mock('@/components/ToastProvider', () => ({
  useToast: () => ({ toast: mockToast, dismiss: mockDismiss, toasts: [] }),
}));

jest.mock('@/lib/auth', () => ({
  isAuthenticated: jest.fn(),
}));

jest.mock('@/lib/api', () => ({
  getCart: jest.fn(),
  updateCartItemQuantity: jest.fn(),
  removeCartItem: jest.fn(),
}));

const mockIsAuthenticated = jest.requireMock('@/lib/auth')
  .isAuthenticated as jest.Mock;
const mockGetCart = jest.requireMock('@/lib/api').getCart as jest.Mock;
const mockUpdateCartItemQuantity = jest.requireMock('@/lib/api')
  .updateCartItemQuantity as jest.Mock;
const mockRemoveCartItem = jest.requireMock('@/lib/api')
  .removeCartItem as jest.Mock;

beforeEach(() => {
  jest.clearAllMocks();
  jest.useFakeTimers();
});

afterEach(() => {
  jest.useRealTimers();
});

describe('CartPage — auth redirect', () => {
  it('redirects to /login?redirect=/cart when not authenticated', async () => {
    mockIsAuthenticated.mockReturnValue(false);
    render(<CartPage />);
    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith('/login?redirect=/cart');
    });
  });
});

describe('CartPage — empty state', () => {
  beforeEach(() => {
    mockIsAuthenticated.mockReturnValue(true);
  });

  it('renders empty cart state when there are no items', async () => {
    mockGetCart.mockResolvedValue(makeCartResponse({ items: [] }));
    render(<CartPage />);
    await waitFor(() =>
      expect(screen.getByText('Your cart is empty')).toBeInTheDocument(),
    );
    expect(
      screen.getByRole('link', { name: /start shopping/i }),
    ).toHaveAttribute('href', '/products');
  });
});

describe('CartPage — item rendering', () => {
  beforeEach(() => {
    mockIsAuthenticated.mockReturnValue(true);
  });

  it('renders cart items with product name, category, and unit price', async () => {
    const product = makeProduct({
      id: 42,
      name: 'Wireless Headphones',
      price: 49.99,
      category: 'Electronics',
    });
    const item = makeCartItem({ id: 1, product, quantity: 2 });
    mockGetCart.mockResolvedValue(makeCartResponse({ items: [item] }));

    render(<CartPage />);
    await waitFor(() =>
      expect(screen.getByText('Wireless Headphones')).toBeInTheDocument(),
    );
    expect(screen.getByText('Electronics')).toBeInTheDocument();
    expect(screen.getByText('$49.99 each')).toBeInTheDocument();
    // Line total: 49.99 × 2 = $99.98
    expect(screen.getAllByText('$99.98').length).toBeGreaterThanOrEqual(1);
  });

  it('product name links to the product detail page', async () => {
    const product = makeProduct({ id: 7, name: 'Gaming Mouse' });
    const item = makeCartItem({ id: 1, product });
    mockGetCart.mockResolvedValue(makeCartResponse({ items: [item] }));

    render(<CartPage />);
    await waitFor(() =>
      expect(screen.getByText('Gaming Mouse')).toBeInTheDocument(),
    );
    expect(screen.getByRole('link', { name: 'Gaming Mouse' })).toHaveAttribute(
      'href',
      '/products/7',
    );
  });

  it('renders continue shopping link to /products', async () => {
    const item = makeCartItem({ id: 1 });
    mockGetCart.mockResolvedValue(makeCartResponse({ items: [item] }));

    render(<CartPage />);
    await waitFor(() =>
      expect(
        screen.getByRole('link', { name: /continue shopping/i }),
      ).toBeInTheDocument(),
    );
    expect(
      screen.getByRole('link', { name: /continue shopping/i }),
    ).toHaveAttribute('href', '/products');
  });

  it('renders checkout button linking to /checkout', async () => {
    const item = makeCartItem({ id: 1 });
    mockGetCart.mockResolvedValue(makeCartResponse({ items: [item] }));

    render(<CartPage />);
    await waitFor(() =>
      expect(
        screen.getByRole('link', { name: /proceed to checkout/i }),
      ).toBeInTheDocument(),
    );
    expect(
      screen.getByRole('link', { name: /proceed to checkout/i }),
    ).toHaveAttribute('href', '/checkout');
  });
});

describe('CartPage — quantity stepper', () => {
  beforeEach(() => {
    mockIsAuthenticated.mockReturnValue(true);
  });

  it('calls updateCartItemQuantity with decreased quantity', async () => {
    const item = makeCartItem({ id: 5, quantity: 3 });
    mockGetCart.mockResolvedValue(makeCartResponse({ items: [item] }));
    mockUpdateCartItemQuantity.mockResolvedValue(
      makeCartResponse({ items: [{ ...item, quantity: 2 }] }),
    );

    render(<CartPage />);
    await waitFor(() =>
      expect(screen.getByLabelText('Decrease quantity')).toBeInTheDocument(),
    );

    fireEvent.click(screen.getByLabelText('Decrease quantity'));
    await waitFor(() =>
      expect(mockUpdateCartItemQuantity).toHaveBeenCalledWith(5, 2),
    );
  });

  it('calls updateCartItemQuantity with increased quantity', async () => {
    const item = makeCartItem({ id: 5, quantity: 2 });
    mockGetCart.mockResolvedValue(makeCartResponse({ items: [item] }));
    mockUpdateCartItemQuantity.mockResolvedValue(
      makeCartResponse({ items: [{ ...item, quantity: 3 }] }),
    );

    render(<CartPage />);
    await waitFor(() =>
      expect(screen.getByLabelText('Increase quantity')).toBeInTheDocument(),
    );

    fireEvent.click(screen.getByLabelText('Increase quantity'));
    await waitFor(() =>
      expect(mockUpdateCartItemQuantity).toHaveBeenCalledWith(5, 3),
    );
  });

  it('disables decrease button when quantity is 1', async () => {
    const item = makeCartItem({ id: 1, quantity: 1 });
    mockGetCart.mockResolvedValue(makeCartResponse({ items: [item] }));

    render(<CartPage />);
    await waitFor(() =>
      expect(screen.getByLabelText('Decrease quantity')).toBeDisabled(),
    );
  });
});

describe('CartPage — remove with undo', () => {
  beforeEach(() => {
    mockIsAuthenticated.mockReturnValue(true);
  });

  it('immediately removes item from display when remove is clicked', async () => {
    const product = makeProduct({ name: 'Mechanical Keyboard' });
    const item = makeCartItem({ id: 3, product });
    mockGetCart.mockResolvedValue(makeCartResponse({ items: [item] }));

    render(<CartPage />);
    await waitFor(() =>
      expect(screen.getByText('Mechanical Keyboard')).toBeInTheDocument(),
    );

    fireEvent.click(screen.getByLabelText('Remove Mechanical Keyboard'));
    expect(screen.queryByText('Mechanical Keyboard')).not.toBeInTheDocument();
  });

  it('shows undo toast with correct title when remove is clicked', async () => {
    const product = makeProduct({ name: 'Laptop Stand' });
    const item = makeCartItem({ id: 8, product });
    mockGetCart.mockResolvedValue(makeCartResponse({ items: [item] }));

    render(<CartPage />);
    await waitFor(() =>
      expect(screen.getByLabelText('Remove Laptop Stand')).toBeInTheDocument(),
    );

    fireEvent.click(screen.getByLabelText('Remove Laptop Stand'));
    expect(mockToast).toHaveBeenCalledWith(
      expect.objectContaining({
        variant: 'info',
        title: expect.stringContaining('Laptop Stand'),
        action: expect.objectContaining({ label: 'Undo' }),
      }),
    );
  });

  it('restores item when undo action is triggered', async () => {
    const product = makeProduct({ name: 'USB Hub' });
    const item = makeCartItem({ id: 11, product });
    mockGetCart.mockResolvedValue(makeCartResponse({ items: [item] }));

    render(<CartPage />);
    await waitFor(() =>
      expect(screen.getByText('USB Hub')).toBeInTheDocument(),
    );

    fireEvent.click(screen.getByLabelText('Remove USB Hub'));
    expect(screen.queryByText('USB Hub')).not.toBeInTheDocument();

    // Retrieve and call the undo action from the toast call
    const toastOptions = mockToast.mock.calls[0][0] as {
      action: { onClick: () => void };
    };
    act(() => {
      toastOptions.action.onClick();
    });

    expect(screen.getByText('USB Hub')).toBeInTheDocument();
  });

  it('calls removeCartItem after 5 second timeout', async () => {
    const item = makeCartItem({ id: 9 });
    mockGetCart.mockResolvedValue(makeCartResponse({ items: [item] }));
    mockRemoveCartItem.mockResolvedValue(undefined);

    render(<CartPage />);
    await waitFor(() =>
      expect(
        screen.getByLabelText(`Remove ${item.product.name}`),
      ).toBeInTheDocument(),
    );

    fireEvent.click(screen.getByLabelText(`Remove ${item.product.name}`));
    expect(mockRemoveCartItem).not.toHaveBeenCalled();

    act(() => {
      jest.advanceTimersByTime(5000);
    });
    expect(mockRemoveCartItem).toHaveBeenCalledWith(9);
  });

  it('does not call removeCartItem when undo is clicked before timeout', async () => {
    const item = makeCartItem({ id: 13 });
    mockGetCart.mockResolvedValue(makeCartResponse({ items: [item] }));
    mockRemoveCartItem.mockResolvedValue(undefined);

    render(<CartPage />);
    await waitFor(() =>
      expect(
        screen.getByLabelText(`Remove ${item.product.name}`),
      ).toBeInTheDocument(),
    );

    fireEvent.click(screen.getByLabelText(`Remove ${item.product.name}`));

    // Undo before timeout
    const toastOptions = mockToast.mock.calls[0][0] as {
      action: { onClick: () => void };
    };
    act(() => {
      toastOptions.action.onClick();
    });

    // Advance past the timeout — removal should NOT be called
    act(() => {
      jest.advanceTimersByTime(5000);
    });
    expect(mockRemoveCartItem).not.toHaveBeenCalled();
  });
});

describe('CartPage — order summary calculations', () => {
  beforeEach(() => {
    mockIsAuthenticated.mockReturnValue(true);
  });

  it('calculates subtotal, $5 shipping, and total when below free shipping threshold', async () => {
    const p1 = makeProduct({ id: 1, price: 10.0 });
    const p2 = makeProduct({ id: 2, price: 20.0 });
    const items = [
      makeCartItem({ id: 1, product: p1, quantity: 2 }), // $20
      makeCartItem({ id: 2, product: p2, quantity: 1 }), // $20
    ];
    mockGetCart.mockResolvedValue(makeCartResponse({ items }));

    render(<CartPage />);
    await waitFor(() =>
      expect(screen.getByText('Order Summary')).toBeInTheDocument(),
    );

    // Subtotal $40.00, shipping $5.00, total $45.00
    expect(screen.getByText('$40.00')).toBeInTheDocument();
    expect(screen.getByText('$5.00')).toBeInTheDocument();
    expect(screen.getByText('$45.00')).toBeInTheDocument();
  });

  it('shows free shipping when subtotal exceeds $50', async () => {
    const p = makeProduct({ id: 1, price: 60.0 });
    const item = makeCartItem({ id: 1, product: p, quantity: 1 });
    mockGetCart.mockResolvedValue(makeCartResponse({ items: [item] }));

    render(<CartPage />);
    await waitFor(() =>
      expect(screen.getByText('Order Summary')).toBeInTheDocument(),
    );

    expect(screen.getByText('Free')).toBeInTheDocument();
    expect(
      screen.queryByText('$5.00'),
    ).not.toBeInTheDocument();
  });

  it('gives free shipping at exactly $50.01', async () => {
    const p = makeProduct({ id: 1, price: 50.01 });
    const item = makeCartItem({ id: 1, product: p, quantity: 1 });
    mockGetCart.mockResolvedValue(makeCartResponse({ items: [item] }));

    render(<CartPage />);
    await waitFor(() =>
      expect(screen.getByText('Free')).toBeInTheDocument(),
    );
  });

  it('charges $5 shipping at exactly $50', async () => {
    const p = makeProduct({ id: 1, price: 25.0 });
    const item = makeCartItem({ id: 1, product: p, quantity: 2 }); // $50
    mockGetCart.mockResolvedValue(makeCartResponse({ items: [item] }));

    render(<CartPage />);
    await waitFor(() =>
      expect(screen.getByText('Order Summary')).toBeInTheDocument(),
    );

    // subtotal $50, not strictly > 50, so shipping = $5
    expect(screen.getByText('$5.00')).toBeInTheDocument();
  });
});
