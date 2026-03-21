'use client';

import { useSyncExternalStore, useCallback } from 'react';
import { CREDENTIALS_STORAGE_KEY } from './api';

export const REMEMBER_ME_KEY = 'shop_credentials_remember';

// ────────────────────────────────────────────────────────────
// Utility functions
// ────────────────────────────────────────────────────────────

/**
 * Encode and persist credentials.
 * - rememberMe=false (default): sessionStorage only — clears when tab closes.
 * - rememberMe=true: localStorage — survives across browser sessions.
 */
export function saveCredentials(
  email: string,
  password: string,
  rememberMe = false,
): void {
  if (typeof window === 'undefined') return;
  const encoded = btoa(`${email}:${password}`);
  if (rememberMe) {
    window.localStorage.setItem(CREDENTIALS_STORAGE_KEY, encoded);
    window.localStorage.setItem(REMEMBER_ME_KEY, '1');
    window.sessionStorage.removeItem(CREDENTIALS_STORAGE_KEY);
  } else {
    window.sessionStorage.setItem(CREDENTIALS_STORAGE_KEY, encoded);
    window.localStorage.removeItem(CREDENTIALS_STORAGE_KEY);
    window.localStorage.removeItem(REMEMBER_ME_KEY);
  }
  notifyListeners();
}

/**
 * Read stored credentials. sessionStorage takes priority over localStorage.
 * Returns null when not authenticated.
 */
export function getCredentials(): { email: string; password: string } | null {
  if (typeof window === 'undefined') return null;
  const encoded =
    window.sessionStorage.getItem(CREDENTIALS_STORAGE_KEY) ??
    window.localStorage.getItem(CREDENTIALS_STORAGE_KEY);
  if (!encoded) return null;
  const decoded = atob(encoded);
  // Split on the first colon only — passwords may contain colons.
  const colonIndex = decoded.indexOf(':');
  if (colonIndex === -1) return null;
  return {
    email: decoded.slice(0, colonIndex),
    password: decoded.slice(colonIndex + 1),
  };
}

/** Remove credentials from every storage location. */
export function clearCredentials(): void {
  if (typeof window === 'undefined') return;
  window.sessionStorage.removeItem(CREDENTIALS_STORAGE_KEY);
  window.localStorage.removeItem(CREDENTIALS_STORAGE_KEY);
  window.localStorage.removeItem(REMEMBER_ME_KEY);
  notifyListeners();
}

/** Returns true when valid credentials are stored. */
export function isAuthenticated(): boolean {
  return getCredentials() !== null;
}

/**
 * Returns the Authorization header value ("Basic <encoded>") or null.
 * Mirrors the logic used inside lib/api.ts so callers can attach the
 * same header to non-api-client requests if needed.
 */
export function getAuthHeader(): string | null {
  if (typeof window === 'undefined') return null;
  const encoded =
    window.sessionStorage.getItem(CREDENTIALS_STORAGE_KEY) ??
    window.localStorage.getItem(CREDENTIALS_STORAGE_KEY);
  return encoded ? `Basic ${encoded}` : null;
}

// ────────────────────────────────────────────────────────────
// Internal event system for same-tab re-renders
// ────────────────────────────────────────────────────────────

const listeners = new Set<() => void>();

function notifyListeners(): void {
  listeners.forEach((fn) => fn());
}

function subscribe(onStoreChange: () => void): () => void {
  listeners.add(onStoreChange);
  // React to credential changes made by other tabs.
  const handleStorage = (e: StorageEvent) => {
    if (e.key === CREDENTIALS_STORAGE_KEY) {
      onStoreChange();
    }
  };
  window.addEventListener('storage', handleStorage);
  return () => {
    listeners.delete(onStoreChange);
    window.removeEventListener('storage', handleStorage);
  };
}

function getSnapshot(): boolean {
  return isAuthenticated();
}

function getServerSnapshot(): boolean {
  return false;
}

// ────────────────────────────────────────────────────────────
// React hook
// ────────────────────────────────────────────────────────────

export interface AuthState {
  isAuthenticated: boolean;
  signIn: (email: string, password: string, rememberMe?: boolean) => void;
  signOut: () => void;
}

/**
 * Client-side hook that reflects the current auth state and provides
 * sign-in / sign-out methods. Re-renders automatically when credentials
 * change (same tab or cross-tab via storage events).
 */
export function useAuth(): AuthState {
  const authed = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  const signIn = useCallback(
    (email: string, password: string, rememberMe = false) => {
      saveCredentials(email, password, rememberMe);
    },
    [],
  );

  const signOut = useCallback(() => {
    clearCredentials();
  }, []);

  return { isAuthenticated: authed, signIn, signOut };
}
