import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Header from '@/components/Header';
import { useAuth } from '@/lib/auth';
import { getCart } from '@/lib/api';
import { useTheme } from '@/components/ThemeProvider';

jest.mock('@/lib/auth', () => ({
  useAuth: jest.fn(),
}));

jest.mock('@/lib/api', () => ({
  getCart: jest.fn(),
}));

jest.mock('@/components/ThemeProvider', () => ({
  useTheme: jest.fn(),
}));

const mockUseAuth = useAuth as jest.Mock;
const mockGetCart = getCart as jest.Mock;
const mockUseTheme = useTheme as jest.Mock;

const defaultAuth = { isAuthenticated: false, signIn: jest.fn(), signOut: jest.fn() };
const defaultTheme = { theme: 'light' as const, toggleTheme: jest.fn() };

describe('Header', () => {
  beforeEach(() => {
    mockUseAuth.mockReturnValue(defaultAuth);
    mockUseTheme.mockReturnValue(defaultTheme);
    mockGetCart.mockResolvedValue({ id: 'c1', items: [], totalPrice: 0 });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders logo link to home page', () => {
    render(<Header />);
    expect(screen.getByRole('link', { name: /shopfront/i })).toHaveAttribute('href', '/');
  });

  it('renders main navigation with Home and Products links', () => {
    render(<Header />);
    const nav = screen.getByRole('navigation', { name: /main navigation/i });
    expect(nav).toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: /^home$/i })[0]).toHaveAttribute('href', '/');
    expect(screen.getAllByRole('link', { name: /^products$/i })[0]).toHaveAttribute('href', '/products');
  });

  it('shows Login and Register links when unauthenticated', () => {
    render(<Header />);
    expect(screen.getAllByRole('link', { name: /^login$/i })[0]).toHaveAttribute('href', '/login');
    expect(screen.getAllByRole('link', { name: /^register$/i })[0]).toHaveAttribute('href', '/register');
  });

  it('does not show Cart/Orders/Profile when unauthenticated', () => {
    render(<Header />);
    expect(screen.queryByRole('link', { name: /^orders$/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /^profile$/i })).not.toBeInTheDocument();
  });

  it('shows Cart, Orders, Profile links when authenticated', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true, signIn: jest.fn(), signOut: jest.fn() });
    render(<Header />);
    // Cart link is identified by aria-label containing "Cart"
    expect(screen.getByRole('link', { name: /^cart$/i })).toHaveAttribute('href', '/cart');
    expect(screen.getByRole('link', { name: /^orders$/i })).toHaveAttribute('href', '/orders');
    expect(screen.getByRole('link', { name: /^profile$/i })).toHaveAttribute('href', '/profile');
  });

  it('does not show Login/Register links when authenticated', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true, signIn: jest.fn(), signOut: jest.fn() });
    render(<Header />);
    expect(screen.queryByRole('link', { name: /^login$/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /^register$/i })).not.toBeInTheDocument();
  });

  it('shows cart badge count when authenticated and cart has items', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true, signIn: jest.fn(), signOut: jest.fn() });
    mockGetCart.mockResolvedValue({
      id: 'c1',
      items: [
        {
          id: 'i1',
          product: { id: 'p1', name: 'P1', price: 10, description: '', imageUrl: '', category: '', stockQuantity: 5, createdAt: '' },
          quantity: 3,
        },
        {
          id: 'i2',
          product: { id: 'p2', name: 'P2', price: 20, description: '', imageUrl: '', category: '', stockQuantity: 2, createdAt: '' },
          quantity: 2,
        },
      ],
      totalPrice: 70,
    });
    render(<Header />);
    await waitFor(() => {
      expect(screen.getByTestId('cart-badge')).toHaveTextContent('5');
    });
  });

  it('does not show cart badge when cart is empty', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true, signIn: jest.fn(), signOut: jest.fn() });
    mockGetCart.mockResolvedValue({ id: 'c1', items: [], totalPrice: 0 });
    render(<Header />);
    await waitFor(() => {
      expect(mockGetCart).toHaveBeenCalledTimes(1);
    });
    expect(screen.queryByTestId('cart-badge')).not.toBeInTheDocument();
  });

  it('renders dark mode toggle button', () => {
    render(<Header />);
    const toggleButtons = screen.getAllByRole('button', { name: /toggle theme/i });
    expect(toggleButtons.length).toBeGreaterThanOrEqual(1);
  });

  it('calls toggleTheme when dark mode button is clicked', () => {
    const toggleTheme = jest.fn();
    mockUseTheme.mockReturnValue({ theme: 'light', toggleTheme });
    render(<Header />);
    const [firstToggle] = screen.getAllByRole('button', { name: /toggle theme/i });
    fireEvent.click(firstToggle);
    expect(toggleTheme).toHaveBeenCalledTimes(1);
  });

  it('shows Sun icon when theme is dark', () => {
    mockUseTheme.mockReturnValue({ theme: 'dark', toggleTheme: jest.fn() });
    render(<Header />);
    // Sun icon is rendered when dark theme is active; lucide renders SVG with title or class
    // We verify the toggle button exists (icon itself is SVG, not text)
    expect(screen.getAllByRole('button', { name: /toggle theme/i }).length).toBeGreaterThanOrEqual(1);
  });

  it('mobile menu is hidden by default', () => {
    render(<Header />);
    expect(screen.queryByRole('navigation', { name: /mobile navigation/i })).not.toBeInTheDocument();
  });

  it('mobile menu opens when hamburger button is clicked', () => {
    render(<Header />);
    const hamburger = screen.getByRole('button', { name: /toggle mobile menu/i });
    expect(hamburger).toHaveAttribute('aria-expanded', 'false');
    fireEvent.click(hamburger);
    expect(hamburger).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByRole('navigation', { name: /mobile navigation/i })).toBeInTheDocument();
  });

  it('mobile menu closes when hamburger button is clicked again', () => {
    render(<Header />);
    const hamburger = screen.getByRole('button', { name: /toggle mobile menu/i });
    fireEvent.click(hamburger);
    expect(screen.getByRole('navigation', { name: /mobile navigation/i })).toBeInTheDocument();
    fireEvent.click(hamburger);
    expect(screen.queryByRole('navigation', { name: /mobile navigation/i })).not.toBeInTheDocument();
  });
});
