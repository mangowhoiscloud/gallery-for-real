import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import CheckoutForm from '@/app/checkout/CheckoutForm';
import {
  makeMember,
  makeCartItem,
  makeCartResponse,
  makeProduct,
  makeOrder,
} from '@/lib/test-factories';

const mockPush = jest.fn();
const mockReplace = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace }),
}));

const mockToast = jest.fn();

jest.mock('@/components/ToastProvider', () => ({
  useToast: () => ({ toast: mockToast }),
}));

jest.mock('@/lib/auth', () => ({
  isAuthenticated: jest.fn(),
}));

jest.mock('@/lib/api', () => ({
  getCart: jest.fn(),
  getProfile: jest.fn(),
  createOrder: jest.fn(),
  clearCart: jest.fn(),
}));

const mockIsAuthenticated = jest.requireMock('@/lib/auth')
  .isAuthenticated as jest.Mock;
const mockGetCart = jest.requireMock('@/lib/api').getCart as jest.Mock;
const mockGetProfile = jest.requireMock('@/lib/api').getProfile as jest.Mock;
const mockCreateOrder = jest.requireMock('@/lib/api').createOrder as jest.Mock;
const mockClearCart = jest.requireMock('@/lib/api').clearCart as jest.Mock;

beforeEach(() => {
  jest.clearAllMocks();
});

/** Render with authenticated user, a non-empty cart, and a profile. */
function renderAuthenticated(
  cartItems = [makeCartItem()],
  profile = makeMember({ name: '', address: '' }),
) {
  mockIsAuthenticated.mockReturnValue(true);
  mockGetCart.mockResolvedValue(makeCartResponse({ items: cartItems }));
  mockGetProfile.mockResolvedValue(profile);
  render(<CheckoutForm />);
}

/** Wait for the form to appear after async data loading. */
async function waitForForm() {
  await waitFor(() =>
    expect(screen.getByRole('button', { name: /place order/i })).toBeInTheDocument(),
  );
}

/** Fill in all required address fields. */
function fillRequiredFields(overrides: Partial<Record<string, string>> = {}) {
  const vals = {
    name: 'John Doe',
    addressLine1: '123 Main St',
    city: 'Springfield',
    state: 'IL',
    zipCode: '62701',
    country: 'US',
    ...overrides,
  };

  if (vals.name !== undefined) {
    const nameInput = screen.getByLabelText(/full name/i);
    fireEvent.change(nameInput, { target: { value: vals.name } });
  }
  fireEvent.change(screen.getByLabelText('Address Line 1'), {
    target: { value: vals.addressLine1 },
  });
  fireEvent.change(screen.getByLabelText(/city/i), {
    target: { value: vals.city },
  });
  fireEvent.change(screen.getByLabelText(/^state/i), {
    target: { value: vals.state },
  });
  fireEvent.change(screen.getByLabelText(/zip code/i), {
    target: { value: vals.zipCode },
  });
  // Country defaults to 'US' — skip unless overriding
  if (overrides.country !== undefined) {
    fireEvent.change(screen.getByLabelText(/country/i), {
      target: { value: vals.country },
    });
  }
}

// ──────────────────────────────────────────────────────────────
describe('CheckoutForm — auth redirect', () => {
  it('redirects to /login?redirect=/checkout when not authenticated', async () => {
    mockIsAuthenticated.mockReturnValue(false);
    render(<CheckoutForm />);
    await waitFor(() =>
      expect(mockReplace).toHaveBeenCalledWith('/login?redirect=/checkout'),
    );
  });
});

// ──────────────────────────────────────────────────────────────
describe('CheckoutForm — empty cart redirect', () => {
  it('redirects to /cart when cart is empty', async () => {
    mockIsAuthenticated.mockReturnValue(true);
    mockGetCart.mockResolvedValue(makeCartResponse({ items: [] }));
    mockGetProfile.mockResolvedValue(makeMember());
    render(<CheckoutForm />);
    await waitFor(() =>
      expect(mockReplace).toHaveBeenCalledWith('/cart'),
    );
  });
});

// ──────────────────────────────────────────────────────────────
describe('CheckoutForm — form pre-fill from profile', () => {
  it('pre-fills name from profile', async () => {
    renderAuthenticated(
      [makeCartItem()],
      makeMember({ name: 'Jane Smith', address: undefined }),
    );
    await waitForForm();
    expect((screen.getByLabelText(/full name/i) as HTMLInputElement).value).toBe(
      'Jane Smith',
    );
  });

  it('pre-fills address line 1 from profile address', async () => {
    renderAuthenticated(
      [makeCartItem()],
      makeMember({ name: 'Jane Smith', address: '456 Oak Ave' }),
    );
    await waitForForm();
    expect(
      (screen.getByLabelText('Address Line 1') as HTMLInputElement).value,
    ).toBe('456 Oak Ave');
  });

  it('defaults country to US', async () => {
    renderAuthenticated();
    await waitForForm();
    expect(
      (screen.getByLabelText(/country/i) as HTMLInputElement).value,
    ).toBe('US');
  });
});

