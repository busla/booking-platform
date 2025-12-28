import type { Metadata, Viewport } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Summerhouse - Vacation Rental in Quesada',
  description:
    'Book your stay at our beautiful apartment in Quesada, Alicante. Chat with our AI assistant to check availability, get pricing, and complete your booking.',
  keywords: [
    'vacation rental',
    'Quesada',
    'Alicante',
    'Costa Blanca',
    'Spain',
    'holiday apartment',
    'beach house',
  ],
  authors: [{ name: 'Summerhouse' }],
  openGraph: {
    title: 'Summerhouse - Vacation Rental in Quesada',
    description:
      'Book your stay at our beautiful apartment in Quesada, Alicante. Chat with our AI assistant.',
    type: 'website',
    locale: 'en_US',
    alternateLocale: 'es_ES',
  },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  themeColor: '#1d4ed8',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body>
        <div className="app-container">{children}</div>
      </body>
    </html>
  )
}
