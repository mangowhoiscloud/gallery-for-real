import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Toast } from '@/components/ui/Toast';
import type { ToastItem } from '@/components/ToastProvider';

function makeItem(overrides: Partial<ToastItem> = {}): ToastItem {
  return {
    id: 'test-id',
    variant: 'success',
    title: 'Test Toast',
    ...overrides,
  };
}

describe('Toast', () => {
  it('renders the title', () => {
    render(<Toast item={makeItem()} onDismiss={jest.fn()} />);
    expect(screen.getByText('Test Toast')).toBeInTheDocument();
  });

  it('renders description when provided', () => {
    render(<Toast item={makeItem({ description: 'A description' })} onDismiss={jest.fn()} />);
    expect(screen.getByText('A description')).toBeInTheDocument();
  });

  it('does not render description when not provided', () => {
    render(<Toast item={makeItem()} onDismiss={jest.fn()} />);
    // No <p> for description
    expect(screen.queryByText('A description')).toBeNull();
  });

  it('applies success variant class (green border)', () => {
    render(<Toast item={makeItem({ variant: 'success' })} onDismiss={jest.fn()} />);
    const root = screen.getByRole('status');
    expect(root.className).toContain('border-green-500');
  });

  it('applies error variant class (red border)', () => {
    render(<Toast item={makeItem({ variant: 'error' })} onDismiss={jest.fn()} />);
    const root = screen.getByRole('status');
    expect(root.className).toContain('border-red-500');
  });

  it('applies info variant class (blue border)', () => {
    render(<Toast item={makeItem({ variant: 'info' })} onDismiss={jest.fn()} />);
    const root = screen.getByRole('status');
    expect(root.className).toContain('border-blue-500');
  });

  it('renders action button when action is provided', () => {
    const onClick = jest.fn();
    render(
      <Toast item={makeItem({ action: { label: 'Undo', onClick } })} onDismiss={jest.fn()} />,
    );
    expect(screen.getByRole('button', { name: 'Undo' })).toBeInTheDocument();
  });

  it('action button calls its callback on click', () => {
    const onClick = jest.fn();
    render(
      <Toast item={makeItem({ action: { label: 'Undo', onClick } })} onDismiss={jest.fn()} />,
    );
    fireEvent.click(screen.getByRole('button', { name: 'Undo' }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('does not render action button when no action', () => {
    render(<Toast item={makeItem()} onDismiss={jest.fn()} />);
    // Only the close button should be present
    expect(screen.getAllByRole('button')).toHaveLength(1);
  });

  it('renders a close button', () => {
    render(<Toast item={makeItem()} onDismiss={jest.fn()} />);
    expect(screen.getByRole('button', { name: /close toast/i })).toBeInTheDocument();
  });

  it('close button calls onDismiss with the toast id', () => {
    const onDismiss = jest.fn();
    render(<Toast item={makeItem({ id: 'abc123' })} onDismiss={onDismiss} />);
    fireEvent.click(screen.getByRole('button', { name: /close toast/i }));
    expect(onDismiss).toHaveBeenCalledWith('abc123');
  });

  it('toast disappears after close button click', () => {
    render(<Toast item={makeItem()} onDismiss={jest.fn()} />);
    expect(screen.getByRole('status')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /close toast/i }));
    expect(screen.queryByRole('status')).toBeNull();
  });
});
