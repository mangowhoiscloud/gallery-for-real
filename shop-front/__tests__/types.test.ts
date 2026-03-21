/**
 * Tests for lib/types.ts — verifies factory functions produce correctly shaped
 * objects and that TypeScript interfaces compile without `any` leaks.
 *
 * These are runtime shape tests; TypeScript strict-mode compilation is the
 * primary type safety guarantee (checked via `npm run build`).
 */

import {
  makeProduct,
  makeCartItem,
  makeCartResponse,
  makeOrderItem,
  makeOrder,
  makeMember,
  makeShippingAddress,
  makePageResponse,
  makeProductList,
  makeAuthCredentials,
  makeCreateOrderPayload,
  makeRegisterPayload,
} from '@/lib/test-factories';
import type {
  Product,
  CartItem,
  CartResponse,
  OrderItem,
  Order,
  Member,
  ShippingAddress,
  PageResponse,
  OrderStatus,
} from '@/lib/types';

// ────────────────────────────────────────────────────────────
// Product
// ────────────────────────────────────────────────────────────

describe('makeProduct', () => {
  it('returns a valid Product shape', () => {
    const product = makeProduct();
    expect(typeof product.id).toBe('number');
    expect(typeof product.name).toBe('string');
    expect(typeof product.price).toBe('number');
    expect(typeof product.description).toBe('string');
    expect(typeof product.imageUrl).toBe('string');
    expect(typeof product.category).toBe('string');
    expect(typeof product.stockQuantity).toBe('number');
    expect(typeof product.createdAt).toBe('string');
  });

  it('applies overrides correctly', () => {
    const product = makeProduct({ id: 99, name: 'Override', stockQuantity: 0 });
    expect(product.id).toBe(99);
    expect(product.name).toBe('Override');
    expect(product.stockQuantity).toBe(0);
    // Non-overridden fields retain defaults
    expect(product.price).toBe(29.99);
  });

  it('can represent an out-of-stock product', () => {
    const product = makeProduct({ stockQuantity: 0 });
    expect(product.stockQuantity).toBe(0);
  });

  it('can represent a low-stock product', () => {
    const product = makeProduct({ stockQuantity: 3 });
    expect(product.stockQuantity).toBeLessThanOrEqual(5);
    expect(product.stockQuantity).toBeGreaterThan(0);
  });
});

// ────────────────────────────────────────────────────────────
// CartItem / CartResponse
// ────────────────────────────────────────────────────────────

describe('makeCartItem', () => {
  it('returns a CartItem with nested Product', () => {
    const item = makeCartItem();
    expect(typeof item.id).toBe('number');
    expect(typeof item.quantity).toBe('number');
    expect(item.product).toBeDefined();
    expect(typeof item.product.id).toBe('number');
  });

  it('applies overrides', () => {
    const product = makeProduct({ id: 5, name: 'Special' });
    const item = makeCartItem({ product, quantity: 3 });
    expect(item.product.name).toBe('Special');
    expect(item.quantity).toBe(3);
  });
});

describe('makeCartResponse', () => {
  it('returns a CartResponse with items array and totalPrice', () => {
    const cart = makeCartResponse();
    expect(Array.isArray(cart.items)).toBe(true);
    expect(cart.items.length).toBeGreaterThan(0);
    expect(typeof cart.totalPrice).toBe('number');
  });

  it('can represent an empty cart', () => {
    const cart = makeCartResponse({ items: [], totalPrice: 0 });
    expect(cart.items).toHaveLength(0);
    expect(cart.totalPrice).toBe(0);
  });
});

// ────────────────────────────────────────────────────────────
// Order / OrderItem / ShippingAddress
// ────────────────────────────────────────────────────────────

describe('makeShippingAddress', () => {
  it('returns a valid ShippingAddress', () => {
    const addr = makeShippingAddress();
    expect(typeof addr.name).toBe('string');
    expect(typeof addr.addressLine1).toBe('string');
    expect(typeof addr.city).toBe('string');
    expect(typeof addr.state).toBe('string');
    expect(typeof addr.zipCode).toBe('string');
    expect(typeof addr.country).toBe('string');
  });

  it('addressLine2 is optional (undefined by default)', () => {
    const addr = makeShippingAddress();
    expect(addr.addressLine2).toBeUndefined();
  });

  it('accepts addressLine2 override', () => {
    const addr = makeShippingAddress({ addressLine2: 'Apt 4B' });
    expect(addr.addressLine2).toBe('Apt 4B');
  });
});

describe('makeOrderItem', () => {
  it('returns a valid OrderItem', () => {
    const item = makeOrderItem();
    expect(typeof item.id).toBe('number');
    expect(typeof item.productId).toBe('number');
    expect(typeof item.productName).toBe('string');
    expect(typeof item.quantity).toBe('number');
    expect(typeof item.price).toBe('number');
  });
});

