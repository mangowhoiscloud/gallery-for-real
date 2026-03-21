import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import OrdersPage from '@/app/orders/OrdersPage';
import { makeOrder, makeOrderItem, makePageResponse } from '@/lib/test-factories';

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
  getOrders: jest.fn(),
  cancelOrder: jest.fn(),
}));

const mockIsAuthenticated = jest.requireMock('@/lib/auth').isAuthenticated as jest.Mock;
const mockGetOrders = jest.requireMock('@/lib/api').getOrders as jest.Mock;
const mockCancelOrder = jest.requireMock('@/lib/api').cancelOrder as jest.Mock;

beforeEach(() => {
  jest.clearAllMocks();
  mockIsAuthenticated.mockReturnValue(true);
});

describe('OrdersPage — auth redirect', () => {
  it('redirects to /login?redirect=/orders when not authenticated', async () => {
    mockIsAuthenticated.mockReturnValue(false);
    render(<OrdersPage />);
    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith('/login?redirect=/orders');
    });
  });
});

describe('OrdersPage — empty state', () => {
  it('shows empty state when no orders', async () => {
    mockGetOrders.mockResolvedValue(makePageResponse([]));
    render(<OrdersPage />);
    expect(await screen.findByText('No orders yet')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Start Shopping' })).toBeInTheDocument();
  });
});

describe('OrdersPage — order list', () => {
  it('renders order rows with ID, item count, and total', async () => {
    const order = makeOrder({
      id: 999,
      totalAmount: 89.97,
      items: [makeOrderItem(), makeOrderItem({ id: 2 })],
    });
    mockGetOrders.mockResolvedValue(makePageResponse([order]));
    render(<OrdersPage />);
    expect(await screen.findByText('Order #999')).toBeInTheDocument();
    expect(screen.getByText('$89.97')).toBeInTheDocument();
    expect(screen.getByText('2 items')).toBeInTheDocument();
  });

  it('shows PENDING status badge with yellow styling', async () => {
    const order = makeOrder({ status: 'PENDING' });
    mockGetOrders.mockResolvedValue(makePageResponse([order]));
    render(<OrdersPage />);
    const badge = await screen.findByLabelText('Status: PENDING');
    expect(badge).toHaveClass('bg-yellow-100');
  });

  it('shows DELIVERED status badge with green styling', async () => {
    const order = makeOrder({ status: 'DELIVERED' });
    mockGetOrders.mockResolvedValue(makePageResponse([order]));
    render(<OrdersPage />);
    const badge = await screen.findByLabelText('Status: DELIVERED');
    expect(badge).toHaveClass('bg-green-100');
  });

  it('shows SHIPPED status badge with purple styling', async () => {
    const order = makeOrder({ status: 'SHIPPED' });
    mockGetOrders.mockResolvedValue(makePageResponse([order]));
    render(<OrdersPage />);
    const badge = await screen.findByLabelText('Status: SHIPPED');
    expect(badge).toHaveClass('bg-purple-100');
  });

  it('expands row on click to reveal items and shipping address', async () => {
    const order = makeOrder({ id: 42 });
    mockGetOrders.mockResolvedValue(makePageResponse([order]));
    render(<OrdersPage />);
    // Wait for data to load, then click the toggle
    await screen.findByText('Order #42');
    fireEvent.click(screen.getByRole('button', { expanded: false }));
    await waitFor(() => {
      expect(screen.getByText('Items')).toBeInTheDocument();
    });
    expect(screen.getByText('Shipping Address')).toBeInTheDocument();
  });

  it('collapses row on second click', async () => {
    const order = makeOrder({ id: 42 });
    mockGetOrders.mockResolvedValue(makePageResponse([order]));
    render(<OrdersPage />);
    await screen.findByText('Order #42');
    // Expand
    fireEvent.click(screen.getByRole('button', { expanded: false }));
    await screen.findByText('Shipping Address');
    // Re-query toggle by expanded:true, then collapse
    fireEvent.click(screen.getByRole('button', { expanded: true }));
    await waitFor(() => {
      expect(screen.queryByText('Shipping Address')).not.toBeInTheDocument();
    });
  });

  it('expanded row shows item names and line totals', async () => {
    const order = makeOrder({
      id: 1001,
      items: [makeOrderItem({ productName: 'Widget Pro', price: 25.0, quantity: 2 })],
    });
    mockGetOrders.mockResolvedValue(makePageResponse([order]));
    render(<OrdersPage />);
    await screen.findByText('Order #1001');
    fireEvent.click(screen.getByRole('button', { expanded: false }));
    await waitFor(() => {
      expect(screen.getByText(/Widget Pro × 2/)).toBeInTheDocument();
    });
    expect(screen.getByText('$50.00')).toBeInTheDocument();
  });

  it('expanded row shows View Details link', async () => {
    const order = makeOrder({ id: 77 });
    mockGetOrders.mockResolvedValue(makePageResponse([order]));
    render(<OrdersPage />);
    await screen.findByText('Order #77');
    fireEvent.click(screen.getByRole('button', { expanded: false }));
    await waitFor(() => {
      expect(screen.getByRole('link', { name: /View Details/i })).toHaveAttribute(
        'href',
        '/orders/77',
      );
    });
  });
});

describe('OrdersPage — cancel flow', () => {
  it('shows Cancel Order button only for PENDING orders when expanded', async () => {
    const order = makeOrder({ id: 1, status: 'PENDING' });
    mockGetOrders.mockResolvedValue(makePageResponse([order]));
    render(<OrdersPage />);
    await screen.findByText('Order #1');
    fireEvent.click(screen.getByRole('button', { expanded: false }));
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Cancel Order' })).toBeInTheDocument();
    });
  });

  it('does not show Cancel Order button for CONFIRMED orders when expanded', async () => {
    const order = makeOrder({ id: 2, status: 'CONFIRMED' });
    mockGetOrders.mockResolvedValue(makePageResponse([order]));
    render(<OrdersPage />);
    await screen.findByText('Order #2');
    fireEvent.click(screen.getByRole('button', { expanded: false }));
    await waitFor(() => {
      expect(screen.getByRole('link', { name: /View Details/ })).toBeInTheDocument();
    });
    expect(screen.queryByRole('button', { name: 'Cancel Order' })).not.toBeInTheDocument();
  });

  it('does not show Cancel Order button for DELIVERED orders when expanded', async () => {
    const order = makeOrder({ id: 3, status: 'DELIVERED' });
    mockGetOrders.mockResolvedValue(makePageResponse([order]));
    render(<OrdersPage />);
    await screen.findByText('Order #3');
    fireEvent.click(screen.getByRole('button', { expanded: false }));
    await waitFor(() => {
      expect(screen.getByRole('link', { name: /View Details/ })).toBeInTheDocument();
    });
    expect(screen.queryByRole('button', { name: 'Cancel Order' })).not.toBeInTheDocument();
  });

  it('opens confirmation dialog when Cancel Order is clicked', async () => {
    const order = makeOrder({ id: 1, status: 'PENDING' });
    mockGetOrders.mockResolvedValue(makePageResponse([order]));
    render(<OrdersPage />);
    await screen.findByText('Order #1');
    fireEvent.click(screen.getByRole('button', { expanded: false }));
    const cancelBtn = await screen.findByRole('button', { name: 'Cancel Order' });
    fireEvent.click(cancelBtn);
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });
    expect(screen.getByText(/Are you sure you want to cancel order/)).toBeInTheDocument();
  });

  it('calls cancelOrder API on confirmation and shows success toast', async () => {
    const order = makeOrder({ id: 1, status: 'PENDING' });
    const cancelled = makeOrder({ id: 1, status: 'CANCELLED' });
    mockGetOrders.mockResolvedValue(makePageResponse([order]));
    mockCancelOrder.mockResolvedValue(cancelled);
    render(<OrdersPage />);
    await screen.findByText('Order #1');
    fireEvent.click(screen.getByRole('button', { expanded: false }));
    const cancelBtn = await screen.findByRole('button', { name: 'Cancel Order' });
    fireEvent.click(cancelBtn); // opens dialog
    const dialog = await screen.findByRole('dialog');
    fireEvent.click(within(dialog).getByRole('button', { name: 'Cancel Order' })); // confirms
    await waitFor(() => {
      expect(mockCancelOrder).toHaveBeenCalledWith(1);
      expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({ variant: 'success' }));
    });
  });

  it('closes dialog when Keep Order is clicked', async () => {
    const order = makeOrder({ id: 1, status: 'PENDING' });
    mockGetOrders.mockResolvedValue(makePageResponse([order]));
    render(<OrdersPage />);
    await screen.findByText('Order #1');
    fireEvent.click(screen.getByRole('button', { expanded: false }));
    const cancelBtn = await screen.findByRole('button', { name: 'Cancel Order' });
    fireEvent.click(cancelBtn);
    await screen.findByRole('dialog');
    fireEvent.click(screen.getByRole('button', { name: 'Keep Order' }));
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });
});

