import { renderHook, act } from '@testing-library/react';
import {
  saveCredentials,
  getCredentials,
  clearCredentials,
  isAuthenticated,
  getAuthHeader,
  useAuth,
  REMEMBER_ME_KEY,
} from '../lib/auth';
import { CREDENTIALS_STORAGE_KEY } from '../lib/api';

// ────────────────────────────────────────────────────────────
// Utility function tests
// ────────────────────────────────────────────────────────────

describe('saveCredentials', () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    window.localStorage.clear();
  });

  it('stores Base64-encoded credentials in sessionStorage by default', () => {
    saveCredentials('user@example.com', 'pass123');
    const stored = window.sessionStorage.getItem(CREDENTIALS_STORAGE_KEY);
    expect(stored).toBe(btoa('user@example.com:pass123'));
  });

  it('does not write to localStorage when rememberMe is false', () => {
    saveCredentials('user@example.com', 'pass123');
    expect(window.localStorage.getItem(CREDENTIALS_STORAGE_KEY)).toBeNull();
  });

  it('stores in localStorage when rememberMe=true', () => {
    saveCredentials('user@example.com', 'pass123', true);
    const stored = window.localStorage.getItem(CREDENTIALS_STORAGE_KEY);
    expect(stored).toBe(btoa('user@example.com:pass123'));
  });

  it('does not write to sessionStorage when rememberMe=true', () => {
    saveCredentials('user@example.com', 'pass123', true);
    expect(window.sessionStorage.getItem(CREDENTIALS_STORAGE_KEY)).toBeNull();
  });

  it('sets REMEMBER_ME_KEY in localStorage when rememberMe=true', () => {
    saveCredentials('user@example.com', 'pass123', true);
    expect(window.localStorage.getItem(REMEMBER_ME_KEY)).toBe('1');
  });

  it('clears localStorage key when switching back to session (rememberMe=false)', () => {
    saveCredentials('user@example.com', 'pass123', true);
    saveCredentials('user@example.com', 'pass123', false);
    expect(window.localStorage.getItem(CREDENTIALS_STORAGE_KEY)).toBeNull();
    expect(window.sessionStorage.getItem(CREDENTIALS_STORAGE_KEY)).not.toBeNull();
  });

  it('removes REMEMBER_ME_KEY when rememberMe=false', () => {
    saveCredentials('user@example.com', 'pass123', true);
    saveCredentials('user@example.com', 'pass123', false);
    expect(window.localStorage.getItem(REMEMBER_ME_KEY)).toBeNull();
  });
});

describe('getCredentials', () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    window.localStorage.clear();
  });

  it('returns null when nothing is stored', () => {
    expect(getCredentials()).toBeNull();
  });

  it('returns credentials from sessionStorage', () => {
    saveCredentials('user@example.com', 'mypassword');
    expect(getCredentials()).toEqual({
      email: 'user@example.com',
      password: 'mypassword',
    });
  });

  it('returns credentials from localStorage when rememberMe=true', () => {
    saveCredentials('user@example.com', 'mypassword', true);
    expect(getCredentials()).toEqual({
      email: 'user@example.com',
      password: 'mypassword',
    });
  });

  it('prefers sessionStorage over localStorage', () => {
    window.sessionStorage.setItem(
      CREDENTIALS_STORAGE_KEY,
      btoa('session@test.com:pass1'),
    );
    window.localStorage.setItem(
      CREDENTIALS_STORAGE_KEY,
      btoa('local@test.com:pass2'),
    );
    expect(getCredentials()).toEqual({
      email: 'session@test.com',
      password: 'pass1',
    });
  });

  it('handles passwords that contain colon characters', () => {
    saveCredentials('user@example.com', 'pass:with:colons');
    expect(getCredentials()).toEqual({
      email: 'user@example.com',
      password: 'pass:with:colons',
    });
  });
});

