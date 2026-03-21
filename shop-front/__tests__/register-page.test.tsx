import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import RegisterPage from '@/app/register/page';

jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

jest.mock('@/lib/api', () => ({
  register: jest.fn(),
}));

jest.mock('@/lib/auth', () => ({
  saveCredentials: jest.fn(),
}));

jest.mock('@/components/ToastProvider', () => ({
  useToast: jest.fn(),
}));

import { useRouter } from 'next/navigation';
import { register } from '@/lib/api';
import { saveCredentials } from '@/lib/auth';
import { useToast } from '@/components/ToastProvider';

const mockUseRouter = useRouter as jest.Mock;
const mockRegister = register as jest.Mock;
const mockSaveCredentials = saveCredentials as jest.Mock;
const mockUseToast = useToast as jest.Mock;

const submitForm = () => {
  const btn = screen.getByRole('button', { name: /create account/i });
  fireEvent.submit(btn.closest('form')!);
};

const fillValidForm = () => {
  fireEvent.change(screen.getByLabelText(/^name$/i), { target: { value: 'Alice' } });
  fireEvent.change(screen.getByLabelText(/^email$/i), {
    target: { value: 'alice@example.com' },
  });
  fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: 'securepass1' } });
  fireEvent.change(screen.getByLabelText(/confirm password/i), {
    target: { value: 'securepass1' },
  });
};

describe('RegisterPage', () => {
  const mockPush = jest.fn();
  const mockToast = jest.fn();

  beforeEach(() => {
    mockUseRouter.mockReturnValue({ push: mockPush });
    mockUseToast.mockReturnValue({ toast: mockToast });
    mockRegister.mockResolvedValue({ id: 1, email: 'alice@example.com', name: 'Alice' });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders name, email, password, confirm-password, phone, address fields and submit button', () => {
    render(<RegisterPage />);
    expect(screen.getByLabelText(/^name$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^email$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/phone/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/address/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument();
  });

  it('renders a link to /login', () => {
    render(<RegisterPage />);
    expect(screen.getByRole('link', { name: /^login$/i })).toHaveAttribute('href', '/login');
  });

  it('shows name error when name is too short', async () => {
    render(<RegisterPage />);
    fireEvent.change(screen.getByLabelText(/^name$/i), { target: { value: 'A' } });
    fireEvent.change(screen.getByLabelText(/^email$/i), {
      target: { value: 'alice@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: 'securepass1' } });
    fireEvent.change(screen.getByLabelText(/confirm password/i), {
      target: { value: 'securepass1' },
    });
    submitForm();
    await waitFor(() => {
      const alerts = screen.getAllByRole('alert');
      expect(alerts.some((el) => el.textContent?.match(/at least 2 characters/i))).toBe(true);
    });
    expect(mockRegister).not.toHaveBeenCalled();
  });

  it('shows email error for invalid email format', async () => {
    render(<RegisterPage />);
    fireEvent.change(screen.getByLabelText(/^name$/i), { target: { value: 'Alice' } });
    fireEvent.change(screen.getByLabelText(/^email$/i), { target: { value: 'bad-email' } });
    fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: 'securepass1' } });
    fireEvent.change(screen.getByLabelText(/confirm password/i), {
      target: { value: 'securepass1' },
    });
    submitForm();
    await waitFor(() => {
      const alerts = screen.getAllByRole('alert');
      expect(alerts.some((el) => el.textContent?.match(/valid email/i))).toBe(true);
    });
    expect(mockRegister).not.toHaveBeenCalled();
  });

  it('shows password error when password is too short', async () => {
    render(<RegisterPage />);
    fireEvent.change(screen.getByLabelText(/^name$/i), { target: { value: 'Alice' } });
    fireEvent.change(screen.getByLabelText(/^email$/i), {
      target: { value: 'alice@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: 'short' } });
    fireEvent.change(screen.getByLabelText(/confirm password/i), {
      target: { value: 'short' },
    });
    submitForm();
    await waitFor(() => {
      const alerts = screen.getAllByRole('alert');
      expect(alerts.some((el) => el.textContent?.match(/at least 8 characters/i))).toBe(true);
    });
    expect(mockRegister).not.toHaveBeenCalled();
  });

  it('shows confirm password error when passwords do not match', async () => {
    render(<RegisterPage />);
    fireEvent.change(screen.getByLabelText(/^name$/i), { target: { value: 'Alice' } });
    fireEvent.change(screen.getByLabelText(/^email$/i), {
      target: { value: 'alice@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: 'securepass1' } });
    fireEvent.change(screen.getByLabelText(/confirm password/i), {
      target: { value: 'different99' },
    });
    submitForm();
    await waitFor(() => {
      const alerts = screen.getAllByRole('alert');
      expect(alerts.some((el) => el.textContent?.match(/passwords do not match/i))).toBe(true);
    });
    expect(mockRegister).not.toHaveBeenCalled();
  });

  it('calls register API with correct payload on valid form submission', async () => {
    render(<RegisterPage />);
    fillValidForm();
    submitForm();
    await waitFor(() =>
      expect(mockRegister).toHaveBeenCalledWith({
        name: 'Alice',
        email: 'alice@example.com',
        password: 'securepass1',
        phone: undefined,
        address: undefined,
      }),
    );
  });

  it('includes optional phone and address when provided', async () => {
    render(<RegisterPage />);
    fillValidForm();
    fireEvent.change(screen.getByLabelText(/phone/i), { target: { value: '555-1234' } });
    fireEvent.change(screen.getByLabelText(/address/i), { target: { value: '123 Main St' } });
    submitForm();
    await waitFor(() =>
      expect(mockRegister).toHaveBeenCalledWith(
        expect.objectContaining({ phone: '555-1234', address: '123 Main St' }),
      ),
    );
  });

  it('saves credentials after successful registration', async () => {
    render(<RegisterPage />);
    fillValidForm();
    submitForm();
    await waitFor(() =>
      expect(mockSaveCredentials).toHaveBeenCalledWith('alice@example.com', 'securepass1'),
    );
  });

  it('redirects to / after successful registration', async () => {
    render(<RegisterPage />);
    fillValidForm();
    submitForm();
    await waitFor(() => expect(mockPush).toHaveBeenCalledWith('/'));
  });

  it('shows error toast when register API fails', async () => {
    mockRegister.mockRejectedValue(new Error('Server error'));
    render(<RegisterPage />);
    fillValidForm();
    submitForm();
    await waitFor(() =>
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: 'error', title: 'Registration failed' }),
      ),
    );
  });

  it('does not redirect when register API fails', async () => {
    mockRegister.mockRejectedValue(new Error('Server error'));
    render(<RegisterPage />);
    fillValidForm();
    submitForm();
    await waitFor(() => expect(mockToast).toHaveBeenCalled());
    expect(mockPush).not.toHaveBeenCalled();
  });
});
