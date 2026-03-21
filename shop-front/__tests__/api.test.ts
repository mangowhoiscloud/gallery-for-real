/**
 * Tests for lib/api.ts — API client with auth and error handling.
 *
 * Strategy: mock global.fetch; verify URL, method, headers, and body for every
 * endpoint. Also test error handling (401 → AuthError, 404 → NotFoundError,
 * 5xx → ApiRequestError) and auth header injection from storage.
 */

import {
  CREDENTIALS_STORAGE_KEY,
  AuthError,
  NotFoundError,
  ApiRequestError,
  getProducts,
  searchProducts,
  getProductById,
  getCart,
  addToCart,
  updateCartItemQuantity,
  removeCartItem,
  clearCart,
  createOrder,
  getOrders,
  getOrderById,
  cancelOrder,
  login,
  register,
  getProfile,
  updateProfile,
} from '@/lib/api';
import {
  makeProduct,
  makeProductList,
  makePageResponse,
  makeCartResponse,
  makeOrder,
  makeMember,
  makeShippingAddress,
  makeCreateOrderPayload,
  makeRegisterPayload,
} from '@/lib/test-factories';

// ────────────────────────────────────────────────────────────
// Helpers
// ────────────────────────────────────────────────────────────

/** Build a minimal mock Response that resolves to the given JSON body. */
function mockJsonResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? 'OK' : String(status),
    json: () => Promise.resolve(body),
  } as unknown as Response;
}

/** Build a mock Response with no JSON body (for 204 No Content). */
function mock204Response(): Response {
  return {
    ok: true,
    status: 204,
    statusText: 'No Content',
    json: () => Promise.reject(new SyntaxError('no body')),
  } as unknown as Response;
}

/** Build a mock error Response that returns an API error body. */
function mockErrorResponse(
  status: number,
  message: string,
  hasJsonBody = true,
): Response {
  return {
    ok: false,
    status,
    statusText: message,
    json: hasJsonBody
      ? () => Promise.resolve({ message })
      : () => Promise.reject(new SyntaxError('no body')),
  } as unknown as Response;
}

/** Extract the Authorization header from the last fetch call. */
function lastCallAuthHeader(): string | undefined {
  const calls = (global.fetch as jest.Mock).mock.calls;
  const lastCall = calls[calls.length - 1];
  const headers = lastCall[1]?.headers as Record<string, string> | undefined;
  return headers?.['Authorization'];
}

/** Extract the parsed request body from the last fetch call. */
function lastCallBody(): unknown {
  const calls = (global.fetch as jest.Mock).mock.calls;
  const lastCall = calls[calls.length - 1];
  const raw = lastCall[1]?.body as string | undefined;
  return raw ? (JSON.parse(raw) as unknown) : undefined;
}

/** Extract the URL from the last fetch call. */
function lastCallUrl(): string {
  const calls = (global.fetch as jest.Mock).mock.calls;
  return calls[calls.length - 1][0] as string;
}

/** Extract the HTTP method from the last fetch call (defaults to GET). */
function lastCallMethod(): string {
  const calls = (global.fetch as jest.Mock).mock.calls;
  return ((calls[calls.length - 1][1]?.method as string) ?? 'GET').toUpperCase();
}

// ────────────────────────────────────────────────────────────
// Setup
// ────────────────────────────────────────────────────────────

beforeAll(() => {
  global.fetch = jest.fn();
});

beforeEach(() => {
  (global.fetch as jest.Mock).mockReset();
  window.localStorage.clear();
  window.sessionStorage.clear();
});

// ────────────────────────────────────────────────────────────
// 1. Core: Auth Header Injection
// ────────────────────────────────────────────────────────────

