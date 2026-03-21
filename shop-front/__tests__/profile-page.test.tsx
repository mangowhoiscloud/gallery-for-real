import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ProfilePage from '@/app/profile/ProfilePage';
import { makeMember } from '@/lib/test-factories';

const mockReplace = jest.fn();
const mockPush = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace }),
}));

const mockToast = jest.fn();

jest.mock('@/components/ToastProvider', () => ({
  useToast: () => ({ toast: mockToast, dismiss: jest.fn(), toasts: [] }),
}));

jest.mock('@/lib/auth', () => ({
  isAuthenticated: jest.fn(),
  clearCredentials: jest.fn(),
}));

jest.mock('@/lib/api', () => ({
  getProfile: jest.fn(),
  updateProfile: jest.fn(),
}));

const mockIsAuthenticated = jest.requireMock('@/lib/auth').isAuthenticated as jest.Mock;
const mockClearCredentials = jest.requireMock('@/lib/auth').clearCredentials as jest.Mock;
const mockGetProfile = jest.requireMock('@/lib/api').getProfile as jest.Mock;
const mockUpdateProfile = jest.requireMock('@/lib/api').updateProfile as jest.Mock;

beforeEach(() => {
  jest.clearAllMocks();
  mockIsAuthenticated.mockReturnValue(true);
});

describe('ProfilePage — auth redirect', () => {
  it('redirects to /login?redirect=/profile when not authenticated', async () => {
    mockIsAuthenticated.mockReturnValue(false);
    render(<ProfilePage />);
    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith('/login?redirect=/profile');
    });
  });
});

describe('ProfilePage — profile display', () => {
  it('renders profile info correctly', async () => {
    const member = makeMember({ name: 'Jane Doe', email: 'jane@example.com', phone: '555-1234', address: '42 Elm St' });
    mockGetProfile.mockResolvedValue(member);
    render(<ProfilePage />);

    expect(await screen.findByText('jane@example.com')).toBeInTheDocument();
    expect(screen.getByText('Jane Doe')).toBeInTheDocument();
    expect(screen.getByText('555-1234')).toBeInTheDocument();
    expect(screen.getByText('42 Elm St')).toBeInTheDocument();
  });

  it('shows em dash for missing optional fields', async () => {
    const member = makeMember({ phone: undefined, address: undefined });
    mockGetProfile.mockResolvedValue(member);
    render(<ProfilePage />);

    await screen.findByText(member.email);
    const dashes = screen.getAllByText('—');
    expect(dashes).toHaveLength(2);
  });

  it('shows orders link and logout button', async () => {
    mockGetProfile.mockResolvedValue(makeMember());
    render(<ProfilePage />);

    await screen.findByText(makeMember().email);
    expect(screen.getByRole('link', { name: 'My Orders' })).toHaveAttribute('href', '/orders');
    expect(screen.getByRole('button', { name: 'Logout' })).toBeInTheDocument();
  });
});

describe('ProfilePage — edit mode', () => {
  it('toggles input fields when Edit Profile is clicked', async () => {
    mockGetProfile.mockResolvedValue(makeMember());
    render(<ProfilePage />);

    await screen.findByText(makeMember().email);
    fireEvent.click(screen.getByRole('button', { name: 'Edit Profile' }));

    expect(screen.getByRole('textbox', { name: /name/i })).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: /phone/i })).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: /address/i })).toBeInTheDocument();
  });

  it('cancel reverts to display mode without saving', async () => {
    mockGetProfile.mockResolvedValue(makeMember({ name: 'Original Name' }));
    render(<ProfilePage />);

    await screen.findByText('Original Name');
    fireEvent.click(screen.getByRole('button', { name: 'Edit Profile' }));

    const nameInput = screen.getByRole('textbox', { name: /name/i });
    fireEvent.change(nameInput, { target: { value: 'Changed Name' } });

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));

    expect(screen.queryByRole('textbox', { name: /name/i })).not.toBeInTheDocument();
    expect(mockUpdateProfile).not.toHaveBeenCalled();
  });

  it('save calls updateProfile API with form values', async () => {
    const original = makeMember({ name: 'Old Name', phone: '000', address: '1 Main St' });
    const updated = makeMember({ name: 'New Name', phone: '111', address: '2 Oak Ave' });
    mockGetProfile.mockResolvedValue(original);
    mockUpdateProfile.mockResolvedValue(updated);

    render(<ProfilePage />);
    await screen.findByText('Old Name');

    fireEvent.click(screen.getByRole('button', { name: 'Edit Profile' }));

    fireEvent.change(screen.getByRole('textbox', { name: /name/i }), { target: { value: 'New Name' } });
    fireEvent.change(screen.getByRole('textbox', { name: /phone/i }), { target: { value: '111' } });
    fireEvent.change(screen.getByRole('textbox', { name: /address/i }), { target: { value: '2 Oak Ave' } });

    fireEvent.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => {
      expect(mockUpdateProfile).toHaveBeenCalledWith({
        name: 'New Name',
        phone: '111',
        address: '2 Oak Ave',
      });
    });
  });

  it('shows success toast and exits edit mode after save', async () => {
    const member = makeMember();
    mockGetProfile.mockResolvedValue(member);
    mockUpdateProfile.mockResolvedValue({ ...member, name: 'Saved Name' });

    render(<ProfilePage />);
    await screen.findByText(member.email);

    fireEvent.click(screen.getByRole('button', { name: 'Edit Profile' }));
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({ title: 'Profile updated successfully', variant: 'success' }),
      );
    });
    expect(screen.queryByRole('textbox', { name: /name/i })).not.toBeInTheDocument();
  });

  it('shows error toast when updateProfile fails', async () => {
    mockGetProfile.mockResolvedValue(makeMember());
    mockUpdateProfile.mockRejectedValue(new Error('Server error'));

    render(<ProfilePage />);
    await screen.findByText(makeMember().email);

    fireEvent.click(screen.getByRole('button', { name: 'Edit Profile' }));
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({ title: 'Failed to update profile', variant: 'error' }),
      );
    });
  });
});

describe('ProfilePage — logout', () => {
  it('clears credentials, shows toast, and redirects to home', async () => {
    mockGetProfile.mockResolvedValue(makeMember());
    render(<ProfilePage />);

    await screen.findByText(makeMember().email);
    fireEvent.click(screen.getByRole('button', { name: 'Logout' }));

    expect(mockClearCredentials).toHaveBeenCalled();
    expect(mockToast).toHaveBeenCalledWith(
      expect.objectContaining({ title: 'Logged out successfully', variant: 'success' }),
    );
    expect(mockPush).toHaveBeenCalledWith('/');
  });
});
