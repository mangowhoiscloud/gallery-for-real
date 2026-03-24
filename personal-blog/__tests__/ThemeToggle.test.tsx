import { render, screen, fireEvent } from '@testing-library/react';
import ThemeToggle from '@/components/ThemeToggle';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
  };
})();

Object.defineProperty(window, 'localStorage', { value: localStorageMock });

beforeEach(() => {
  localStorageMock.clear();
  document.documentElement.classList.remove('dark');
});

describe('ThemeToggle', () => {
  it('renders a button with accessible label', () => {
    render(<ThemeToggle />);
    const btn = screen.getByRole('button');
    expect(btn).toBeTruthy();
    expect(btn.getAttribute('aria-label')).toBe('다크 모드로 전환');
  });

  it('renders sun and moon icons', () => {
    render(<ThemeToggle />);
    expect(screen.getByTestId('sun-icon')).toBeTruthy();
    expect(screen.getByTestId('moon-icon')).toBeTruthy();
  });

  it('starts in light mode when no dark class on html', () => {
    render(<ThemeToggle />);
    const btn = screen.getByRole('button');
    expect(btn.getAttribute('aria-label')).toBe('다크 모드로 전환');
  });

  it('starts in dark mode when html has .dark class', () => {
    document.documentElement.classList.add('dark');
    render(<ThemeToggle />);
    const btn = screen.getByRole('button');
    // After useEffect fires (sync), label should reflect dark state
    // RTL wraps renders in act(), so useEffect fires synchronously
    expect(btn.getAttribute('aria-label')).toBe('라이트 모드로 전환');
  });

  it('clicking toggles dark class on <html>', () => {
    render(<ThemeToggle />);
    expect(document.documentElement.classList.contains('dark')).toBe(false);
    fireEvent.click(screen.getByRole('button'));
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    fireEvent.click(screen.getByRole('button'));
    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });

  it('persists theme to localStorage on toggle', () => {
    render(<ThemeToggle />);
    fireEvent.click(screen.getByRole('button'));
    expect(localStorageMock.getItem('theme')).toBe('dark');
    fireEvent.click(screen.getByRole('button'));
    expect(localStorageMock.getItem('theme')).toBe('light');
  });

  it('aria-label updates after toggle to reflect new state', () => {
    render(<ThemeToggle />);
    const btn = screen.getByRole('button');
    expect(btn.getAttribute('aria-label')).toBe('다크 모드로 전환');
    fireEvent.click(btn);
    expect(btn.getAttribute('aria-label')).toBe('라이트 모드로 전환');
    fireEvent.click(btn);
    expect(btn.getAttribute('aria-label')).toBe('다크 모드로 전환');
  });

  it('multiple rapid toggles keep state consistent', () => {
    render(<ThemeToggle />);
    const btn = screen.getByRole('button');
    fireEvent.click(btn); // → dark
    fireEvent.click(btn); // → light
    fireEvent.click(btn); // → dark
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(localStorageMock.getItem('theme')).toBe('dark');
  });
});
