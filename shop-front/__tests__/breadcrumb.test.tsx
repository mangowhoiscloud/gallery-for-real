import { render, screen } from '@testing-library/react';
import Breadcrumb from '@/components/ui/Breadcrumb';

const threeItems = [
  { label: 'Home', href: '/' },
  { label: 'Products', href: '/products' },
  { label: 'Wireless Headphones', href: '/products/42' },
];

describe('Breadcrumb', () => {
  it('renders all item labels', () => {
    render(<Breadcrumb items={threeItems} />);
    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Products')).toBeInTheDocument();
    expect(screen.getByText('Wireless Headphones')).toBeInTheDocument();
  });

  it('links all items except the last', () => {
    render(<Breadcrumb items={threeItems} />);
    expect(screen.getByRole('link', { name: 'Home' })).toHaveAttribute('href', '/');
    expect(screen.getByRole('link', { name: 'Products' })).toHaveAttribute('href', '/products');
  });

  it('does not render the last item as a link', () => {
    render(<Breadcrumb items={threeItems} />);
    expect(screen.queryByRole('link', { name: 'Wireless Headphones' })).not.toBeInTheDocument();
  });

  it('marks the last item with aria-current="page"', () => {
    render(<Breadcrumb items={threeItems} />);
    expect(screen.getByText('Wireless Headphones')).toHaveAttribute('aria-current', 'page');
  });

  it('renders a single item as non-linked with aria-current="page"', () => {
    render(<Breadcrumb items={[{ label: 'Home', href: '/' }]} />);
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
    expect(screen.getByText('Home')).toHaveAttribute('aria-current', 'page');
  });

  it('renders correct number of links for multi-item list', () => {
    render(<Breadcrumb items={threeItems} />);
    // 3 items → 2 links (all except last)
    expect(screen.getAllByRole('link')).toHaveLength(2);
  });

  it('has accessible nav landmark', () => {
    render(<Breadcrumb items={threeItems} />);
    expect(screen.getByRole('navigation', { name: 'Breadcrumb' })).toBeInTheDocument();
  });
});