describe('auth header injection', () => {
  it('injects stored sessionStorage credentials as Basic header', async () => {
    const encoded = btoa('user@test.com:pass123');
    window.sessionStorage.setItem(CREDENTIALS_STORAGE_KEY, encoded);
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockJsonResponse(makeMember()),
    );

    await getProfile();

    expect(lastCallAuthHeader()).toBe(`Basic ${encoded}`);
  });

  it('injects stored localStorage credentials when sessionStorage is empty', async () => {
    const encoded = btoa('user@test.com:pass123');
    window.localStorage.setItem(CREDENTIALS_STORAGE_KEY, encoded);
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockJsonResponse(makeMember()),
    );

    await getProfile();

    expect(lastCallAuthHeader()).toBe(`Basic ${encoded}`);
  });

  it('prefers sessionStorage credentials over localStorage', async () => {
    const sessionEncoded = btoa('session@test.com:pass1');
    const localEncoded = btoa('local@test.com:pass2');
    window.sessionStorage.setItem(CREDENTIALS_STORAGE_KEY, sessionEncoded);
    window.localStorage.setItem(CREDENTIALS_STORAGE_KEY, localEncoded);
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockJsonResponse(makeMember()),
    );

    await getProfile();

    expect(lastCallAuthHeader()).toBe(`Basic ${sessionEncoded}`);
  });

  it('omits Authorization header when no credentials are stored', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockJsonResponse(makePageResponse(makeProductList(3))),
    );

    await getProducts();

    expect(lastCallAuthHeader()).toBeUndefined();
  });
});

// ────────────────────────────────────────────────────────────
// 2. Core: Error Handling
// ────────────────────────────────────────────────────────────

describe('error handling', () => {
  it('throws AuthError on 401 response', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockErrorResponse(401, 'Unauthorized'),
    );

    await expect(getProfile()).rejects.toThrow(AuthError);
  });

  it('AuthError carries the message from the JSON body', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockErrorResponse(401, 'Bad credentials'),
    );

    await expect(getProfile()).rejects.toMatchObject({
      name: 'AuthError',
      message: 'Bad credentials',
      status: 401,
    });
  });

  it('throws NotFoundError on 404 response', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockErrorResponse(404, 'Product not found'),
    );

    await expect(getProductById(999)).rejects.toThrow(NotFoundError);
  });

  it('NotFoundError carries status 404', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockErrorResponse(404, 'Not Found'),
    );

    await expect(getProductById(1)).rejects.toMatchObject({ status: 404 });
  });

  it('throws ApiRequestError on 500 response', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockErrorResponse(500, 'Internal Server Error'),
    );

    await expect(getCart()).rejects.toThrow(ApiRequestError);
  });

  it('ApiRequestError carries the HTTP status code', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockErrorResponse(503, 'Service Unavailable'),
    );

    await expect(getCart()).rejects.toMatchObject({ status: 503 });
  });

  it('falls back to statusText when error response body has no JSON', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockErrorResponse(500, 'Internal Server Error', false),
    );

    await expect(getCart()).rejects.toMatchObject({
      message: 'Internal Server Error',
    });
  });

  it('propagates network errors (fetch rejects)', async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new TypeError('Failed to fetch'));

    await expect(getCart()).rejects.toThrow('Failed to fetch');
  });

  it('returns undefined for 204 No Content responses', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(mock204Response());

    const result = await clearCart();

    expect(result).toBeUndefined();
  });
});

// ────────────────────────────────────────────────────────────
// 3. Products
// ────────────────────────────────────────────────────────────

describe('getProducts()', () => {
  it('calls GET /api/products', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockJsonResponse(makePageResponse(makeProductList(3))),
    );

    await getProducts();

    expect(lastCallUrl()).toBe('/api/products');
    expect(lastCallMethod()).toBe('GET');
  });

  it('appends page and size query params when provided', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockJsonResponse(makePageResponse(makeProductList(2))),
    );

    await getProducts({ page: 2, size: 6 });

    expect(lastCallUrl()).toBe('/api/products?page=2&size=6');
  });

  it('returns a PageResponse of Products', async () => {
    const page = makePageResponse(makeProductList(3));
    (global.fetch as jest.Mock).mockResolvedValueOnce(mockJsonResponse(page));

    const result = await getProducts();

    expect(result.content).toHaveLength(3);
    expect(result.totalPages).toBe(1);
  });
});

