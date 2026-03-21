/**
 * Test factory functions for creating mock domain objects.
 * All factories accept a partial override so individual fields can be
 * customised in specific tests without repeating boilerplate.
 */

import type {
  Product,
  CartItem,
  CartResponse,
  OrderItem,
  Order,
  Member,
  ShippingAddress,
  PageResponse,
  AuthCredentials,
  ProductSearchParams,
  CreateOrderPayload,
  RegisterPayload,
} from '@/lib/types';

// ────────────────────────────────────────────────────────────
// Primitive factories
// ────────────────────────────────────────────────────────────

export function makeProduct(overrides: Partial<Product> = {}): Product {
  return {
    id: 1,
    name: 'Test Product',
    price: 29.99,
    description: 'A product used in tests.',
    imageUrl: 'https://example.com/image.jpg',
    category: 'Electronics',
    stockQuantity: 10,
    createdAt: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

export function makeShippingAddress(
  overrides: Partial<ShippingAddress> = {},
): ShippingAddress {
  return {
    name: 'John Doe',
    addressLine1: '123 Main St',
    city: 'Springfield',
    state: 'IL',
    zipCode: '62701',
    country: 'US',
    ...overrides,
  };
}

export function makeOrderItem(overrides: Partial<OrderItem> = {}): OrderItem {
  return {
    id: 1,
    productId: 1,
    productName: 'Test Product',
    quantity: 2,
    price: 29.99,
    ...overrides,
  };
}

export function makeOrder(overrides: Partial<Order> = {}): Order {
  return {
    id: 1001,
    items: [makeOrderItem()],
    totalAmount: 59.98,
    status: 'PENDING',
    shippingAddress: makeShippingAddress(),
    createdAt: '2026-03-01T12:00:00Z',
    ...overrides,
  };
}

export function makeCartItem(overrides: Partial<CartItem> = {}): CartItem {
  return {
    id: 1,
    product: makeProduct(),
    quantity: 1,
    ...overrides,
  };
}

export function makeCartResponse(
  overrides: Partial<CartResponse> = {},
): CartResponse {
  return {
    id: 1,
    items: [makeCartItem()],
    totalPrice: 29.99,
    ...overrides,
  };
}

export function makeMember(overrides: Partial<Member> = {}): Member {
  return {
    id: 42,
    email: 'user@example.com',
    name: 'Test User',
    ...overrides,
  };
}

export function makeAuthCredentials(
  overrides: Partial<AuthCredentials> = {},
): AuthCredentials {
  return {
    email: 'user@example.com',
    password: 'password123',
    ...overrides,
  };
}

export function makeProductSearchParams(
  overrides: Partial<ProductSearchParams> = {},
): ProductSearchParams {
  return {
    page: 0,
    size: 12,
    ...overrides,
  };
}

export function makeCreateOrderPayload(
  overrides: Partial<CreateOrderPayload> = {},
): CreateOrderPayload {
  return {
    shippingAddress: makeShippingAddress(),
    ...overrides,
  };
}

export function makeRegisterPayload(
  overrides: Partial<RegisterPayload> = {},
): RegisterPayload {
  return {
    name: 'Test User',
    email: 'newuser@example.com',
    password: 'securepass',
    ...overrides,
  };
}

// ────────────────────────────────────────────────────────────
// Collection factories
// ────────────────────────────────────────────────────────────

export function makePageResponse<T>(
  items: T[],
  overrides: Partial<Omit<PageResponse<T>, 'content'>> = {},
): PageResponse<T> {
  return {
    content: items,
    totalElements: items.length,
    totalPages: 1,
    size: 12,
    number: 0,
    first: true,
    last: true,
    ...overrides,
  };
}

/** Create N products with sequential IDs */
export function makeProductList(count: number): Product[] {
  return Array.from({ length: count }, (_, i) =>
    makeProduct({ id: i + 1, name: `Product ${i + 1}` }),
  );
}