describe('clearCredentials', () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    window.localStorage.clear();
  });

  it('removes credentials from sessionStorage', () => {
    saveCredentials('user@example.com', 'pass');
    clearCredentials();
    expect(window.sessionStorage.getItem(CREDENTIALS_STORAGE_KEY)).toBeNull();
  });

  it('removes credentials from localStorage', () => {
    saveCredentials('user@example.com', 'pass', true);
    clearCredentials();
    expect(window.localStorage.getItem(CREDENTIALS_STORAGE_KEY)).toBeNull();
  });

  it('removes REMEMBER_ME_KEY from localStorage', () => {
    saveCredentials('user@example.com', 'pass', true);
    clearCredentials();
    expect(window.localStorage.getItem(REMEMBER_ME_KEY)).toBeNull();
  });

  it('getCredentials returns null after clear', () => {
    saveCredentials('user@example.com', 'pass');
    clearCredentials();
    expect(getCredentials()).toBeNull();
  });
});

describe('isAuthenticated', () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    window.localStorage.clear();
  });

  it('returns false when no credentials are stored', () => {
    expect(isAuthenticated()).toBe(false);
  });

  it('returns true when credentials are in sessionStorage', () => {
    saveCredentials('user@example.com', 'pass');
    expect(isAuthenticated()).toBe(true);
  });

  it('returns true when credentials are in localStorage', () => {
    saveCredentials('user@example.com', 'pass', true);
    expect(isAuthenticated()).toBe(true);
  });

  it('returns false after clearCredentials', () => {
    saveCredentials('user@example.com', 'pass');
    clearCredentials();
    expect(isAuthenticated()).toBe(false);
  });
});

describe('getAuthHeader', () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    window.localStorage.clear();
  });

  it('returns null when not authenticated', () => {
    expect(getAuthHeader()).toBeNull();
  });

  it('returns Basic auth header from sessionStorage credentials', () => {
    saveCredentials('user@example.com', 'pass123');
    expect(getAuthHeader()).toBe(`Basic ${btoa('user@example.com:pass123')}`);
  });

  it('returns Basic auth header from localStorage credentials', () => {
    saveCredentials('user@example.com', 'pass123', true);
    expect(getAuthHeader()).toBe(`Basic ${btoa('user@example.com:pass123')}`);
  });

  it('returns null after clearCredentials', () => {
    saveCredentials('user@example.com', 'pass');
    clearCredentials();
    expect(getAuthHeader()).toBeNull();
  });
});

// ────────────────────────────────────────────────────────────
// useAuth hook tests
// ────────────────────────────────────────────────────────────

describe('useAuth hook', () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    window.localStorage.clear();
  });

  it('isAuthenticated is false initially when no credentials exist', () => {
    const { result } = renderHook(() => useAuth());
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('isAuthenticated is true when credentials already exist at mount', () => {
    saveCredentials('user@example.com', 'pass');
    const { result } = renderHook(() => useAuth());
    expect(result.current.isAuthenticated).toBe(true);
  });

  it('signIn sets isAuthenticated to true and triggers re-render', () => {
    const { result } = renderHook(() => useAuth());
    expect(result.current.isAuthenticated).toBe(false);
    act(() => {
      result.current.signIn('user@example.com', 'pass123');
    });
    expect(result.current.isAuthenticated).toBe(true);
  });

  it('signOut sets isAuthenticated to false and triggers re-render', () => {
    saveCredentials('user@example.com', 'pass');
    const { result } = renderHook(() => useAuth());
    expect(result.current.isAuthenticated).toBe(true);
    act(() => {
      result.current.signOut();
    });
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('signIn with rememberMe=true stores credentials in localStorage', () => {
    const { result } = renderHook(() => useAuth());
    act(() => {
      result.current.signIn('user@example.com', 'pass', true);
    });
    expect(window.localStorage.getItem(CREDENTIALS_STORAGE_KEY)).not.toBeNull();
    expect(window.sessionStorage.getItem(CREDENTIALS_STORAGE_KEY)).toBeNull();
  });

  it('signIn without rememberMe stores credentials in sessionStorage', () => {
    const { result } = renderHook(() => useAuth());
    act(() => {
      result.current.signIn('user@example.com', 'pass');
    });
    expect(window.sessionStorage.getItem(CREDENTIALS_STORAGE_KEY)).not.toBeNull();
    expect(window.localStorage.getItem(CREDENTIALS_STORAGE_KEY)).toBeNull();
  });
});