describe('OrdersPage — pagination', () => {
  it('shows pagination when totalPages > 1', async () => {
    const orders = [makeOrder()];
    mockGetOrders.mockResolvedValue(
      makePageResponse(orders, { totalPages: 3, totalElements: 30 }),
    );
    render(<OrdersPage />);
    expect(await screen.findByRole('navigation', { name: 'Pagination' })).toBeInTheDocument();
  });

  it('does not show pagination when totalPages is 1', async () => {
    const orders = [makeOrder()];
    mockGetOrders.mockResolvedValue(makePageResponse(orders, { totalPages: 1 }));
    render(<OrdersPage />);
    await screen.findByText('Order #1001');
    expect(screen.queryByRole('navigation', { name: 'Pagination' })).not.toBeInTheDocument();
  });

  it('calls getOrders with new page number when pagination button is clicked', async () => {
    const orders = [makeOrder()];
    mockGetOrders.mockResolvedValue(
      makePageResponse(orders, { totalPages: 3, totalElements: 30 }),
    );
    render(<OrdersPage />);
    await screen.findByRole('navigation', { name: 'Pagination' });
    fireEvent.click(screen.getByRole('button', { name: 'Page 2' }));
    await waitFor(() => {
      expect(mockGetOrders).toHaveBeenCalledWith(1, 10);
    });
  });
});
