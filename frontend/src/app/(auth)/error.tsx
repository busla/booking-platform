/**
 * Auth Error Boundary
 *
 * Handles unexpected errors in auth pages.
 * Uses shadcn Alert with destructive variant for error display.
 */

'use client'

import * as React from 'react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { AlertCircle } from 'lucide-react'

interface AuthErrorProps {
  error: Error & { digest?: string }
  reset: () => void
}

export default function AuthError({ error, reset }: AuthErrorProps) {
  React.useEffect(() => {
    // Log error to monitoring service in production
    console.error('[Auth Error]', error)
  }, [error])

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Authentication Error</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Something went wrong</AlertTitle>
          <AlertDescription>
            {error.message || 'An unexpected error occurred during authentication.'}
          </AlertDescription>
        </Alert>
        <div className="flex gap-2">
          <Button onClick={reset} variant="default">
            Try again
          </Button>
          <Button onClick={() => window.location.href = '/'} variant="outline">
            Go home
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