describe('searchProducts()', () => {
  it('calls GET /api/products/search', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockJsonResponse(makePageResponse([])),
    );

    await searchProducts();

    expect(lastCallUrl()).toBe('/api/products/search');
    expect(lastCallMethod()).toBe('GET');
  });

  it('appends all provided search params as query string', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockJsonResponse(makePageResponse([])),
    );

    await searchProducts({
      keyword: 'phone',
      category: 'Electronics',
      minPrice: 100,
      maxPrice: 500,
      sortBy: 'price',
      sortDir: 'asc',
      page: 0,
      size: 12,
    });

    const url = lastCallUrl();
    expect(url).toContain('keyword=phone');
    expect(url).toContain('category=Electronics');
    expect(url).toContain('minPrice=100');
    expect(url).toContain('maxPrice=500');
    expect(url).toContain('sortBy=price');
    expect(url).toContain('sortDir=asc');
  });

  it('omits undefined params from the query string', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockJsonResponse(makePageResponse([])),
    );

    await searchProducts({ keyword: 'shirt' });

    const url = lastCallUrl();
    expect(url).toContain('keyword=shirt');
    expect(url).not.toContain('category=');
    expect(url).not.toContain('minPrice=');
  });
});

describe('getProductById()', () => {
  it('calls GET /api/products/{id}', async () => {
    const product = makeProduct({ id: 42 });
    (global.fetch as jest.Mock).mockResolvedValueOnce(mockJsonResponse(product));

    const result = await getProductById(42);

    expect(lastCallUrl()).toBe('/api/products/42');
    expect(lastCallMethod()).toBe('GET');
    expect(result.id).toBe(42);
  });
});

// ────────────────────────────────────────────────────────────
// 4. Cart
// ────────────────────────────────────────────────────────────

describe('getCart()', () => {
  it('calls GET /api/cart with auth header', async () => {
    const encoded = btoa('user@test.com:pass');
    window.sessionStorage.setItem(CREDENTIALS_STORAGE_KEY, encoded);
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockJsonResponse(makeCartResponse()),
    );

    await getCart();

    expect(lastCallUrl()).toBe('/api/cart');
    expect(lastCallMethod()).toBe('GET');
    expect(lastCallAuthHeader()).toBe(`Basic ${encoded}`);
  });

  it('returns a CartResponse', async () => {
    const cart = makeCartResponse({ totalPrice: 99.99 });
    (global.fetch as jest.Mock).mockResolvedValueOnce(mockJsonResponse(cart));

    const result = await getCart();

    expect(result.totalPrice).toBe(99.99);
    expect(result.items).toHaveLength(1);
  });
});

describe('addToCart()', () => {
  it('calls POST /api/cart/items with productId and quantity', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockJsonResponse(makeCartResponse()),
    );

    await addToCart(5, 3);

    expect(lastCallUrl()).toBe('/api/cart/items');
    expect(lastCallMethod()).toBe('POST');
    expect(lastCallBody()).toEqual({ productId: 5, quantity: 3 });
  });
});

describe('updateCartItemQuantity()', () => {
  it('calls PUT /api/cart/items/{id} with quantity', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockJsonResponse(makeCartResponse()),
    );

    await updateCartItemQuantity(7, 2);

    expect(lastCallUrl()).toBe('/api/cart/items/7');
    expect(lastCallMethod()).toBe('PUT');
    expect(lastCallBody()).toEqual({ quantity: 2 });
  });
});

describe('removeCartItem()', () => {
  it('calls DELETE /api/cart/items/{id}', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(mock204Response());

    await removeCartItem(3);

    expect(lastCallUrl()).toBe('/api/cart/items/3');
    expect(lastCallMethod()).toBe('DELETE');
  });
});

describe('clearCart()', () => {
  it('calls DELETE /api/cart', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(mock204Response());

    await clearCart();

    expect(lastCallUrl()).toBe('/api/cart');
    expect(lastCallMethod()).toBe('DELETE');
  });
});

