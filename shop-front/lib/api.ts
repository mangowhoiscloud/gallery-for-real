import type {
  Product,
  CartResponse,
  Order,
  Member,
  PageResponse,
  ProductSearchParams,
  RegisterPayload,
  UpdateProfilePayload,
  CreateOrderPayload,
} from './types';

// ────────────────────────────────────────────────────────────
// Constants
// ────────────────────────────────────────────────────────────

/**
 * localStorage / sessionStorage key holding the Base64-encoded credentials.
 * auth.ts uses this same key when saving credentials.
 */
export const CREDENTIALS_STORAGE_KEY = 'shop_credentials';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? '';

// ────────────────────────────────────────────────────────────
// Error Classes
// ────────────────────────────────────────────────────────────

export class AuthError extends Error {
  readonly status = 401;
  constructor(message = 'Unauthorized') {
    super(message);
    this.name = 'AuthError';
  }
}

export class NotFoundError extends Error {
  readonly status = 404;
  constructor(message = 'Not Found') {
    super(message);
    this.name = 'NotFoundError';
  }
}

export class ApiRequestError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiRequestError';
  }
}

// ────────────────────────────────────────────────────────────
// Auth Header Helper
// ────────────────────────────────────────────────────────────

/**
 * Reads the stored Base64-encoded credentials from sessionStorage (primary)
 * or localStorage (remember-me) and returns the Authorization header value,
 * or null when the user is not authenticated.
 */
function getStoredAuthHeader(): string | null {
  if (typeof window === 'undefined') return null;
  const encoded =
    window.sessionStorage.getItem(CREDENTIALS_STORAGE_KEY) ??
    window.localStorage.getItem(CREDENTIALS_STORAGE_KEY);
  return encoded ? `Basic ${encoded}` : null;
}

// ────────────────────────────────────────────────────────────
// Core Fetch Wrapper
// ────────────────────────────────────────────────────────────

interface RequestOptions extends RequestInit {
  /** Inject stored Basic Auth header. Defaults to true. */
  auth?: boolean;
  /** Explicit Authorization header value (overrides stored credentials). */
  authOverride?: string;
}

async function request<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { auth = true, authOverride, ...init } = options;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init.headers as Record<string, string>),
  };

  if (authOverride) {
    headers['Authorization'] = authOverride;
  } else if (auth) {
    const storedHeader = getStoredAuthHeader();
    if (storedHeader) headers['Authorization'] = storedHeader;
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...init, headers });

  if (!res.ok) {
    let message = res.statusText;
    try {
      const body = (await res.json()) as { message?: string };
      if (body.message) message = body.message;
    } catch {
      // ignore JSON parse errors on error responses
    }
    if (res.status === 401) throw new AuthError(message);
    if (res.status === 404) throw new NotFoundError(message);
    throw new ApiRequestError(res.status, message);
  }

  // 204 No Content — no body to parse
  if (res.status === 204) return undefined as unknown as T;

  return res.json() as Promise<T>;
}

// ────────────────────────────────────────────────────────────
// Query String Builder
// ────────────────────────────────────────────────────────────

function buildQuery(params: Record<string, unknown>): string {
  const entries = Object.entries(params).filter(
    ([, v]) => v !== undefined && v !== null && v !== '',
  );
  if (entries.length === 0) return '';
  return (
    '?' +
    new URLSearchParams(entries.map(([k, v]) => [k, String(v)])).toString()
  );
}

// ────────────────────────────────────────────────────────────
// Products
// ────────────────────────────────────────────────────────────

export function getProducts(
  params: { page?: number; size?: number } = {},
): Promise<PageResponse<Product>> {
  return request<PageResponse<Product>>(`/api/products${buildQuery(params)}`);
}

export function searchProducts(
  params: ProductSearchParams = {},
): Promise<PageResponse<Product>> {
  return request<PageResponse<Product>>(
    `/api/products/search${buildQuery(params as Record<string, unknown>)}`,
  );
}

export function getProductById(id: number): Promise<Product> {
  return request<Product>(`/api/products/${id}`);
}

// ────────────────────────────────────────────────────────────
// Cart
// ────────────────────────────────────────────────────────────

export function getCart(): Promise<CartResponse> {
  return request<CartResponse>('/api/cart');
}

export function addToCart(
  productId: number,
  quantity: number,
): Promise<CartResponse> {
  return request<CartResponse>('/api/cart/items', {
    method: 'POST',
    body: JSON.stringify({ productId, quantity }),
  });
}

export function updateCartItemQuantity(
  cartItemId: number,
  quantity: number,
): Promise<CartResponse> {
  return request<CartResponse>(`/api/cart/items/${cartItemId}`, {
    method: 'PUT',
    body: JSON.stringify({ quantity }),
  });
}

export function removeCartItem(cartItemId: number): Promise<void> {
  return request<void>(`/api/cart/items/${cartItemId}`, { method: 'DELETE' });
}

export function clearCart(): Promise<void> {
  return request<void>('/api/cart', { method: 'DELETE' });
}

// ────────────────────────────────────────────────────────────
// Orders
// ────────────────────────────────────────────────────────────

export function createOrder(payload: CreateOrderPayload): Promise<Order> {
  return request<Order>('/api/orders', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function getOrders(page = 0, size = 10): Promise<PageResponse<Order>> {
  return request<PageResponse<Order>>(
    `/api/orders${buildQuery({ page, size })}`,
  );
}

export function getOrderById(id: number): Promise<Order> {
  return request<Order>(`/api/orders/${id}`);
}

export function cancelOrder(id: number): Promise<Order> {
  return request<Order>(`/api/orders/${id}/cancel`, { method: 'PUT' });
}

// ────────────────────────────────────────────────────────────
// Auth
// ────────────────────────────────────────────────────────────

export function login(email: string, password: string): Promise<Member> {
  const encoded = btoa(`${email}:${password}`);
  return request<Member>('/api/members/login', {
    method: 'POST',
    auth: false,
    authOverride: `Basic ${encoded}`,
  });
}

export function register(payload: RegisterPayload): Promise<Member> {
  return request<Member>('/api/members', {
    method: 'POST',
    auth: false,
    body: JSON.stringify(payload),
  });
}

// ────────────────────────────────────────────────────────────
// Members
// ────────────────────────────────────────────────────────────

export function getProfile(): Promise<Member> {
  return request<Member>('/api/members/me');
}

export function updateProfile(data: UpdateProfilePayload): Promise<Member> {
  return request<Member>('/api/members/me', {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}
