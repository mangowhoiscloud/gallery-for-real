interface LoadingSkeletonProps {
  count?: number;
}

function SkeletonCard() {
  return (
    <div className="rounded-xl overflow-hidden border border-[var(--border)] animate-pulse">
      <div className="aspect-square bg-gray-200 dark:bg-gray-700" />
      <div className="p-4 space-y-3">
        <div className="h-4 w-16 bg-gray-200 dark:bg-gray-700 rounded-full" />
        <div className="h-4 w-full bg-gray-200 dark:bg-gray-700 rounded" />
        <div className="h-4 w-2/3 bg-gray-200 dark:bg-gray-700 rounded" />
        <div className="h-6 w-20 bg-gray-200 dark:bg-gray-700 rounded" />
      </div>
    </div>
  );
}

export default function LoadingSkeleton({ count = 8 }: LoadingSkeletonProps) {
  return (
    <div
      data-testid="loading-skeleton"
      className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6"
    >
      {Array.from({ length: count }, (_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}
