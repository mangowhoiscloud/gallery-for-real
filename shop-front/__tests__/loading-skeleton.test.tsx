import { render, screen } from '@testing-library/react';
import LoadingSkeleton from '@/components/ui/LoadingSkeleton';

describe('LoadingSkeleton', () => {
  it('renders default 8 skeleton cards', () => {
    const { container } = render(<LoadingSkeleton />);
    const pulseElements = container.querySelectorAll('.animate-pulse');
    expect(pulseElements).toHaveLength(8);
  });

  it('renders specified count of skeleton cards', () => {
    const { container } = render(<LoadingSkeleton count={4} />);
    const pulseElements = container.querySelectorAll('.animate-pulse');
    expect(pulseElements).toHaveLength(4);
  });

  it('renders 1 skeleton card when count is 1', () => {
    const { container } = render(<LoadingSkeleton count={1} />);
    const pulseElements = container.querySelectorAll('.animate-pulse');
    expect(pulseElements).toHaveLength(1);
  });

  it('has testid="loading-skeleton" on the container', () => {
    render(<LoadingSkeleton />);
    expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
  });

  it('renders responsive grid classes on the container', () => {
    render(<LoadingSkeleton />);
    const container = screen.getByTestId('loading-skeleton');
    expect(container.className).toMatch(/grid/);
    expect(container.className).toMatch(/grid-cols-1/);
  });
});
