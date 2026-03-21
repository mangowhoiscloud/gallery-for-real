import React from 'react';
import { render, screen } from '@testing-library/react';
import Footer from '@/components/Footer';

describe('Footer', () => {
  it('renders brand name', () => {
    render(<Footer />);
    expect(screen.getByText('ShopFront')).toBeInTheDocument();
  });

  it('renders Products, About, Contact nav links with correct hrefs', () => {
    render(<Footer />);
    expect(screen.getByRole('link', { name: /products/i })).toHaveAttribute('href', '/products');
    expect(screen.getByRole('link', { name: /about/i })).toHaveAttribute('href', '/about');
    expect(screen.getByRole('link', { name: /contact/i })).toHaveAttribute('href', '/contact');
  });

  it('renders copyright with current year', () => {
    render(<Footer />);
    const year = new Date().getFullYear().toString();
    expect(screen.getByText(new RegExp(year))).toBeInTheDocument();
  });

  it('renders footer navigation landmark', () => {
    render(<Footer />);
    expect(screen.getByRole('navigation', { name: /footer navigation/i })).toBeInTheDocument();
  });
});
