import { render, screen } from '@testing-library/react';
import ProductCard from '@/components/ui/ProductCard';
import { makeProduct } from '@/lib/test-factories';

describe('ProductCard', () => {
  it('renders product name', () => {
    render(<ProductCard product={makeProduct({ name: 'Wireless Headphones' })} />);
    expect(screen.getByText('Wireless Headphones')).toBeInTheDocument();
  });

  it('renders formatted price', () => {
    render(<ProductCard product={makeProduct({ price: 49.99 })} />);
    expect(screen.getByText('$49.99')).toBeInTheDocument();
  });

  it('renders price with two decimal places', () => {
    render(<ProductCard product={makeProduct({ price: 10 })} />);
    expect(screen.getByText('$10.00')).toBeInTheDocument();
  });

  it('renders category badge', () => {
    render(<ProductCard product={makeProduct({ category: 'Electronics' })} />);
    expect(screen.getByText('Electronics')).toBeInTheDocument();
  });

  it('links to /products/[id]', () => {
    render(<ProductCard product={makeProduct({ id: 42 })} />);
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/products/42');
  });

  it('renders product image with alt text', () => {
    render(<ProductCard product={makeProduct({ name: 'Camera', imageUrl: 'https://example.com/cam.jpg' })} />);
    const img = screen.getByRole('img');
    expect(img).toHaveAttribute('alt', 'Camera');
    expect(img).toHaveAttribute('src', 'https://example.com/cam.jpg');
  });

  it('shows out-of-stock badge when stockQuantity is 0', () => {
    render(<ProductCard product={makeProduct({ stockQuantity: 0 })} />);
    expect(screen.getByText('Out of Stock')).toBeInTheDocument();
  });

  it('shows "Only X left" when stockQuantity is 1', () => {
    render(<ProductCard product={makeProduct({ stockQuantity: 1 })} />);
    expect(screen.getByText('Only 1 left')).toBeInTheDocument();
  });

  it('shows "Only X left" when stockQuantity is 5', () => {
    render(<ProductCard product={makeProduct({ stockQuantity: 5 })} />);
    expect(screen.getByText('Only 5 left')).toBeInTheDocument();
  });

  it('shows no stock indicator when stockQuantity is greater than 5', () => {
    render(<ProductCard product={makeProduct({ stockQuantity: 10 })} />);
    expect(screen.queryByText('Out of Stock')).not.toBeInTheDocument();
    expect(screen.queryByText(/Only \d+ left/)).not.toBeInTheDocument();
  });

  it('does not show "Only X left" when out of stock', () => {
    render(<ProductCard product={makeProduct({ stockQuantity: 0 })} />);
    expect(screen.queryByText(/Only \d+ left/)).not.toBeInTheDocument();
  });
});
