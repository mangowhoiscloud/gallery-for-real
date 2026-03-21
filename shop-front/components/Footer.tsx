import Link from 'next/link';

export default function Footer() {
  return (
    <footer className="border-t border-[var(--border)] bg-[var(--bg)]">
      <div className="mx-auto max-w-7xl px-4 py-8">
        <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-between">
          <p className="text-lg font-bold text-[var(--color-accent)]">ShopFront</p>
          <nav aria-label="Footer navigation" className="flex gap-6">
            <Link href="/products" className="text-[var(--muted)] hover:text-[var(--fg)]">
              Products
            </Link>
            <Link href="/about" className="text-[var(--muted)] hover:text-[var(--fg)]">
              About
            </Link>
            <Link href="/contact" className="text-[var(--muted)] hover:text-[var(--fg)]">
              Contact
            </Link>
          </nav>
          <p className="text-sm text-[var(--muted)]">
            © {new Date().getFullYear()} ShopFront. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
