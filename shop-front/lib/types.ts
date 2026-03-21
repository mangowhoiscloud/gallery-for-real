// ────────────────────────────────────────────────────────────
// Domain Entities
// ────────────────────────────────────────────────────────────

export interface Product {
  id: number;
  name: string;
  price: number;
  description: string;
  imageUrl: string;
  category: string;
  stockQuantity: number;
  createdAt: string; // ISO 8601 date string
}

export interface CartItem {
  id: number;
  product: Product;
  quantity: number;
}

export interface CartResponse {
  id: number;
  items: CartItem[];
  totalPrice: number;
}

export type OrderStatus =
  | 'PENDING'
  | 'CONFIRMED'
  | 'SHIPPED'
  | 'DELIVERED'
  | 'CANCELLED';

export interface ShippingAddress {
  name: string;
  addressLine1: string;
  addressLine2?: string;
  city: string;
  state: string;
  zipCode: string;
  country: string;
}

export interface OrderItem {
  id: number;
  productId: number;
  productName: string;
  quantity: number;
  price: number;
}

export interface Order {
  id: number;
  items: OrderItem[];
  totalAmount: number;
  status: OrderStatus;
  shippingAddress: ShippingAddress;
  createdAt: string; // ISO 8601 date string
}

export interface Member {
  id: number;
  email: string;
  name: string;
  phone?: string;
  address?: string;
}

// ────────────────────────────────────────────────────────────
// API Shapes
// ────────────────────────────────────────────────────────────

/** Spring Boot Page response envelope */
export interface PageResponse<T> {
  content: T[];
  totalElements: number;
  totalPages: number;
  size: number;
  number: number; // 0-indexed current page
  first: boolean;
  last: boolean;
}

export interface ApiError {
  status: number;
  message: string;
}

export interface AuthCredentials {
  email: string;
  password: string;
}

// ────────────────────────────────────────────────────────────
// Request Payloads
// ────────────────────────────────────────────────────────────

export interface CreateOrderPayload {
  shippingAddress: ShippingAddress;
}

export interface UpdateProfilePayload {
  name?: string;
  phone?: string;
  address?: string;
}

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
  phone?: string;
  address?: string;
}

export interface AddToCartPayload {
  productId: number;
  quantity: number;
}

export interface UpdateCartItemPayload {
  quantity: number;
}

// ────────────────────────────────────────────────────────────
// Search / Filter Params
// ────────────────────────────────────────────────────────────

export type SortField = 'name' | 'price' | 'createdAt';
export type SortDir = 'asc' | 'desc';

export interface ProductSearchParams {
  keyword?: string;
  category?: string;
  minPrice?: number;
  maxPrice?: number;
  sortBy?: SortField;
  sortDir?: SortDir;
  page?: number;
  size?: number;
}
