export default function Loading() {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '200px',
        opacity: 1,
        animation: 'fadeIn 200ms ease-out',
      }}
      aria-label="로딩 중"
      role="status"
    >
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '0.75rem',
          transform: 'translateY(0)',
          animation: 'slideUp 200ms ease-out',
        }}
      >
        <div
          data-testid="loading-spinner"
          style={{
            width: '32px',
            height: '32px',
            border: '3px solid var(--border)',
            borderTopColor: 'var(--accent)',
            borderRadius: '50%',
            animation: 'spin 600ms linear infinite',
          }}
        />
        <p
          style={{
            fontSize: '0.875rem',
            color: 'var(--text-muted)',
            margin: 0,
          }}
        >
          로딩 중...
        </p>
      </div>
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to   { opacity: 1; }
        }
        @keyframes slideUp {
          from { transform: translateY(8px); opacity: 0; }
          to   { transform: translateY(0);  opacity: 1; }
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
