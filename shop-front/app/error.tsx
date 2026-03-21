'use client';

import { useEffect } from 'react';

interface Props {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function Error({ error, reset }: Props) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4 p-8 text-center">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
        Something went wrong
      </h2>
      <p className="text-gray-600 dark:text-gray-400 max-w-md">
        {error.message || 'An unexpected error occurred.'}
      </p>
      <button
        type="button"
        onClick={reset}
        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
      >
        Try Again
      </button>
    </div>
  );
}
