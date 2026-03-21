'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { Menu, Moon, ShoppingCart, Sun, X } from 'lucide-react';
import { useAuth } from '@/lib/auth';
import { getCart } from '@/lib/api';
import { useTheme } from '@/components/ThemeProvider';

export default function Header() {
  const { isAuthenticated } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [cartCount, setCartCount] = useState(0);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      setCartCount(0);
      return;
    }
    getCart()
      .then((cart) => {
        setCartCount(cart.items.reduce((sum, item) => sum + item.quantity, 0));
      })
      .catch(() => setCartCount(0));
  }, [isAuthenticated]);

  return (
    <header className="sticky top-0 z-50 border-b border-[var(--border)] bg-[var(--bg)]">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
        {/* Logo */}
        <Link href="/" className="text-xl font-bold text-[var(--color-accent)]">
          ShopFront
        </Link>

        {/* Desktop nav */}
        <nav aria-label="Main navigation" className="hidden items-center gap-6 md:flex">
          <Link href="/" className="hover:text-[var(--color-accent)]">
            Home
          </Link>
          <Link href="/products" className="hover:text-[var(--color-accent)]">
            Products
          </Link>
        </nav>

        {/* Desktop auth + theme */}
        <div className="hidden items-center gap-3 md:flex">
          {isAuthenticated ? (
            <>
              <Link
                href="/cart"
                aria-label={`Cart${cartCount > 0 ? ` (${cartCount} items)` : ''}`}
                className="relative flex items-center gap-1 hover:text-[var(--color-accent)]"
              >
                <ShoppingCart size={20} />
                <span>Cart</span>
                {cartCount > 0 && (
                  <span
                    data-testid="cart-badge"
                    aria-hidden="true"
                    className="absolute -right-3 -top-2 flex h-5 w-5 items-center justify-center rounded-full bg-[var(--color-accent)] text-xs font-bold text-white"
                  >
                    {cartCount}
                  </span>
                )}
              </Link>
              <Link href="/orders" className="hover:text-[var(--color-accent)]">
                Orders
              </Link>
              <Link href="/profile" className="hover:text-[var(--color-accent)]">
                Profile
              </Link>
            </>
          ) : (
            <>
              <Link href="/login" className="hover:text-[var(--color-accent)]">
                Login
              </Link>
              <Link
                href="/register"
                className="rounded-md bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--color-accent-dark)]"
              >
                Register
              </Link>
            </>
          )}
          <button
            onClick={toggleTheme}
            aria-label="Toggle theme"
            className="rounded-md p-2 hover:bg-[var(--border)]"
          >
            {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
          </button>
        </div>

        {/* Mobile controls */}
        <div className="flex items-center gap-2 md:hidden">
          <button
            onClick={toggleTheme}
            aria-label="Toggle theme"
            className="rounded-md p-2"
          >
            {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
          </button>
          <button
            onClick={() => setMenuOpen((prev) => !prev)}
            aria-expanded={menuOpen}
            aria-label="Toggle mobile menu"
            className="rounded-md p-2"
          >
            {menuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <nav
          aria-label="Mobile navigation"
          className="border-t border-[var(--border)] px-4 py-4 md:hidden"
        >
          <div className="flex flex-col gap-3">
            <Link href="/" onClick={() => setMenuOpen(false)}>
              Home
            </Link>
            <Link href="/products" onClick={() => setMenuOpen(false)}>
              Products
            </Link>
            {isAuthenticated ? (
              <>
                <Link href="/cart" onClick={() => setMenuOpen(false)}>
                  Cart{cartCount > 0 && <span> ({cartCount})</span>}
                </Link>
                <Link href="/orders" onClick={() => setMenuOpen(false)}>
                  Orders
                </Link>
                <Link href="/profile" onClick={() => setMenuOpen(false)}>
                  Profile
                </Link>
              </>
            ) : (
              <>
                <Link href="/login" onClick={() => setMenuOpen(false)}>
                  Login
                </Link>
                <Link href="/register" onClick={() => setMenuOpen(false)}>
                  Register
                </Link>
              </>
            )}
          </div>
        </nav>
      )}
    </header>
  );
}
