import { Suspense } from 'react';
import ProfilePage from './ProfilePage';
import LoadingSkeleton from '@/components/ui/LoadingSkeleton';

export const metadata = { title: 'My Profile' };

export default function Profile() {
  return (
    <Suspense
      fallback={
        <div className="container mx-auto px-4 py-8 max-w-2xl">
          <LoadingSkeleton count={3} />
        </div>
      }
    >
      <ProfilePage />
    </Suspense>
  );
}
