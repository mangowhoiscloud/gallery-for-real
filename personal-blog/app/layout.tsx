import type { Metadata } from 'next'
import { JetBrains_Mono } from 'next/font/google'
import { THEME_SCRIPT } from '@/lib/theme-script'
import Navigation from '@/components/Navigation'
import './globals.css'

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  display: 'swap',
})

export const metadata: Metadata = {
  title: {
    default: '개발 블로그',
    template: '%s | 개발 블로그',
  },
  description: '개발 경험과 기술 인사이트를 공유하는 블로그입니다.',
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'),
  openGraph: {
    title: '개발 블로그',
    description: '개발 경험과 기술 인사이트를 공유하는 블로그입니다.',
    type: 'website',
    locale: 'ko_KR',
    siteName: '개발 블로그',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <head>
        <link
          rel="stylesheet"
          href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css"
          crossOrigin="anonymous"
        />
        <script dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }} />
      </head>
      <body className={jetbrainsMono.variable}>
        <Navigation />
        <main>{children}</main>
      </body>
    </html>
  )
}
