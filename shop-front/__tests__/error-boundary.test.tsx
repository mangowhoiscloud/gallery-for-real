import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ErrorBoundary } from '@/components/ErrorBoundary';

function ThrowError({ message = 'Test error' }: { message?: string }) {
  throw new Error(message);
}

describe('ErrorBoundary', () => {
  beforeEach(() => {
    // Suppress React's error logging during intentional error throws
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    (console.error as jest.Mock).mockRestore();
  });

  it('renders children when there is no error', () => {
    render(
      <ErrorBoundary>
        <div>Normal content</div>
      </ErrorBoundary>,
    );
    expect(screen.getByText('Normal content')).toBeInTheDocument();
  });

  it('catches a render error and shows default fallback', () => {
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>,
    );
    expect(screen.getByRole('heading', { name: /something went wrong/i })).toBeInTheDocument();
  });

  it('displays the error message from the thrown error', () => {
    render(
      <ErrorBoundary>
        <ThrowError message="Boom!" />
      </ErrorBoundary>,
    );
    expect(screen.getByText('Boom!')).toBeInTheDocument();
  });

  it('renders custom fallback when provided', () => {
    render(
      <ErrorBoundary fallback={<div>Custom fallback UI</div>}>
        <ThrowError />
      </ErrorBoundary>,
    );
    expect(screen.getByText('Custom fallback UI')).toBeInTheDocument();
    expect(screen.queryByText(/something went wrong/i)).toBeNull();
  });

  it('Try Again button resets error state so children can re-render', () => {
    let shouldThrow = true;

    function Conditional() {
      if (shouldThrow) throw new Error('Recoverable error');
      return <div>Recovered!</div>;
    }

    render(
      <ErrorBoundary>
        <Conditional />
      </ErrorBoundary>,
    );

    expect(screen.getByRole('heading', { name: /something went wrong/i })).toBeInTheDocument();

    shouldThrow = false;
    fireEvent.click(screen.getByRole('button', { name: /try again/i }));

    expect(screen.getByText('Recovered!')).toBeInTheDocument();
  });

  it('shows a generic message when error has no message', () => {
    function ThrowEmptyError() {
      const err = new Error();
      err.message = '';
      throw err;
    }

    render(
      <ErrorBoundary>
        <ThrowEmptyError />
      </ErrorBoundary>,
    );
    expect(screen.getByText('An unexpected error occurred.')).toBeInTheDocument();
  });
});
