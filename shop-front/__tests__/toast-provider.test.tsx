import React from 'react';
import { render, screen, fireEvent, act, waitFor } from '@testing-library/react';
import { ToastProvider, useToast, ToastItem } from '@/components/ToastProvider';

function ToastConsumer() {
  const { toasts, toast, dismiss } = useToast();
  return (
    <div>
      <span data-testid="count">{toasts.length}</span>
      <ul>
        {toasts.map((t: ToastItem) => (
          <li key={t.id} data-testid={`toast-${t.id}`}>
            <span data-testid="toast-title">{t.title}</span>
            <span data-testid="toast-variant">{t.variant}</span>
            <button onClick={() => dismiss(t.id)}>Dismiss</button>
          </li>
        ))}
      </ul>
      <button
        onClick={() =>
          toast({ variant: 'success', title: 'Hello', description: 'World' })
        }
        aria-label="Add toast"
      >
        Add
      </button>
      <button
        onClick={() => toast({ variant: 'error', title: 'Error toast' })}
        aria-label="Add error"
      >
        Error
      </button>
    </div>
  );
}

describe('ToastProvider', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('starts with empty toasts array', () => {
    render(
      <ToastProvider>
        <ToastConsumer />
      </ToastProvider>,
    );
    expect(screen.getByTestId('count')).toHaveTextContent('0');
  });

  it('toast() adds a toast to the list', () => {
    render(
      <ToastProvider>
        <ToastConsumer />
      </ToastProvider>,
    );
    act(() => {
      fireEvent.click(screen.getByRole('button', { name: /add toast/i }));
    });
    expect(screen.getByTestId('count')).toHaveTextContent('1');
    expect(screen.getByTestId('toast-title')).toHaveTextContent('Hello');
    expect(screen.getByTestId('toast-variant')).toHaveTextContent('success');
  });

  it('dismiss() removes the toast immediately', () => {
    render(
      <ToastProvider>
        <ToastConsumer />
      </ToastProvider>,
    );
    act(() => {
      fireEvent.click(screen.getByRole('button', { name: /add toast/i }));
    });
    expect(screen.getByTestId('count')).toHaveTextContent('1');

    act(() => {
      fireEvent.click(screen.getByRole('button', { name: /dismiss/i }));
    });
    expect(screen.getByTestId('count')).toHaveTextContent('0');
  });

  it('toast auto-dismisses after 5 seconds', async () => {
    render(
      <ToastProvider>
        <ToastConsumer />
      </ToastProvider>,
    );
    act(() => {
      fireEvent.click(screen.getByRole('button', { name: /add toast/i }));
    });
    expect(screen.getByTestId('count')).toHaveTextContent('1');

    act(() => {
      jest.advanceTimersByTime(5000);
    });
    await waitFor(() => {
      expect(screen.getByTestId('count')).toHaveTextContent('0');
    });
  });

  it('multiple toasts can coexist', () => {
    render(
      <ToastProvider>
        <ToastConsumer />
      </ToastProvider>,
    );
    act(() => {
      fireEvent.click(screen.getByRole('button', { name: /add toast/i }));
      fireEvent.click(screen.getByRole('button', { name: /add error/i }));
    });
    expect(screen.getByTestId('count')).toHaveTextContent('2');
  });

  it('only the timed-out toast is removed after 5s when multiple exist', async () => {
    render(
      <ToastProvider>
        <ToastConsumer />
      </ToastProvider>,
    );
    // Add first toast at t=0
    act(() => {
      fireEvent.click(screen.getByRole('button', { name: /add toast/i }));
    });
    // Advance 2s, add second toast at t=2000
    act(() => {
      jest.advanceTimersByTime(2000);
    });
    act(() => {
      fireEvent.click(screen.getByRole('button', { name: /add error/i }));
    });
    expect(screen.getByTestId('count')).toHaveTextContent('2');

    // Advance to t=5000 — first toast timer fires
    act(() => {
      jest.advanceTimersByTime(3000);
    });
    await waitFor(() => {
      expect(screen.getByTestId('count')).toHaveTextContent('1');
    });
  });
});
