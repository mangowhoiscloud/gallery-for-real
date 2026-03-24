import Link from 'next/link';

export default function NotFound() {
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
        페이지를 찾을 수 없습니다
      </h1>
      <p
        style={{
          color: 'var(--text-muted)',
          marginBottom: '2rem',
          fontSize: '0.9375rem',
        }}
      >
        요청하신 페이지가 존재하지 않거나 이동되었습니다.
      </p>
      <Link
        href="/"
        style={{
          color: 'var(--accent)',
          textDecoration: 'none',
          fontSize: '0.9375rem',
          padding: '0.5rem 1.25rem',
          border: '1px solid var(--accent)',
          borderRadius: '6px',
        }}
      >
        홈으로 돌아가기
      </Link>
    </main>
  );
}
