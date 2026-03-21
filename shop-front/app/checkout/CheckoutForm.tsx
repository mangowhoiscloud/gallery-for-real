'use client';

import { useState, useEffect, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { getCart, getProfile, createOrder, clearCart } from '@/lib/api';
import { isAuthenticated } from '@/lib/auth';
import { useToast } from '@/components/ToastProvider';
import type { CartItem, CartResponse, Member, ShippingAddress } from '@/lib/types';

const SHIPPING_THRESHOLD = 50;
const SHIPPING_COST = 5;

function formatPrice(amount: number): string {
  return `$${amount.toFixed(2)}`;
}

function calcSubtotal(items: CartItem[]): number {
  return items.reduce((sum, item) => sum + item.product.price * item.quantity, 0);
}

interface FormErrors {
  name?: string;
  addressLine1?: string;
  city?: string;
  state?: string;
  zipCode?: string;
  country?: string;
}

function validate(fields: ShippingAddress): FormErrors {
  const errors: FormErrors = {};
  if (!fields.name.trim()) errors.name = 'Name is required';
  if (!fields.addressLine1.trim()) errors.addressLine1 = 'Address is required';
  if (!fields.city.trim()) errors.city = 'City is required';
  if (!fields.state.trim()) errors.state = 'State is required';
  if (!fields.zipCode.trim()) errors.zipCode = 'ZIP code is required';
  if (!fields.country.trim()) errors.country = 'Country is required';
  return errors;
}

export default function CheckoutForm() {
  const router = useRouter();
  const { toast } = useToast();

  const [cartItems, setCartItems] = useState<CartItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Shipping address state
  const [name, setName] = useState('');
  const [addressLine1, setAddressLine1] = useState('');
  const [addressLine2, setAddressLine2] = useState('');
  const [city, setCity] = useState('');
  const [state, setState] = useState('');
  const [zipCode, setZipCode] = useState('');
  const [country, setCountry] = useState('US');

  const [errors, setErrors] = useState<FormErrors>({});

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace('/login?redirect=/checkout');
      return;
    }

    Promise.all([getCart(), getProfile()])
      .then(([cart, profile]: [CartResponse, Member]) => {
        if (cart.items.length === 0) {
          router.replace('/cart');
          return;
        }
        setCartItems(cart.items);
        if (profile.name) setName(profile.name);
        if (profile.address) setAddressLine1(profile.address);
      })
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, [router]);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();

    const shippingAddress: ShippingAddress = {
      name,
      addressLine1,
      addressLine2: addressLine2 || undefined,
      city,
      state,
      zipCode,
      country,
    };

    const validationErrors = validate(shippingAddress);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) return;

    setIsSubmitting(true);
    try {
      const order = await createOrder({ shippingAddress });
      await clearCart();
      router.push(`/orders/${order.id}`);
    } catch {
      toast({
        variant: 'error',
        title: 'Order failed',
        description: 'An error occurred. Please try again.',
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="animate-pulse space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 bg-gray-200 dark:bg-gray-700 rounded" />
          ))}
        </div>
      </div>
    );
  }

  const subtotal = calcSubtotal(cartItems);
  const shipping = subtotal > SHIPPING_THRESHOLD ? 0 : SHIPPING_COST;
  const total = subtotal + shipping;

  const inputClass =
    'w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-accent';

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Checkout</h1>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Shipping address form */}
        <div className="flex-1">
          <h2 className="text-xl font-semibold mb-4">Shipping Address</h2>
          <form onSubmit={handleSubmit} noValidate className="space-y-4">
            {/* Full Name */}
            <div>
              <label htmlFor="checkout-name" className="block text-sm font-medium mb-1">
                Full Name
              </label>
              <input
                id="checkout-name"
                type="text"
                autoComplete="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className={inputClass}
                aria-invalid={errors.name ? 'true' : 'false'}
                aria-describedby={errors.name ? 'checkout-name-error' : undefined}
              />
              {errors.name && (
                <p id="checkout-name-error" role="alert" className="text-red-600 text-xs mt-1">
                  {errors.name}
                </p>
              )}
            </div>

            {/* Address Line 1 */}
            <div>
              <label htmlFor="checkout-address1" className="block text-sm font-medium mb-1">
                Address Line 1
              </label>
              <input
                id="checkout-address1"
                type="text"
                autoComplete="address-line1"
                value={addressLine1}
                onChange={(e) => setAddressLine1(e.target.value)}
                className={inputClass}
                aria-invalid={errors.addressLine1 ? 'true' : 'false'}
                aria-describedby={errors.addressLine1 ? 'checkout-address1-error' : undefined}
              />
              {errors.addressLine1 && (
                <p id="checkout-address1-error" role="alert" className="text-red-600 text-xs mt-1">
                  {errors.addressLine1}
                </p>
              )}
            </div>

            {/* Address Line 2 (optional) */}
            <div>
              <label htmlFor="checkout-address2" className="block text-sm font-medium mb-1">
                Address Line 2{' '}
                <span className="text-gray-500">(optional)</span>
              </label>
              <input
                id="checkout-address2"
                type="text"
                autoComplete="address-line2"
                value={addressLine2}
                onChange={(e) => setAddressLine2(e.target.value)}
                className={inputClass}
              />
            </div>

            {/* City */}
            <div>
              <label htmlFor="checkout-city" className="block text-sm font-medium mb-1">
                City
              </label>
              <input
                id="checkout-city"
                type="text"
                autoComplete="address-level2"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                className={inputClass}
                aria-invalid={errors.city ? 'true' : 'false'}
                aria-describedby={errors.city ? 'checkout-city-error' : undefined}
              />
              {errors.city && (
                <p id="checkout-city-error" role="alert" className="text-red-600 text-xs mt-1">
                  {errors.city}
                </p>
              )}
            </div>

            {/* State / ZIP side-by-side */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="checkout-state" className="block text-sm font-medium mb-1">
                  State
                </label>
                <input
                  id="checkout-state"
                  type="text"
                  autoComplete="address-level1"
                  value={state}
                  onChange={(e) => setState(e.target.value)}
                  className={inputClass}
                  aria-invalid={errors.state ? 'true' : 'false'}
                  aria-describedby={errors.state ? 'checkout-state-error' : undefined}
                />
                {errors.state && (
                  <p id="checkout-state-error" role="alert" className="text-red-600 text-xs mt-1">
                    {errors.state}
                  </p>
                )}
              </div>
              <div>
                <label htmlFor="checkout-zip" className="block text-sm font-medium mb-1">
                  ZIP Code
                </label>
                <input
                  id="checkout-zip"
                  type="text"
                  autoComplete="postal-code"
                  value={zipCode}
                  onChange={(e) => setZipCode(e.target.value)}
                  className={inputClass}
                  aria-invalid={errors.zipCode ? 'true' : 'false'}
                  aria-describedby={errors.zipCode ? 'checkout-zip-error' : undefined}
                />
                {errors.zipCode && (
                  <p id="checkout-zip-error" role="alert" className="text-red-600 text-xs mt-1">
                    {errors.zipCode}
                  </p>
                )}
              </div>
            </div>

            {/* Country */}
            <div>
              <label htmlFor="checkout-country" className="block text-sm font-medium mb-1">
                Country
              </label>
              <input
                id="checkout-country"
                type="text"
                autoComplete="country-name"
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                className={inputClass}
                aria-invalid={errors.country ? 'true' : 'false'}
                aria-describedby={errors.country ? 'checkout-country-error' : undefined}
              />
              {errors.country && (
                <p id="checkout-country-error" role="alert" className="text-red-600 text-xs mt-1">
                  {errors.country}
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-60 transition-colors"
            >
              {isSubmitting ? 'Placing Order\u2026' : 'Place Order'}
            </button>
          </form>
        </div>

        {/* Order summary */}
        <div className="lg:w-80">
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-6 space-y-3">
            <h2 className="text-xl font-bold">Order Summary</h2>

            {/* Cart items list */}
            <ul className="space-y-2">
              {cartItems.map((item) => (
                <li key={item.id} className="flex justify-between text-sm">
                  <span className="text-gray-700 dark:text-gray-300 truncate mr-2">
                    {item.product.name} × {item.quantity}
                  </span>
                  <span className="flex-shrink-0 font-medium">
                    {formatPrice(item.product.price * item.quantity)}
                  </span>
                </li>
              ))}
            </ul>

            <div className="border-t border-gray-200 dark:border-gray-700 pt-3 space-y-2">
              <div className="flex justify-between text-gray-600 dark:text-gray-400">
                <span>Subtotal</span>
                <span>{formatPrice(subtotal)}</span>
              </div>

              <div className="flex justify-between text-gray-600 dark:text-gray-400">
                <span>Estimated Shipping</span>
                <span>{shipping === 0 ? 'Free' : formatPrice(shipping)}</span>
              </div>

              {shipping === 0 && (
                <p className="text-xs text-green-600">You qualify for free shipping!</p>
              )}

              <div className="border-t border-gray-200 dark:border-gray-700 pt-3 flex justify-between font-bold text-lg">
                <span>Total</span>
                <span>{formatPrice(total)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
