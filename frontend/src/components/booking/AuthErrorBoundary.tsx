'use client'

/**
 * AuthErrorBoundary - Error boundary for authentication-related components (T034).
 *
 * Catches JavaScript errors in child components and displays a fallback UI
 * with retry functionality. This prevents auth errors from crashing the
 * entire application.
 *
 * Uses shadcn Alert component with destructive variant for consistent styling.
 */

import { Component, ReactNode } from 'react'
import { AlertCircle } from 'lucide-react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'

interface AuthErrorBoundaryProps {
  children: ReactNode
  onRetry?: () => void
}

interface AuthErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

/**
 * Error Boundary component for catching and handling auth-related crashes.
 *
 * Usage:
 * ```tsx
 * <AuthErrorBoundary onRetry={() => window.location.reload()}>
 *   <CustomerDetailsForm />
 * </AuthErrorBoundary>
 * ```
 */
export class AuthErrorBoundary extends Component<
  AuthErrorBoundaryProps,
  AuthErrorBoundaryState
> {
  constructor(props: AuthErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): AuthErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    // Log error for debugging (could send to error tracking service)
    console.error('AuthErrorBoundary caught error:', error, errorInfo)
  }

  handleRetry = (): void => {
    this.setState({ hasError: false, error: null })
    this.props.onRetry?.()
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <Alert variant="destructive" className="p-6">
          <AlertCircle className="h-5 w-5" />
          <AlertTitle className="text-lg font-semibold">
            Something went wrong
          </AlertTitle>
          <AlertDescription className="mt-2">
            <p className="mb-4">
              We encountered an unexpected error. Please try again.
            </p>
            <Button
              type="button"
              variant="destructive"
              onClick={this.handleRetry}
            >
              Try again
            </Button>
          </AlertDescription>
        </Alert>
      )
    }

    return this.props.children
  }
}
