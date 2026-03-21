import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import HeroCarousel from '@/components/HeroCarousel';
import { makeProduct } from '@/lib/test-factories';

const products = [
  makeProduct({ id: 1, name: 'Product A', price: 10.0, description: 'Short description' }),
  makeProduct({ id: 2, name: 'Product B', price: 20.0, description: 'Short description' }),
  makeProduct({ id: 3, name: 'Product C', price: 30.0, description: 'Short description' }),
];

describe('HeroCarousel', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('renders null when products array is empty', () => {
    const { container } = render(<HeroCarousel products={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders the first product slide by default', () => {
    render(<HeroCarousel products={products} />);
    expect(screen.getByText('Product A')).toBeInTheDocument();
  });

  it('renders the product price formatted to 2 decimal places', () => {
    render(<HeroCarousel products={products} />);
    expect(screen.getByText('$10.00')).toBeInTheDocument();
  });

  it('renders Previous and Next slide navigation buttons', () => {
    render(<HeroCarousel products={products} />);
    expect(screen.getByRole('button', { name: /previous slide/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /next slide/i })).toBeInTheDocument();
  });

  it('renders a dot indicator for each slide', () => {
    render(<HeroCarousel products={products} />);
    const dots = screen.getAllByRole('button', { name: /go to slide/i });
    expect(dots).toHaveLength(3);
  });

  it('marks the first dot as current with aria-current', () => {
    render(<HeroCarousel products={products} />);
    const dots = screen.getAllByRole('button', { name: /go to slide/i });
    expect(dots[0]).toHaveAttribute('aria-current', 'true');
    expect(dots[1]).not.toHaveAttribute('aria-current');
    expect(dots[2]).not.toHaveAttribute('aria-current');
  });

  it('navigates to the next slide on next button click', () => {
    render(<HeroCarousel products={products} />);
    fireEvent.click(screen.getByRole('button', { name: /next slide/i }));
    expect(screen.getByText('Product B')).toBeInTheDocument();
  });

  it('wraps to the last slide when pressing prev on the first slide', () => {
    render(<HeroCarousel products={products} />);
    fireEvent.click(screen.getByRole('button', { name: /previous slide/i }));
    expect(screen.getByText('Product C')).toBeInTheDocument();
  });

  it('navigates directly to a specific slide on dot click', () => {
    render(<HeroCarousel products={products} />);
    const dots = screen.getAllByRole('button', { name: /go to slide/i });
    fireEvent.click(dots[2]);
    expect(screen.getByText('Product C')).toBeInTheDocument();
  });

  it('auto-rotates to the next slide after 5 seconds', () => {
    render(<HeroCarousel products={products} />);
    expect(screen.getByText('Product A')).toBeInTheDocument();
    act(() => {
      jest.advanceTimersByTime(5000);
    });
    expect(screen.getByText('Product B')).toBeInTheDocument();
  });

  it('pauses auto-rotation on mouse enter', () => {
    render(<HeroCarousel products={products} />);
    const carousel = screen.getByTestId('hero-carousel');
    act(() => {
      fireEvent.mouseEnter(carousel);
    });
    act(() => {
      jest.advanceTimersByTime(5000);
    });
    expect(screen.getByText('Product A')).toBeInTheDocument();
  });

  it('resumes auto-rotation after mouse leave', () => {
    render(<HeroCarousel products={products} />);
    const carousel = screen.getByTestId('hero-carousel');
    act(() => {
      fireEvent.mouseEnter(carousel);
    });
    act(() => {
      jest.advanceTimersByTime(5000);
    });
    act(() => {
      fireEvent.mouseLeave(carousel);
    });
    act(() => {
      jest.advanceTimersByTime(5000);
    });
    expect(screen.getByText('Product B')).toBeInTheDocument();
  });

  it('links the current slide to the product detail page', () => {
    render(<HeroCarousel products={products} />);
    const link = screen.getByTestId('hero-slide-link');
    expect(link).toHaveAttribute('href', '/products/1');
  });

  it('shows the product image with correct alt text', () => {
    render(<HeroCarousel products={products} />);
    const img = screen.getByRole('img', { name: 'Product A' });
    expect(img).toBeInTheDocument();
  });
});
