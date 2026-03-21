import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import LoginForm from '@/app/login/LoginForm';

jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  useSearchParams: jest.fn(),
}));

// Spread real module to preserve AuthError class for instanceof checks
jest.mock('@/lib/api', () => {
  const actual = jest.requireActual('@/lib/api');
  return { ...actual, login: jest.fn() };
});

jest.mock('@/lib/auth', () => ({
  saveCredentials: jest.fn(),
}));

jest.mock('@/components/ToastProvider', () => ({
  useToast: jest.fn(),
}));

import { useRouter, useSearchParams } from 'next/navigation';
import { login, AuthError } from '@/lib/api';
import { saveCredentials } from '@/lib/auth';
import { useToast } from '@/components/ToastProvider';

const mockUseRouter = useRouter as jest.Mock;
const mockUseSearchParams = useSearchParams as jest.Mock;
const mockLogin = login as jest.Mock;
const mockSaveCredentials = saveCredentials as jest.Mock;
const mockUseToast = useToast as jest.Mock;

const submitForm = () => {
  const btn = screen.getByRole('button', { name: /sign in/i });
  fireEvent.submit(btn.closest('form')!);
};

describe('LoginForm', () => {
  const mockPush = jest.fn();
  const mockToast = jest.fn();
  const mockSearchParamsGet = jest.fn();

  beforeEach(() => {
    mockUseRouter.mockReturnValue({ push: mockPush });
    mockUseSearchParams.mockReturnValue({ get: mockSearchParamsGet });
    mockUseToast.mockReturnValue({ toast: mockToast });
    mockSearchParamsGet.mockReturnValue(null);
    mockLogin.mockResolvedValue({ id: 1, email: 'user@example.com', name: 'User' });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders email, password, remember-me, and sign-in button', () => {
    render(<LoginForm />);
    expect(screen.getByLabelText(/^email$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/remember me/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('renders a link to /register', () => {
    render(<LoginForm />);
    expect(screen.getByRole('link', { name: /register/i })).toHaveAttribute('href', '/register');
  });

  it('shows email required error when email is empty', async () => {
    render(<LoginForm />);
    fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: 'secret123' } });
    submitForm();
    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(/email is required/i),
    );
    expect(mockLogin).not.toHaveBeenCalled();
  });

  it('shows email format error for invalid email', async () => {
    render(<LoginForm />);
    fireEvent.change(screen.getByLabelText(/^email$/i), { target: { value: 'not-an-email' } });
    fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: 'secret123' } });
    submitForm();
    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(/valid email/i),
    );
    expect(mockLogin).not.toHaveBeenCalled();
  });

  it('shows password required error when password is empty', async () => {
    render(<LoginForm />);
    fireEvent.change(screen.getByLabelText(/^email$/i), { target: { value: 'user@example.com' } });
    submitForm();
    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(/password is required/i),
    );
    expect(mockLogin).not.toHaveBeenCalled();
  });

  it('calls login API with correct credentials on valid submission', async () => {
    render(<LoginForm />);
    fireEvent.change(screen.getByLabelText(/^email$/i), {
      target: { value: 'user@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: 'password123' } });
    submitForm();
    await waitFor(() =>
      expect(mockLogin).toHaveBeenCalledWith('user@example.com', 'password123'),
    );
  });

  it('saves credentials with rememberMe=false by default', async () => {
    render(<LoginForm />);
    fireEvent.change(screen.getByLabelText(/^email$/i), {
      target: { value: 'user@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: 'password123' } });
    submitForm();
    await waitFor(() =>
      expect(mockSaveCredentials).toHaveBeenCalledWith('user@example.com', 'password123', false),
    );
  });

  it('saves credentials with rememberMe=true when checkbox is checked', async () => {
    render(<LoginForm />);
    fireEvent.change(screen.getByLabelText(/^email$/i), {
      target: { value: 'user@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: 'password123' } });
    fireEvent.click(screen.getByLabelText(/remember me/i));
    submitForm();
    await waitFor(() =>
      expect(mockSaveCredentials).toHaveBeenCalledWith('user@example.com', 'password123', true),
    );
  });

  it('redirects to / when no redirect param present', async () => {
    mockSearchParamsGet.mockReturnValue(null);
    render(<LoginForm />);
    fireEvent.change(screen.getByLabelText(/^email$/i), {
      target: { value: 'user@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: 'password123' } });
    submitForm();
    await waitFor(() => expect(mockPush).toHaveBeenCalledWith('/'));
  });

  it('redirects to the redirect param URL after successful login', async () => {
    mockSearchParamsGet.mockReturnValue('/cart');
    render(<LoginForm />);
    fireEvent.change(screen.getByLabelText(/^email$/i), {
      target: { value: 'user@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: 'password123' } });
    submitForm();
    await waitFor(() => expect(mockPush).toHaveBeenCalledWith('/cart'));
  });

  it('shows error toast when AuthError is thrown', async () => {
    mockLogin.mockRejectedValue(new AuthError('Unauthorized'));
    render(<LoginForm />);
    fireEvent.change(screen.getByLabelText(/^email$/i), {
      target: { value: 'user@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: 'wrongpass' } });
    submitForm();
    await waitFor(() =>
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: 'error', title: 'Invalid credentials' }),
      ),
    );
  });

  it('does not save credentials or redirect when login fails', async () => {
    mockLogin.mockRejectedValue(new AuthError('Unauthorized'));
    render(<LoginForm />);
    fireEvent.change(screen.getByLabelText(/^email$/i), {
      target: { value: 'user@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: 'wrongpass' } });
    submitForm();
    await waitFor(() => expect(mockToast).toHaveBeenCalled());
    expect(mockSaveCredentials).not.toHaveBeenCalled();
    expect(mockPush).not.toHaveBeenCalled();
  });

  it('shows generic error toast for non-auth errors', async () => {
    mockLogin.mockRejectedValue(new Error('Network error'));
    render(<LoginForm />);
    fireEvent.change(screen.getByLabelText(/^email$/i), {
      target: { value: 'user@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: 'password123' } });
    submitForm();
    await waitFor(() =>
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: 'error', title: 'Login failed' }),
      ),
    );
  });
});
