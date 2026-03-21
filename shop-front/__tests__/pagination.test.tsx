import { render, screen, fireEvent } from '@testing-library/react';
import Pagination from '@/components/ui/Pagination';

describe('Pagination', () => {
  it('renders nothing when totalPages is 1', () => {
    const { container } = render(
      <Pagination currentPage={0} totalPages={1} onPageChange={() => {}} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders nothing when totalPages is 0', () => {
    const { container } = render(
      <Pagination currentPage={0} totalPages={0} onPageChange={() => {}} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders Previous and Next buttons', () => {
    render(<Pagination currentPage={1} totalPages={5} onPageChange={() => {}} />);
    expect(screen.getByLabelText('Previous page')).toBeInTheDocument();
    expect(screen.getByLabelText('Next page')).toBeInTheDocument();
  });

  it('disables Previous button on first page (page 0)', () => {
    render(<Pagination currentPage={0} totalPages={5} onPageChange={() => {}} />);
    expect(screen.getByLabelText('Previous page')).toBeDisabled();
  });

  it('disables Next button on last page', () => {
    render(<Pagination currentPage={4} totalPages={5} onPageChange={() => {}} />);
    expect(screen.getByLabelText('Next page')).toBeDisabled();
  });

  it('enables both buttons on a middle page', () => {
    render(<Pagination currentPage={2} totalPages={5} onPageChange={() => {}} />);
    expect(screen.getByLabelText('Previous page')).not.toBeDisabled();
    expect(screen.getByLabelText('Next page')).not.toBeDisabled();
  });

  it('calls onPageChange with correct 0-indexed page when clicking a page number', () => {
    const onPageChange = jest.fn();
    render(<Pagination currentPage={0} totalPages={5} onPageChange={onPageChange} />);
    fireEvent.click(screen.getByLabelText('Page 3'));
    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it('calls onPageChange with next page when clicking Next', () => {
    const onPageChange = jest.fn();
    render(<Pagination currentPage={1} totalPages={5} onPageChange={onPageChange} />);
    fireEvent.click(screen.getByLabelText('Next page'));
    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it('calls onPageChange with prev page when clicking Previous', () => {
    const onPageChange = jest.fn();
    render(<Pagination currentPage={2} totalPages={5} onPageChange={onPageChange} />);
    fireEvent.click(screen.getByLabelText('Previous page'));
    expect(onPageChange).toHaveBeenCalledWith(1);
  });

  it('marks current page with aria-current="page"', () => {
    render(<Pagination currentPage={2} totalPages={5} onPageChange={() => {}} />);
    expect(screen.getByLabelText('Page 3')).toHaveAttribute('aria-current', 'page');
  });

  it('does not mark other pages with aria-current', () => {
    render(<Pagination currentPage={2} totalPages={5} onPageChange={() => {}} />);
    expect(screen.getByLabelText('Page 1')).not.toHaveAttribute('aria-current');
  });

  it('shows ellipsis for large page counts', () => {
    render(<Pagination currentPage={5} totalPages={20} onPageChange={() => {}} />);
    const ellipses = screen.getAllByText('…');
    expect(ellipses.length).toBeGreaterThanOrEqual(1);
  });

  it('always shows first and last page buttons for large page counts', () => {
    render(<Pagination currentPage={5} totalPages={20} onPageChange={() => {}} />);
    expect(screen.getByLabelText('Page 1')).toBeInTheDocument();
    expect(screen.getByLabelText('Page 20')).toBeInTheDocument();
  });

  it('renders all page buttons when totalPages is 7 or fewer', () => {
    render(<Pagination currentPage={0} totalPages={7} onPageChange={() => {}} />);
    for (let i = 1; i <= 7; i++) {
      expect(screen.getByLabelText(`Page ${i}`)).toBeInTheDocument();
    }
  });
});