// ────────────────────────────────────────────────────────────
// 5. Orders
// ────────────────────────────────────────────────────────────

describe('createOrder()', () => {
  it('calls POST /api/orders with the CreateOrderPayload', async () => {
    const payload = makeCreateOrderPayload();
    const order = makeOrder();
    (global.fetch as jest.Mock).mockResolvedValueOnce(mockJsonResponse(order));

    const result = await createOrder(payload);

    expect(lastCallUrl()).toBe('/api/orders');
    expect(lastCallMethod()).toBe('POST');
    expect(lastCallBody()).toEqual(payload);
    expect(result.id).toBe(order.id);
  });

  it('includes the shipping address in the request body', async () => {
    const address = makeShippingAddress({ city: 'Chicago', state: 'IL' });
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockJsonResponse(makeOrder()),
    );

    await createOrder({ shippingAddress: address });

    const body = lastCallBody() as { shippingAddress: typeof address };
    expect(body.shippingAddress.city).toBe('Chicago');
    expect(body.shippingAddress.state).toBe('IL');
  });
});

describe('getOrders()', () => {
  it('calls GET /api/orders with default page=0 and size=10', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockJsonResponse(makePageResponse([makeOrder()])),
    );

    await getOrders();

    expect(lastCallUrl()).toBe('/api/orders?page=0&size=10');
    expect(lastCallMethod()).toBe('GET');
  });

  it('accepts custom page and size', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockJsonResponse(makePageResponse([])),
    );

    await getOrders(2, 5);

    expect(lastCallUrl()).toBe('/api/orders?page=2&size=5');
  });

  it('returns a PageResponse of Orders', async () => {
    const page = makePageResponse([makeOrder(), makeOrder({ id: 1002 })]);
    (global.fetch as jest.Mock).mockResolvedValueOnce(mockJsonResponse(page));

    const result = await getOrders();

    expect(result.content).toHaveLength(2);
  });
});

describe('getOrderById()', () => {
  it('calls GET /api/orders/{id}', async () => {
    const order = makeOrder({ id: 555 });
    (global.fetch as jest.Mock).mockResolvedValueOnce(mockJsonResponse(order));

    const result = await getOrderById(555);

    expect(lastCallUrl()).toBe('/api/orders/555');
    expect(lastCallMethod()).toBe('GET');
    expect(result.id).toBe(555);
  });
});

describe('cancelOrder()', () => {
  it('calls PUT /api/orders/{id}/cancel', async () => {
    const cancelled = makeOrder({ status: 'CANCELLED' });
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockJsonResponse(cancelled),
    );

    const result = await cancelOrder(1001);

    expect(lastCallUrl()).toBe('/api/orders/1001/cancel');
    expect(lastCallMethod()).toBe('PUT');
    expect(result.status).toBe('CANCELLED');
  });
});

// ────────────────────────────────────────────────────────────
// 6. Auth
// ────────────────────────────────────────────────────────────

describe('login()', () => {
  it('calls POST /api/members/login', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockJsonResponse(makeMember()),
    );

    await login('user@test.com', 'secret');

    expect(lastCallUrl()).toBe('/api/members/login');
    expect(lastCallMethod()).toBe('POST');
  });

  it('sends the provided credentials as a Basic Auth header (not stored creds)', async () => {
    // Put different credentials in storage — login must ignore them
    const storedEncoded = btoa('other@test.com:otherpass');
    window.sessionStorage.setItem(CREDENTIALS_STORAGE_KEY, storedEncoded);

    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockJsonResponse(makeMember()),
    );

    await login('user@test.com', 'secret');

    const expectedHeader = `Basic ${btoa('user@test.com:secret')}`;
    expect(lastCallAuthHeader()).toBe(expectedHeader);
    // Must NOT use the stored credentials
    expect(lastCallAuthHeader()).not.toBe(`Basic ${storedEncoded}`);
  });

  it('Base64-encodes email:password correctly', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockJsonResponse(makeMember()),
    );

    await login('alice@example.com', 'p@$$w0rd');

    const expectedEncoded = btoa('alice@example.com:p@$$w0rd');
    expect(lastCallAuthHeader()).toBe(`Basic ${expectedEncoded}`);
  });

  it('returns a Member on success', async () => {
    const member = makeMember({ name: 'Alice', email: 'alice@example.com' });
    (global.fetch as jest.Mock).mockResolvedValueOnce(mockJsonResponse(member));

    const result = await login('alice@example.com', 'pass');

    expect(result.email).toBe('alice@example.com');
    expect(result.name).toBe('Alice');
  });
});

