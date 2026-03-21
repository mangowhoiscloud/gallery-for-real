import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import OrderDetailPage from '@/app/orders/[id]/OrderDetailPage';
import { makeOrder, makeOrderItem, makeShippingAddress } from '@/lib/test-factories';

const mockReplace = jest.fn();
const mockPush = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace }),
}));

const mockToast = jest.fn();

jest.mock('@/components/ToastProvider', () => ({
  useToast: () => ({ toast: mockToast, dismiss: jest.fn(), toasts: [] }),
}));

jest.mock('@/lib/auth', () => ({
  isAuthenticated: jest.fn(),
}));

jest.mock('@/lib/api', () => ({
  getOrderById: jest.fn(),
  cancelOrder: jest.fn(),
}));

const mockIsAuthenticated = jest.requireMock('@/lib/auth').isAuthenticated as jest.Mock;
const mockGetOrderById = jest.requireMock('@/lib/api').getOrderById as jest.Mock;
const mockCancelOrder = jest.requireMock('@/lib/api').cancelOrder as jest.Mock;

/** Wait for the order detail page to finish loading by checking for the heading */
async function waitForOrderLoad(id: number) {
  // Use findAllByText since the ID appears in both heading and breadcrumb
  await screen.findAllByText(`Order #${id}`);
}

beforeEach(() => {
  jest.clearAllMocks();
  mockIsAuthenticated.mockReturnValue(true);
});

describe('OrderDetailPage — auth redirect', () => {
  it('redirects to /login?redirect=/orders/{id} when not authenticated', async () => {
    mockIsAuthenticated.mockReturnValue(false);
    render(<OrderDetailPage orderId={42} />);
    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith('/login?redirect=/orders/42');
    });
  });
});

describe('OrderDetailPage — order info', () => {
  it('renders order ID (in heading and breadcrumb) and total amount', async () => {
    const order = makeOrder({ id: 500, totalAmount: 75.5 });
    mockGetOrderById.mockResolvedValue(order);
    render(<OrderDetailPage orderId={500} />);
    const headings = await screen.findAllByText('Order #500');
    expect(headings.length).toBeGreaterThanOrEqual(1);
    // Total appears as "Total: $75.50" in a paragraph
    expect(screen.getByText(/\$75\.50/)).toBeInTheDocument();
  });

  it('renders item list with product names and line totals', async () => {
    // Use a totalAmount different from the line total to avoid duplicate matches
    const order = makeOrder({
      items: [makeOrderItem({ productName: 'Gadget Plus', price: 19.99, quantity: 3 })],
      totalAmount: 64.97, // 59.97 line + 5.00 shipping
    });
    mockGetOrderById.mockResolvedValue(order);
    render(<OrderDetailPage orderId={1001} />);
    expect(await screen.findByText('Gadget Plus')).toBeInTheDocument();
    // Line total = 19.99 × 3 = 59.97 (unique, different from totalAmount)
    expect(screen.getByText(/\$59\.97/)).toBeInTheDocument();
    // Order total shown separately
    expect(screen.getByText(/\$64\.97/)).toBeInTheDocument();
  });

  it('renders shipping address', async () => {
    const order = makeOrder({
      shippingAddress: makeShippingAddress({
        name: 'Jane Doe',
        addressLine1: '456 Elm St',
        city: 'Springfield',
        state: 'IL',
        zipCode: '62701',
        country: 'US',
      }),
    });
    mockGetOrderById.mockResolvedValue(order);
    render(<OrderDetailPage orderId={1001} />);
    expect(await screen.findByText('Jane Doe')).toBeInTheDocument();
    expect(screen.getByText('456 Elm St')).toBeInTheDocument();
    expect(screen.getByText(/Springfield, IL 62701/)).toBeInTheDocument();
  });

  it('renders status badge', async () => {
    const order = makeOrder({ status: 'CONFIRMED' });
    mockGetOrderById.mockResolvedValue(order);
    render(<OrderDetailPage orderId={1001} />);
    const badge = await screen.findByLabelText('Status: CONFIRMED');
    expect(badge).toHaveClass('bg-blue-100');
  });
});

describe('OrderDetailPage — status stepper', () => {
  it('marks the current step with aria-current="step"', async () => {
    const order = makeOrder({ status: 'SHIPPED' });
    mockGetOrderById.mockResolvedValue(order);
    const { container } = render(<OrderDetailPage orderId={1001} />);
    await waitForOrderLoad(1001);
    const activeStep = container.querySelector('[aria-current="step"]');
    expect(activeStep).toBeInTheDocument();
  });

  it('shows CANCELLED message instead of stepper for cancelled orders', async () => {
    const order = makeOrder({ status: 'CANCELLED' });
    mockGetOrderById.mockResolvedValue(order);
    render(<OrderDetailPage orderId={1001} />);
    await waitForOrderLoad(1001);
    expect(screen.getByText('This order has been cancelled.')).toBeInTheDocument();
  });
});

describe('OrderDetailPage — cancel', () => {
  it('shows Cancel Order button for PENDING orders', async () => {
    const order = makeOrder({ status: 'PENDING' });
    mockGetOrderById.mockResolvedValue(order);
    render(<OrderDetailPage orderId={1001} />);
    expect(await screen.findByRole('button', { name: 'Cancel Order' })).toBeInTheDocument();
  });

  it('does not show Cancel Order button for DELIVERED orders', async () => {
    const order = makeOrder({ status: 'DELIVERED' });
    mockGetOrderById.mockResolvedValue(order);
    render(<OrderDetailPage orderId={1001} />);
    await waitForOrderLoad(1001);
    expect(screen.queryByRole('button', { name: 'Cancel Order' })).not.toBeInTheDocument();
  });

  it('opens confirmation dialog when Cancel Order button is clicked', async () => {
    const order = makeOrder({ status: 'PENDING' });
    mockGetOrderById.mockResolvedValue(order);
    render(<OrderDetailPage orderId={1001} />);
    fireEvent.click(await screen.findByRole('button', { name: 'Cancel Order' }));
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });
    expect(screen.getByText(/This cannot be undone/)).toBeInTheDocument();
  });

  it('calls cancelOrder API on confirmation and shows success toast', async () => {
    const order = makeOrder({ id: 1001, status: 'PENDING' });
    const cancelled = makeOrder({ id: 1001, status: 'CANCELLED' });
    mockGetOrderById.mockResolvedValue(order);
    mockCancelOrder.mockResolvedValue(cancelled);
    render(<OrderDetailPage orderId={1001} />);
    fireEvent.click(await screen.findByRole('button', { name: 'Cancel Order' }));
    const dialog = await screen.findByRole('dialog');
    fireEvent.click(within(dialog).getByRole('button', { name: 'Cancel Order' }));
    await waitFor(() => {
      expect(mockCancelOrder).toHaveBeenCalledWith(1001);
      expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({ variant: 'success' }));
    });
  });

  it('closes dialog when Keep Order is clicked', async () => {
    const order = makeOrder({ status: 'PENDING' });
    mockGetOrderById.mockResolvedValue(order);
    render(<OrderDetailPage orderId={1001} />);
    fireEvent.click(await screen.findByRole('button', { name: 'Cancel Order' }));
    await screen.findByRole('dialog');
    fireEvent.click(screen.getByRole('button', { name: 'Keep Order' }));
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });
});
