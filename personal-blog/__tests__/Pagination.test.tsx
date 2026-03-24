import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Pagination from '../components/Pagination';

describe('Pagination', () => {
  const defaultProps = {
    totalItems: 25,
    currentPage: 1,
    onPageChange: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('page count rendering', () => {
    it('renders correct number of page buttons for 25 items at 10 per page', () => {
      render(<Pagination {...defaultProps} />);
      // 3 pages: 1-10, 11-20, 21-25
      expect(screen.getByRole('button', { name: '1' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '2' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '3' })).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: '4' })).not.toBeInTheDocument();
    });

    it('renders 1 page for 10 items at 10 per page', () => {
      render(<Pagination totalItems={10} currentPage={1} onPageChange={jest.fn()} />);
      expect(screen.getByRole('button', { name: '1' })).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: '2' })).not.toBeInTheDocument();
    });

    it('renders 1 page for 5 items at 10 per page', () => {
      render(<Pagination totalItems={5} currentPage={1} onPageChange={jest.fn()} />);
      expect(screen.getByRole('button', { name: '1' })).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: '2' })).not.toBeInTheDocument();
    });

    it('renders correct pages with custom itemsPerPage', () => {
      render(<Pagination totalItems={20} itemsPerPage={5} currentPage={1} onPageChange={jest.fn()} />);
      // 4 pages: 1-5, 6-10, 11-15, 16-20
      expect(screen.getByRole('button', { name: '4' })).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: '5' })).not.toBeInTheDocument();
    });

    it('renders 0 items without crashing (0 pages, no page buttons)', () => {
      render(<Pagination totalItems={0} currentPage={1} onPageChange={jest.fn()} />);
      expect(screen.queryByRole('button', { name: '1' })).not.toBeInTheDocument();
    });
  });

  describe('boundary button disabled states', () => {
    it('disables previous button on page 1', () => {
      render(<Pagination {...defaultProps} />);
      const prev = screen.getByRole('button', { name: /previous|이전|prev/i });
      expect(prev).toBeDisabled();
    });

    it('enables next button on page 1 when multiple pages exist', () => {
      render(<Pagination {...defaultProps} />);
      const next = screen.getByRole('button', { name: /next|다음/i });
      expect(next).not.toBeDisabled();
    });

    it('disables next button on last page', () => {
      render(<Pagination totalItems={25} currentPage={3} onPageChange={jest.fn()} />);
      const next = screen.getByRole('button', { name: /next|다음/i });
      expect(next).toBeDisabled();
    });

    it('enables previous button on last page', () => {
      render(<Pagination totalItems={25} currentPage={3} onPageChange={jest.fn()} />);
      const prev = screen.getByRole('button', { name: /previous|이전|prev/i });
      expect(prev).not.toBeDisabled();
    });

    it('disables both prev and next on single page', () => {
      render(<Pagination totalItems={5} currentPage={1} onPageChange={jest.fn()} />);
      const prev = screen.getByRole('button', { name: /previous|이전|prev/i });
      const next = screen.getByRole('button', { name: /next|다음/i });
      expect(prev).toBeDisabled();
      expect(next).toBeDisabled();
    });

    it('enables both prev and next on a middle page', () => {
      render(<Pagination totalItems={30} currentPage={2} onPageChange={jest.fn()} />);
      const prev = screen.getByRole('button', { name: /previous|이전|prev/i });
      const next = screen.getByRole('button', { name: /next|다음/i });
      expect(prev).not.toBeDisabled();
      expect(next).not.toBeDisabled();
    });
  });

  describe('onPageChange callbacks', () => {
    it('calls onPageChange with page number when a page button is clicked', () => {
      const onPageChange = jest.fn();
      render(<Pagination totalItems={25} currentPage={1} onPageChange={onPageChange} />);
      fireEvent.click(screen.getByRole('button', { name: '2' }));
      expect(onPageChange).toHaveBeenCalledWith(2);
    });

    it('calls onPageChange with next page when next button is clicked', () => {
      const onPageChange = jest.fn();
      render(<Pagination totalItems={25} currentPage={1} onPageChange={onPageChange} />);
      fireEvent.click(screen.getByRole('button', { name: /next|다음/i }));
      expect(onPageChange).toHaveBeenCalledWith(2);
    });

    it('calls onPageChange with previous page when prev button is clicked', () => {
      const onPageChange = jest.fn();
      render(<Pagination totalItems={25} currentPage={3} onPageChange={onPageChange} />);
      fireEvent.click(screen.getByRole('button', { name: /previous|이전|prev/i }));
      expect(onPageChange).toHaveBeenCalledWith(2);
    });

    it('does not call onPageChange when disabled prev is clicked', () => {
      const onPageChange = jest.fn();
      render(<Pagination totalItems={25} currentPage={1} onPageChange={onPageChange} />);
      fireEvent.click(screen.getByRole('button', { name: /previous|이전|prev/i }));
      expect(onPageChange).not.toHaveBeenCalled();
    });

    it('does not call onPageChange when disabled next is clicked', () => {
      const onPageChange = jest.fn();
      render(<Pagination totalItems={25} currentPage={3} onPageChange={onPageChange} />);
      fireEvent.click(screen.getByRole('button', { name: /next|다음/i }));
      expect(onPageChange).not.toHaveBeenCalled();
    });

    it('calls onPageChange(1) when page 1 button is clicked regardless of currentPage', () => {
      const onPageChange = jest.fn();
      render(<Pagination totalItems={25} currentPage={3} onPageChange={onPageChange} />);
      fireEvent.click(screen.getByRole('button', { name: '1' }));
      expect(onPageChange).toHaveBeenCalledWith(1);
    });
  });

  describe('current page highlighting', () => {
    it('marks current page button as active/selected (aria-current)', () => {
      render(<Pagination totalItems={25} currentPage={2} onPageChange={jest.fn()} />);
      const page2 = screen.getByRole('button', { name: '2' });
      expect(page2).toHaveAttribute('aria-current', 'page');
    });

    it('does not mark non-current pages as aria-current', () => {
      render(<Pagination totalItems={25} currentPage={2} onPageChange={jest.fn()} />);
      const page1 = screen.getByRole('button', { name: '1' });
      expect(page1).not.toHaveAttribute('aria-current', 'page');
    });
  });
});