describe('register()', () => {
  it('calls POST /api/members without an Authorization header', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockJsonResponse(makeMember()),
    );

    const payload = makeRegisterPayload();
    await register(payload);

    expect(lastCallUrl()).toBe('/api/members');
    expect(lastCallMethod()).toBe('POST');
    expect(lastCallAuthHeader()).toBeUndefined();
  });

  it('sends the registration payload in the request body', async () => {
    const payload = makeRegisterPayload({
      name: 'Bob',
      email: 'bob@example.com',
      password: 'bobspass',
    });
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockJsonResponse(makeMember()),
    );

    await register(payload);

    expect(lastCallBody()).toEqual(payload);
  });

  it('returns the new Member on success', async () => {
    const member = makeMember({ name: 'Bob', email: 'bob@example.com' });
    (global.fetch as jest.Mock).mockResolvedValueOnce(mockJsonResponse(member));

    const result = await register(makeRegisterPayload({ name: 'Bob' }));

    expect(result.name).toBe('Bob');
  });
});

// ────────────────────────────────────────────────────────────
// 7. Members
// ────────────────────────────────────────────────────────────

describe('getProfile()', () => {
  it('calls GET /api/members/me', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockJsonResponse(makeMember()),
    );

    await getProfile();

    expect(lastCallUrl()).toBe('/api/members/me');
    expect(lastCallMethod()).toBe('GET');
  });

  it('returns the authenticated member', async () => {
    const member = makeMember({ name: 'Carol', email: 'carol@example.com' });
    (global.fetch as jest.Mock).mockResolvedValueOnce(mockJsonResponse(member));

    const result = await getProfile();

    expect(result.name).toBe('Carol');
  });
});

describe('updateProfile()', () => {
  it('calls PUT /api/members/me with the update payload', async () => {
    const updated = makeMember({ name: 'Updated Name', phone: '555-1234' });
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockJsonResponse(updated),
    );

    await updateProfile({ name: 'Updated Name', phone: '555-1234' });

    expect(lastCallUrl()).toBe('/api/members/me');
    expect(lastCallMethod()).toBe('PUT');
    expect(lastCallBody()).toEqual({ name: 'Updated Name', phone: '555-1234' });
  });

  it('returns the updated Member', async () => {
    const member = makeMember({ phone: '555-9999' });
    (global.fetch as jest.Mock).mockResolvedValueOnce(mockJsonResponse(member));

    const result = await updateProfile({ phone: '555-9999' });

    expect(result.phone).toBe('555-9999');
  });
});

// ────────────────────────────────────────────────────────────
// 8. PageResponse parsing
// ────────────────────────────────────────────────────────────

describe('PageResponse parsing', () => {
  it('correctly exposes all Spring Boot Page fields', async () => {
    const page = makePageResponse(makeProductList(5), {
      totalElements: 50,
      totalPages: 5,
      size: 10,
      number: 1,
      first: false,
      last: false,
    });
    (global.fetch as jest.Mock).mockResolvedValueOnce(mockJsonResponse(page));

    const result = await getProducts({ page: 1, size: 10 });

    expect(result.totalElements).toBe(50);
    expect(result.totalPages).toBe(5);
    expect(result.size).toBe(10);
    expect(result.number).toBe(1);
    expect(result.first).toBe(false);
    expect(result.last).toBe(false);
    expect(result.content).toHaveLength(5);
  });
});
