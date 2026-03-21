import React from 'react';
import { render, screen } from '@testing-library/react';
import CategoryNav, { FALLBACK_CATEGORIES } from '@/components/CategoryNav';
import ProductSection from '@/components/ProductSection';
import { makeProduct } from '@/lib/test-factories';

describe('CategoryNav', () => {
  it('renders all fallback categories when none are provided', () => {
    render(<CategoryNav />);
    for (const cat of FALLBACK_CATEGORIES) {
      expect(screen.getByRole('link', { name: cat })).toBeInTheDocument();
    }
  });

  it('renders links with correct category href params', () => {
    render(<CategoryNav categories={['Electronics', 'Clothing']} />);
    expect(screen.getByRole('link', { name: 'Electronics' })).toHaveAttribute(
      'href',
      '/products?category=Electronics',
    );
    expect(screen.getByRole('link', { name: 'Clothing' })).toHaveAttribute(
      'href',
      '/products?category=Clothing',
    );
  });

  it('renders only the provided categories', () => {
    render(<CategoryNav categories={['Home', 'Books']} />);
    expect(screen.queryByRole('link', { name: 'Electronics' })).not.toBeInTheDocument();
    expect(screen.getAllByRole('link')).toHaveLength(2);
  });

  it('renders an accessible nav landmark with a label', () => {
    render(<CategoryNav />);
    expect(screen.getByRole('navigation', { name: /product categories/i })).toBeInTheDocument();
  });

  it('URL-encodes category names with spaces', () => {
    render(<CategoryNav categories={['Home Goods']} />);
    const link = screen.getByRole('link', { name: 'Home Goods' });
    expect(link.getAttribute('href')).toBe(`/products?category=${encodeURIComponent('Home Goods')}`);
  });
});

describe('ProductSection', () => {
  const products = [
    makeProduct({ id: 1, name: 'Widget Alpha' }),
    makeProduct({ id: 2, name: 'Widget Beta' }),
  ];

  it('renders the section title as a heading', () => {
    render(<ProductSection title="New Arrivals" products={products} />);
    expect(screen.getByRole('heading', { name: 'New Arrivals' })).toBeInTheDocument();
  });

  it('renders a product card for each product in New Arrivals', () => {
    render(<ProductSection title="New Arrivals" products={products} />);
    expect(screen.getByText('Widget Alpha')).toBeInTheDocument();
    expect(screen.getByText('Widget Beta')).toBeInTheDocument();
  });

  it('renders a product card for each product in Best Sellers', () => {
    render(<ProductSection title="Best Sellers" products={products} />);
    expect(screen.getByRole('heading', { name: 'Best Sellers' })).toBeInTheDocument();
    expect(screen.getByText('Widget Alpha')).toBeInTheDocument();
    expect(screen.getByText('Widget Beta')).toBeInTheDocument();
  });

  it('renders an empty grid when no products are provided', () => {
    render(<ProductSection title="New Arrivals" products={[]} />);
    expect(screen.getByRole('heading', { name: 'New Arrivals' })).toBeInTheDocument();
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });
});
