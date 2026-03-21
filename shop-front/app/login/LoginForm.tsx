'use client';

import { useState, FormEvent } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { login, AuthError } from '@/lib/api';
import { saveCredentials } from '@/lib/auth';
import { useToast } from '@/components/ToastProvider';

function validateEmail(email: string): string | null {
  if (!email) return 'Email is required';
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return 'Enter a valid email address';
  return null;
}

function validatePassword(password: string): string | null {
  if (!password) return 'Password is required';
  return null;
}

export default function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [emailError, setEmailError] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();

    const emailErr = validateEmail(email);
    const passwordErr = validatePassword(password);
    setEmailError(emailErr);
    setPasswordError(passwordErr);
    if (emailErr || passwordErr) return;

    setIsSubmitting(true);
    try {
      await login(email, password);
      saveCredentials(email, password, rememberMe);
      const redirectTo = searchParams.get('redirect') ?? '/';
      router.push(redirectTo);
    } catch (err) {
      if (err instanceof AuthError) {
        toast({
          variant: 'error',
          title: 'Invalid credentials',
          description: 'Please check your email and password.',
        });
      } else {
        toast({
          variant: 'error',
          title: 'Login failed',
          description: 'An unexpected error occurred. Please try again.',
        });
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center py-12 px-4">
      <div className="w-full max-w-md">
        <h1 className="text-3xl font-bold text-center mb-8">Sign In</h1>
        <form onSubmit={handleSubmit} noValidate className="space-y-5">
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
              aria-invalid={emailError ? 'true' : 'false'}
              aria-describedby={emailError ? 'email-error' : undefined}
            />
            {emailError && (
              <p id="email-error" role="alert" className="text-red-600 text-xs mt-1">
                {emailError}
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
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
              aria-invalid={passwordError ? 'true' : 'false'}
              aria-describedby={passwordError ? 'password-error' : undefined}
            />
            {passwordError && (
              <p id="password-error" role="alert" className="text-red-600 text-xs mt-1">
                {passwordError}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2">
            <input
              id="remember-me"
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="rounded"
            />
            <label htmlFor="remember-me" className="text-sm">
              Remember me
            </label>
          </div>
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-accent text-white rounded-lg px-4 py-2 font-semibold hover:bg-accent/90 disabled:opacity-60 transition-colors"
          >
            {isSubmitting ? 'Signing in\u2026' : 'Sign In'}
          </button>
        </form>
        <p className="text-center text-sm mt-6">
          Don&apos;t have an account?{' '}
          <Link href="/register" className="text-accent font-medium hover:underline">
            Register
          </Link>
        </p>
      </div>
    </main>
  );
}