// ──────────────────────────────────────────────────────────────
describe('CheckoutForm — validation', () => {
  it('shows error when address line 1 is empty', async () => {
    renderAuthenticated();
    await waitForForm();
    fillRequiredFields({ addressLine1: '' });
    fireEvent.submit(screen.getByRole('button', { name: /place order/i }).closest('form')!);
    await waitFor(() =>
      expect(screen.getByRole('alert')).toBeInTheDocument(),
    );
    expect(mockCreateOrder).not.toHaveBeenCalled();
  });

  it('shows error when city is empty', async () => {
    renderAuthenticated();
    await waitForForm();
    fillRequiredFields({ city: '' });
    fireEvent.submit(screen.getByRole('button', { name: /place order/i }).closest('form')!);
    await waitFor(() =>
      expect(screen.getAllByRole('alert').length).toBeGreaterThanOrEqual(1),
    );
    expect(mockCreateOrder).not.toHaveBeenCalled();
  });

  it('shows error when state is empty', async () => {
    renderAuthenticated();
    await waitForForm();
    fillRequiredFields({ state: '' });
    fireEvent.submit(screen.getByRole('button', { name: /place order/i }).closest('form')!);
    await waitFor(() =>
      expect(screen.getAllByRole('alert').length).toBeGreaterThanOrEqual(1),
    );
    expect(mockCreateOrder).not.toHaveBeenCalled();
  });

  it('shows error when zip code is empty', async () => {
    renderAuthenticated();
    await waitForForm();
    fillRequiredFields({ zipCode: '' });
    fireEvent.submit(screen.getByRole('button', { name: /place order/i }).closest('form')!);
    await waitFor(() =>
      expect(screen.getAllByRole('alert').length).toBeGreaterThanOrEqual(1),
    );
    expect(mockCreateOrder).not.toHaveBeenCalled();
  });
});

// ──────────────────────────────────────────────────────────────
describe('CheckoutForm — order placement', () => {
  it('calls createOrder with correct shipping address', async () => {
    mockCreateOrder.mockResolvedValue(makeOrder({ id: 500 }));
    mockClearCart.mockResolvedValue(undefined);
    renderAuthenticated();
    await waitForForm();
    fillRequiredFields();
    fireEvent.click(screen.getByRole('button', { name: /place order/i }));
    await waitFor(() => expect(mockCreateOrder).toHaveBeenCalledTimes(1));
    expect(mockCreateOrder).toHaveBeenCalledWith({
      shippingAddress: {
        name: 'John Doe',
        addressLine1: '123 Main St',
        city: 'Springfield',
        state: 'IL',
        zipCode: '62701',
        country: 'US',
      },
    });
  });

  it('calls clearCart after successful order', async () => {
    mockCreateOrder.mockResolvedValue(makeOrder({ id: 501 }));
    mockClearCart.mockResolvedValue(undefined);
    renderAuthenticated();
    await waitForForm();
    fillRequiredFields();
    fireEvent.click(screen.getByRole('button', { name: /place order/i }));
    await waitFor(() => expect(mockClearCart).toHaveBeenCalled());
  });

  it('redirects to /orders/{id} on success', async () => {
    mockCreateOrder.mockResolvedValue(makeOrder({ id: 999 }));
    mockClearCart.mockResolvedValue(undefined);
    renderAuthenticated();
    await waitForForm();
    fillRequiredFields();
    fireEvent.click(screen.getByRole('button', { name: /place order/i }));
    await waitFor(() => expect(mockPush).toHaveBeenCalledWith('/orders/999'));
  });

  it('shows loading state on button during submission', async () => {
    let resolveOrder!: (v: ReturnType<typeof makeOrder>) => void;
    mockCreateOrder.mockImplementation(
      () => new Promise((res) => { resolveOrder = res; }),
    );
    mockClearCart.mockResolvedValue(undefined);
    renderAuthenticated();
    await waitForForm();
    fillRequiredFields();
    fireEvent.click(screen.getByRole('button', { name: /place order/i }));
    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: /placing order/i }),
      ).toBeDisabled(),
    );
    // Clean up: resolve the promise so component can unmount cleanly
    resolveOrder(makeOrder({ id: 1 }));
  });

  it('shows error toast when createOrder fails', async () => {
    mockCreateOrder.mockRejectedValue(new Error('Network error'));
    renderAuthenticated();
    await waitForForm();
    fillRequiredFields();
    fireEvent.click(screen.getByRole('button', { name: /place order/i }));
    await waitFor(() =>
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: 'error' }),
      ),
    );
    expect(mockPush).not.toHaveBeenCalled();
  });
});

// ──────────────────────────────────────────────────────────────
describe('CheckoutForm — order summary', () => {
  it('renders cart item names and line totals in order summary', async () => {
    const product = makeProduct({ name: 'USB Keyboard', price: 45.0 });
    const item = makeCartItem({ id: 1, product, quantity: 2 });
    renderAuthenticated([item]);
    await waitForForm();
    expect(screen.getByText(/USB Keyboard/)).toBeInTheDocument();
    // Line total: 45 × 2 = $90.00 (may also appear as subtotal/total)
    expect(screen.getAllByText('$90.00').length).toBeGreaterThanOrEqual(1);
  });

  it('calculates subtotal, $5 shipping, and total below free-shipping threshold', async () => {
    const product = makeProduct({ id: 1, price: 20.0 });
    const item = makeCartItem({ id: 1, product, quantity: 2 }); // $40 subtotal
    renderAuthenticated([item]);
    await waitForForm();
    // subtotal $40, shipping $5, total $45
    expect(screen.getAllByText('$40.00').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('$5.00')).toBeInTheDocument();
    expect(screen.getByText('$45.00')).toBeInTheDocument();
  });

  it('shows Free shipping when subtotal exceeds $50', async () => {
    const product = makeProduct({ id: 1, price: 60.0 });
    const item = makeCartItem({ id: 1, product, quantity: 1 }); // $60 subtotal
    renderAuthenticated([item]);
    await waitForForm();
    expect(screen.getByText('Free')).toBeInTheDocument();
  });
});
