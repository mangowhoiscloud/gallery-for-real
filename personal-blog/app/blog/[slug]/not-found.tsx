import Link from 'next/link';

export default function PostNotFound() {
  return (
    <main
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
        padding: '2rem 1rem',
        textAlign: 'center',
      }}
    >
      <p
        style={{
          fontSize: '5rem',
          fontWeight: 700,
          color: 'var(--accent)',
          lineHeight: 1,
          margin: 0,
        }}
      >
        404
      </p>
      <h1
        style={{
          fontSize: '1.5rem',
          fontWeight: 700,
          marginTop: '1rem',
          marginBottom: '0.5rem',
        }}
      >
        게시물을 찾을 수 없습니다
      </h1>
      <p
        style={{
          color: 'var(--text-muted)',
          marginBottom: '2rem',
          fontSize: '0.9375rem',
        }}
      >
        요청하신 게시물이 존재하지 않거나 삭제되었습니다.
      </p>
      <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', justifyContent: 'center' }}>
        <Link
          href="/blog"
          style={{
            color: 'var(--accent)',
            textDecoration: 'none',
            fontSize: '0.9375rem',
            padding: '0.5rem 1.25rem',
            border: '1px solid var(--accent)',
            borderRadius: '6px',
          }}
        >
          블로그 목록으로
        </Link>
        <Link
          href="/"
          style={{
            color: 'var(--text-muted)',
            textDecoration: 'none',
            fontSize: '0.9375rem',
            padding: '0.5rem 1.25rem',
            border: '1px solid var(--border)',
            borderRadius: '6px',
          }}
        >
          홈으로 돌아가기
        </Link>
      </div>
    </main>
  );
}