describe('makeOrder', () => {
  const VALID_STATUSES: OrderStatus[] = [
    'PENDING',
    'CONFIRMED',
    'SHIPPED',
    'DELIVERED',
    'CANCELLED',
  ];

  it('returns a valid Order shape', () => {
    const order = makeOrder();
    expect(typeof order.id).toBe('number');
    expect(Array.isArray(order.items)).toBe(true);
    expect(typeof order.totalAmount).toBe('number');
    expect(VALID_STATUSES).toContain(order.status);
    expect(typeof order.shippingAddress).toBe('object');
    expect(typeof order.createdAt).toBe('string');
  });

  it('supports all valid order statuses', () => {
    for (const status of VALID_STATUSES) {
      const order = makeOrder({ status });
      expect(order.status).toBe(status);
    }
  });

  it('applies overrides', () => {
    const order = makeOrder({ status: 'CANCELLED', totalAmount: 0 });
    expect(order.status).toBe('CANCELLED');
    expect(order.totalAmount).toBe(0);
  });
});

// ────────────────────────────────────────────────────────────
// Member
// ────────────────────────────────────────────────────────────

describe('makeMember', () => {
  it('returns a valid Member shape', () => {
    const member = makeMember();
    expect(typeof member.id).toBe('number');
    expect(typeof member.email).toBe('string');
    expect(typeof member.name).toBe('string');
  });

  it('phone and address are optional (undefined by default)', () => {
    const member = makeMember();
    expect(member.phone).toBeUndefined();
    expect(member.address).toBeUndefined();
  });

  it('accepts optional fields', () => {
    const member = makeMember({ phone: '555-1234', address: '1 Main St' });
    expect(member.phone).toBe('555-1234');
    expect(member.address).toBe('1 Main St');
  });
});

// ────────────────────────────────────────────────────────────
// PageResponse
// ────────────────────────────────────────────────────────────

describe('makePageResponse', () => {
  it('wraps items in a Page envelope', () => {
    const products = makeProductList(3);
    const page = makePageResponse(products);
    expect(page.content).toHaveLength(3);
    expect(page.totalElements).toBe(3);
    expect(page.totalPages).toBe(1);
    expect(page.number).toBe(0);
    expect(page.first).toBe(true);
    expect(page.last).toBe(true);
  });

  it('handles multi-page responses via overrides', () => {
    const products = makeProductList(12);
    const page = makePageResponse(products, {
      totalElements: 36,
      totalPages: 3,
      number: 1,
      first: false,
      last: false,
    });
    expect(page.totalPages).toBe(3);
    expect(page.number).toBe(1);
    expect(page.first).toBe(false);
    expect(page.last).toBe(false);
  });

  it('is generic — works with any type', () => {
    const members = [makeMember({ id: 1 }), makeMember({ id: 2 })];
    const page: PageResponse<Member> = makePageResponse(members);
    expect(page.content[0].id).toBe(1);
    expect(page.content[1].id).toBe(2);
  });
});

// ────────────────────────────────────────────────────────────
// makeProductList
// ────────────────────────────────────────────────────────────

describe('makeProductList', () => {
  it('creates N products with sequential IDs', () => {
    const list = makeProductList(5);
    expect(list).toHaveLength(5);
    list.forEach((p, i) => {
      expect(p.id).toBe(i + 1);
      expect(p.name).toBe(`Product ${i + 1}`);
    });
  });

  it('returns empty array for count 0', () => {
    expect(makeProductList(0)).toHaveLength(0);
  });
});

// ────────────────────────────────────────────────────────────
// AuthCredentials / Payloads
// ────────────────────────────────────────────────────────────

describe('makeAuthCredentials', () => {
  it('returns email and password strings', () => {
    const creds = makeAuthCredentials();
    expect(typeof creds.email).toBe('string');
    expect(typeof creds.password).toBe('string');
  });
});

describe('makeCreateOrderPayload', () => {
  it('contains a shippingAddress', () => {
    const payload = makeCreateOrderPayload();
    expect(payload.shippingAddress).toBeDefined();
    expect(typeof payload.shippingAddress.city).toBe('string');
  });
});

describe('makeRegisterPayload', () => {
  it('has required name, email, and password', () => {
    const payload = makeRegisterPayload();
    expect(typeof payload.name).toBe('string');
    expect(typeof payload.email).toBe('string');
    expect(typeof payload.password).toBe('string');
  });

  it('phone and address are optional', () => {
    const payload = makeRegisterPayload();
    expect(payload.phone).toBeUndefined();
    expect(payload.address).toBeUndefined();
  });
});
