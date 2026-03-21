import React from 'react';
import { render, screen } from '@testing-library/react';
import NotFound from '@/app/not-found';

describe('NotFound page', () => {
  it('renders the 404 text', () => {
    render(<NotFound />);
    expect(screen.getByText('404')).toBeInTheDocument();
  });

  it('renders the "Page not found" heading', () => {
    render(<NotFound />);
    expect(screen.getByRole('heading', { name: /page not found/i })).toBeInTheDocument();
  });

  it('renders a description paragraph', () => {
    render(<NotFound />);
    expect(screen.getByText(/doesn't exist or has been moved/i)).toBeInTheDocument();
  });

  it('renders a link to the home page', () => {
    render(<NotFound />);
    const link = screen.getByRole('link', { name: /go home/i });
    expect(link).toHaveAttribute('href', '/');
  });
});
