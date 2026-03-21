import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4 p-8 text-center">
      <p className="text-8xl font-bold text-gray-200 dark:text-gray-700 select-none">404</p>
      <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">Page not found</h2>
      <p className="text-gray-600 dark:text-gray-400 max-w-md">
        The page you&apos;re looking for doesn&apos;t exist or has been moved.
      </p>
      <Link
        href="/"
        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
      >
        Go Home
      </Link>
    </div>
  );
}
