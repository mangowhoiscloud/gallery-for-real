import { Suspense } from 'react';
import type { Metadata } from 'next';
import CheckoutForm from './CheckoutForm';

export const metadata: Metadata = {
  title: 'Checkout',
  description: 'Complete your purchase',
};

export default function CheckoutPage() {
  return (
    <Suspense>
      <CheckoutForm />
    </Suspense>
  );
}
