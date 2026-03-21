import { render, screen } from '@testing-library/react';
import ProductGrid from '@/components/ui/ProductGrid';
import { makeProductList } from '@/lib/test-factories';

describe('ProductGrid', () => {
  it('renders responsive grid layout classes', () => {
    const { container } = render(<ProductGrid />);
    const grid = container.firstChild as HTMLElement;
    expect(grid.className).toMatch(/grid/);
    expect(grid.className).toMatch(/grid-cols-1/);
    expect(grid.className).toMatch(/sm:grid-cols-2/);
    expect(grid.className).toMatch(/md:grid-cols-3/);
    expect(grid.className).toMatch(/lg:grid-cols-4/);
  });

  it('renders children when products prop is not passed', () => {
    render(
      <ProductGrid>
        <div data-testid="child-1">Item 1</div>
        <div data-testid="child-2">Item 2</div>
      </ProductGrid>,
    );
    expect(screen.getByTestId('child-1')).toBeInTheDocument();
    expect(screen.getByTestId('child-2')).toBeInTheDocument();
  });

  it('renders a ProductCard for each product when products prop is passed', () => {
    const products = makeProductList(3);
    render(<ProductGrid products={products} />);
    expect(screen.getByText('Product 1')).toBeInTheDocument();
    expect(screen.getByText('Product 2')).toBeInTheDocument();
    expect(screen.getByText('Product 3')).toBeInTheDocument();
  });

  it('renders correct number of card links for products array', () => {
    const products = makeProductList(4);
    render(<ProductGrid products={products} />);
    expect(screen.getAllByRole('link')).toHaveLength(4);
  });

  it('accepts custom className', () => {
    const { container } = render(<ProductGrid className="custom-class" />);
    const grid = container.firstChild as HTMLElement;
    expect(grid.className).toMatch(/custom-class/);
  });

  it('renders empty grid when products array is empty', () => {
    const { container } = render(<ProductGrid products={[]} />);
    const grid = container.firstChild as HTMLElement;
    expect(grid.children).toHaveLength(0);
  });
});
