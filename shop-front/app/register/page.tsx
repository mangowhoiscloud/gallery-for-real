'use client';

import { useState, FormEvent } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { register } from '@/lib/api';
import { saveCredentials } from '@/lib/auth';
import { useToast } from '@/components/ToastProvider';

interface FormErrors {
  name?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
}

function validateForm(
  name: string,
  email: string,
  password: string,
  confirmPassword: string,
): FormErrors {
  const errors: FormErrors = {};
  if (!name || name.trim().length < 2) errors.name = 'Name must be at least 2 characters';
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))
    errors.email = 'Enter a valid email address';
  if (!password || password.length < 8) errors.password = 'Password must be at least 8 characters';
  if (password !== confirmPassword) errors.confirmPassword = 'Passwords do not match';
  return errors;
}

export default function RegisterPage() {
  const router = useRouter();
  const { toast } = useToast();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();

    const validationErrors = validateForm(name, email, password, confirmPassword);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) return;

    setIsSubmitting(true);
    try {
      await register({
        name: name.trim(),
        email,
        password,
        phone: phone || undefined,
        address: address || undefined,
      });
      saveCredentials(email, password);
      router.push('/');
    } catch {
      toast({
        variant: 'error',
        title: 'Registration failed',
        description: 'An error occurred. Please try again.',
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center py-12 px-4">
      <div className="w-full max-w-md">
        <h1 className="text-3xl font-bold text-center mb-8">Create Account</h1>
        <form onSubmit={handleSubmit} noValidate className="space-y-5">
          <div>
            <label htmlFor="name" className="block text-sm font-medium mb-1">
              Name
            </label>
            <input
              id="name"
              type="text"
              autoComplete="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
              aria-invalid={errors.name ? 'true' : 'false'}
              aria-describedby={errors.name ? 'name-error' : undefined}
            />
            {errors.name && (
              <p id="name-error" role="alert" className="text-red-600 text-xs mt-1">
                {errors.name}
              </p>
            )}
          </div>
          <div>
            <label htmlFor="email" className="block text-sm font-medium mb-1">
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
              aria-invalid={errors.email ? 'true' : 'false'}
              aria-describedby={errors.email ? 'email-error' : undefined}
            />
            {errors.email && (
              <p id="email-error" role="alert" className="text-red-600 text-xs mt-1">
                {errors.email}
              </p>
            )}
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium mb-1">
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
              aria-invalid={errors.password ? 'true' : 'false'}
              aria-describedby={errors.password ? 'password-error' : undefined}
            />
            {errors.password && (
              <p id="password-error" role="alert" className="text-red-600 text-xs mt-1">
                {errors.password}
              </p>
            )}
          </div>
          <div>
            <label htmlFor="confirm-password" className="block text-sm font-medium mb-1">
              Confirm Password
            </label>
            <input
              id="confirm-password"
              type="password"
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
              aria-invalid={errors.confirmPassword ? 'true' : 'false'}
              aria-describedby={errors.confirmPassword ? 'confirm-password-error' : undefined}
            />
            {errors.confirmPassword && (
              <p id="confirm-password-error" role="alert" className="text-red-600 text-xs mt-1">
                {errors.confirmPassword}
              </p>
            )}
          </div>
          <div>
            <label htmlFor="phone" className="block text-sm font-medium mb-1">
              Phone <span className="text-gray-500">(optional)</span>
            </label>
            <input
              id="phone"
              type="tel"
              autoComplete="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
          <div>
            <label htmlFor="address" className="block text-sm font-medium mb-1">
              Address <span className="text-gray-500">(optional)</span>
            </label>
            <input
              id="address"
              type="text"
              autoComplete="street-address"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-accent text-white rounded-lg px-4 py-2 font-semibold hover:bg-accent/90 disabled:opacity-60 transition-colors"
          >
            {isSubmitting ? 'Creating account\u2026' : 'Create Account'}
          </button>
        </form>
        <p className="text-center text-sm mt-6">
          Already have an account?{' '}
          <Link href="/login" className="text-accent font-medium hover:underline">
            Login
          </Link>
        </p>
      </div>
    </main>
  );
}
