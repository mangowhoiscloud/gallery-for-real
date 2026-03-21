import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { ThemeProvider, useTheme } from '@/components/ThemeProvider';

// Stub matchMedia — jsdom doesn't implement it
function setupMatchMedia(prefersDark: boolean) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation((query: string) => ({
      matches: prefersDark && query === '(prefers-color-scheme: dark)',
      media: query,
      onchange: null,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  });
}

function ThemeConsumer() {
  const { theme, toggleTheme } = useTheme();
  return (
    <div>
      <span data-testid="theme">{theme}</span>
      <button onClick={toggleTheme}>Toggle</button>
    </div>
  );
}

describe('ThemeProvider', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('dark');
    setupMatchMedia(false);
  });

  it('defaults to light theme when no stored preference or system preference', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    expect(screen.getByTestId('theme')).toHaveTextContent('light');
  });

  it('reads dark theme from localStorage on mount', async () => {
    localStorage.setItem('theme', 'dark');
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    await waitFor(() => {
      expect(screen.getByTestId('theme')).toHaveTextContent('dark');
    });
  });

  it('reads light theme from localStorage on mount', async () => {
    localStorage.setItem('theme', 'light');
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    await waitFor(() => {
      expect(screen.getByTestId('theme')).toHaveTextContent('light');
    });
  });

  it('detects system dark preference when no localStorage entry', async () => {
    setupMatchMedia(true);
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    await waitFor(() => {
      expect(screen.getByTestId('theme')).toHaveTextContent('dark');
    });
  });

  it('toggleTheme switches from light to dark', async () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    act(() => {
      fireEvent.click(screen.getByRole('button', { name: /toggle/i }));
    });
    expect(screen.getByTestId('theme')).toHaveTextContent('dark');
  });

  it('toggleTheme applies "dark" class to document.documentElement', async () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    act(() => {
      fireEvent.click(screen.getByRole('button', { name: /toggle/i }));
    });
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  it('toggleTheme persists choice to localStorage', async () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    act(() => {
      fireEvent.click(screen.getByRole('button', { name: /toggle/i }));
    });
    expect(localStorage.getItem('theme')).toBe('dark');
  });

  it('toggleTheme switches back from dark to light', async () => {
    localStorage.setItem('theme', 'dark');
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    await waitFor(() => expect(screen.getByTestId('theme')).toHaveTextContent('dark'));
    act(() => {
      fireEvent.click(screen.getByRole('button', { name: /toggle/i }));
    });
    expect(screen.getByTestId('theme')).toHaveTextContent('light');
    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });
});
