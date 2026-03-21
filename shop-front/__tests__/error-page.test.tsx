import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ErrorPage from '@/app/error';

describe('Error page', () => {
  beforeEach(() => {
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    (console.error as jest.Mock).mockRestore();
  });

  it('renders "Something went wrong" heading', () => {
    render(<ErrorPage error={new Error('Test error')} reset={jest.fn()} />);
    expect(screen.getByRole('heading', { name: /something went wrong/i })).toBeInTheDocument();
  });

  it('renders the error message', () => {
    render(<ErrorPage error={new Error('Disk full')} reset={jest.fn()} />);
    expect(screen.getByText('Disk full')).toBeInTheDocument();
  });

  it('renders a fallback message when error has no message', () => {
    const err = new Error();
    err.message = '';
    render(<ErrorPage error={err} reset={jest.fn()} />);
    expect(screen.getByText('An unexpected error occurred.')).toBeInTheDocument();
  });

  it('Try Again button calls reset', () => {
    const reset = jest.fn();
    render(<ErrorPage error={new Error('Test error')} reset={reset} />);
    fireEvent.click(screen.getByRole('button', { name: /try again/i }));
    expect(reset).toHaveBeenCalledTimes(1);
  });
});
