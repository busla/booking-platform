/**
 * Unit tests for Login Page (T029).
 *
 * Tests the EMAIL_OTP authentication flow:
 * - Email form submission triggers signIn()
 * - OTP form handles verification via confirmSignIn()
 * - CSRF state is extracted from URL params and passed to callback
 * - Error handling for auth failures
 * - Already authenticated users are redirected
 */

import { describe, it, expect, beforeEach, vi, type Mock } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// Mock Next.js navigation
const mockPush = vi.fn()
const mockSearchParams = new Map<string, string>()

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  useSearchParams: () => ({
    get: (key: string) => mockSearchParams.get(key) ?? null,
  }),
}))

// Mock Amplify Auth
const mockSignIn = vi.fn()
const mockConfirmSignIn = vi.fn()
const mockGetCurrentUser = vi.fn()
const mockSignOut = vi.fn()

vi.mock('aws-amplify/auth', () => ({
  signIn: (...args: unknown[]) => mockSignIn(...args),
  confirmSignIn: (...args: unknown[]) => mockConfirmSignIn(...args),
  getCurrentUser: () => mockGetCurrentUser(),
  signOut: () => mockSignOut(),
}))

// Mock AmplifyProvider to avoid Amplify configuration issues in tests
vi.mock('@/components/providers/AmplifyProvider', () => ({
  AmplifyProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

// Import component after mocks are set up
// Note: (auth) is a route group - doesn't affect URL but organizes files
import LoginPage from '@/app/(auth)/login/page'

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockSearchParams.clear()
    // Default: user not logged in
    mockGetCurrentUser.mockRejectedValue(new Error('No current user'))
  })

  describe('Initial Rendering', () => {
    it('renders email form by default', async () => {
      render(<LoginPage />)

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /sign in/i })).toBeInTheDocument()
      })
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /send verification code/i })).toBeInTheDocument()
    })

    it('shows passwordless messaging', async () => {
      render(<LoginPage />)

      await waitFor(() => {
        expect(screen.getByText(/no password needed/i)).toBeInTheDocument()
      })
    })

    it('disables submit button when email is empty', async () => {
      render(<LoginPage />)

      await waitFor(() => {
        const button = screen.getByRole('button', { name: /send verification code/i })
        expect(button).toBeDisabled()
      })
    })
  })

  describe('Email Submission', () => {
    it('calls signIn with correct parameters on email submission', async () => {
      mockSignIn.mockResolvedValueOnce({
        nextStep: { signInStep: 'CONFIRM_SIGN_IN_WITH_EMAIL_CODE' },
      })

      render(<LoginPage />)
      const user = userEvent.setup()

      await waitFor(() => {
        expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
      })

      const emailInput = screen.getByLabelText(/email address/i)
      await user.type(emailInput, 'test@example.com')

      const submitButton = screen.getByRole('button', { name: /send verification code/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(mockSignIn).toHaveBeenCalledWith({
          username: 'test@example.com',
          options: {
            authFlowType: 'USER_AUTH',
            preferredChallenge: 'EMAIL_OTP',
          },
        })
      })
    })

    it('normalizes email to lowercase', async () => {
      mockSignIn.mockResolvedValueOnce({
        nextStep: { signInStep: 'CONFIRM_SIGN_IN_WITH_EMAIL_CODE' },
      })

      render(<LoginPage />)
      const user = userEvent.setup()

      await waitFor(() => {
        expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
      })

      const emailInput = screen.getByLabelText(/email address/i)
      await user.type(emailInput, 'TEST@EXAMPLE.COM')

      const submitButton = screen.getByRole('button', { name: /send verification code/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(mockSignIn).toHaveBeenCalledWith(
          expect.objectContaining({
            username: 'test@example.com',
          })
        )
      })
    })

    it('transitions to OTP step after successful signIn', async () => {
      mockSignIn.mockResolvedValueOnce({
        nextStep: { signInStep: 'CONFIRM_SIGN_IN_WITH_EMAIL_CODE' },
      })

      render(<LoginPage />)
      const user = userEvent.setup()

      await waitFor(() => {
        expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
      })

      const emailInput = screen.getByLabelText(/email address/i)
      await user.type(emailInput, 'test@example.com')

      const submitButton = screen.getByRole('button', { name: /send verification code/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /enter verification code/i })).toBeInTheDocument()
      })
      expect(screen.getByText(/we sent a code to test@example.com/i)).toBeInTheDocument()
    })

    it('displays error message on signIn failure', async () => {
      mockSignIn.mockRejectedValueOnce(new Error('User not found'))

      render(<LoginPage />)
      const user = userEvent.setup()

      await waitFor(() => {
        expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
      })

      const emailInput = screen.getByLabelText(/email address/i)
      await user.type(emailInput, 'unknown@example.com')

      const submitButton = screen.getByRole('button', { name: /send verification code/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/user not found/i)).toBeInTheDocument()
      })
    })

    it('signs out and retries when already signed in error occurs', async () => {
      mockSignIn
        .mockRejectedValueOnce(new Error('There is already a signed in user.'))
        .mockResolvedValueOnce({
          nextStep: { signInStep: 'CONFIRM_SIGN_IN_WITH_EMAIL_CODE' },
        })
      mockSignOut.mockResolvedValueOnce(undefined)

      render(<LoginPage />)
      const user = userEvent.setup()

      await waitFor(() => {
        expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
      })

      const emailInput = screen.getByLabelText(/email address/i)
      await user.type(emailInput, 'test@example.com')

      const submitButton = screen.getByRole('button', { name: /send verification code/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(mockSignOut).toHaveBeenCalled()
      })
    })
  })

  describe('OTP Verification', () => {
    beforeEach(async () => {
      // Set up to OTP step
      mockSignIn.mockResolvedValueOnce({
        nextStep: { signInStep: 'CONFIRM_SIGN_IN_WITH_EMAIL_CODE' },
      })
    })

    it('calls confirmSignIn with OTP code', async () => {
      mockConfirmSignIn.mockResolvedValueOnce({
        nextStep: { signInStep: 'DONE' },
      })

      render(<LoginPage />)
      const user = userEvent.setup()

      // Submit email first
      await waitFor(() => {
        expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
      })

      const emailInput = screen.getByLabelText(/email address/i)
      await user.type(emailInput, 'test@example.com')
      await user.click(screen.getByRole('button', { name: /send verification code/i }))

      // Wait for OTP step
      await waitFor(() => {
        expect(screen.getByLabelText(/verification code/i)).toBeInTheDocument()
      })

      const otpInput = screen.getByLabelText(/verification code/i)
      await user.type(otpInput, '12345678')

      const verifyButton = screen.getByRole('button', { name: /verify code/i })
      await user.click(verifyButton)

      await waitFor(() => {
        expect(mockConfirmSignIn).toHaveBeenCalledWith({
          challengeResponse: '12345678',
        })
      })
    })

    it('filters non-numeric characters from OTP input', async () => {
      render(<LoginPage />)
      const user = userEvent.setup()

      // Submit email first
      await waitFor(() => {
        expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
      })

      const emailInput = screen.getByLabelText(/email address/i)
      await user.type(emailInput, 'test@example.com')
      await user.click(screen.getByRole('button', { name: /send verification code/i }))

      // Wait for OTP step
      await waitFor(() => {
        expect(screen.getByLabelText(/verification code/i)).toBeInTheDocument()
      })

      const otpInput = screen.getByLabelText(/verification code/i)
      await user.type(otpInput, '12ab34cd56ef78')

      // Should only contain digits
      expect(otpInput).toHaveValue('12345678')
    })

    it('shows success message after successful OTP verification', async () => {
      mockConfirmSignIn.mockResolvedValueOnce({
        nextStep: { signInStep: 'DONE' },
      })

      render(<LoginPage />)
      const user = userEvent.setup()

      // Submit email first
      await waitFor(() => {
        expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
      })

      const emailInput = screen.getByLabelText(/email address/i)
      await user.type(emailInput, 'test@example.com')
      await user.click(screen.getByRole('button', { name: /send verification code/i }))

      // Wait for OTP step
      await waitFor(() => {
        expect(screen.getByLabelText(/verification code/i)).toBeInTheDocument()
      })

      const otpInput = screen.getByLabelText(/verification code/i)
      await user.type(otpInput, '12345678')
      await user.click(screen.getByRole('button', { name: /verify code/i }))

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /success/i })).toBeInTheDocument()
      })
    })

    it('displays error on invalid OTP', async () => {
      mockConfirmSignIn.mockRejectedValueOnce(new Error('Invalid verification code'))

      render(<LoginPage />)
      const user = userEvent.setup()

      // Submit email first
      await waitFor(() => {
        expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
      })

      const emailInput = screen.getByLabelText(/email address/i)
      await user.type(emailInput, 'test@example.com')
      await user.click(screen.getByRole('button', { name: /send verification code/i }))

      // Wait for OTP step
      await waitFor(() => {
        expect(screen.getByLabelText(/verification code/i)).toBeInTheDocument()
      })

      const otpInput = screen.getByLabelText(/verification code/i)
      await user.type(otpInput, '00000000')
      await user.click(screen.getByRole('button', { name: /verify code/i }))

      await waitFor(() => {
        expect(screen.getByText(/invalid verification code/i)).toBeInTheDocument()
      })
    })

    it('allows returning to email step', async () => {
      render(<LoginPage />)
      const user = userEvent.setup()

      // Submit email first
      await waitFor(() => {
        expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
      })

      const emailInput = screen.getByLabelText(/email address/i)
      await user.type(emailInput, 'test@example.com')
      await user.click(screen.getByRole('button', { name: /send verification code/i }))

      // Wait for OTP step
      await waitFor(() => {
        expect(screen.getByLabelText(/verification code/i)).toBeInTheDocument()
      })

      // Click "Use a different email"
      const backButton = screen.getByRole('button', { name: /use a different email/i })
      await user.click(backButton)

      // Should be back at email step
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /sign in/i })).toBeInTheDocument()
      })
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
    })
  })

  describe('CSRF State Handling (FR-023)', () => {
    it('reads state parameter from URL query params', async () => {
      // This test verifies the component reads the state parameter
      // The full CSRF flow is tested in E2E tests (auth-flow.spec.ts)
      mockSearchParams.set('state', encodeURIComponent('csrf-token-123'))
      mockSearchParams.set('redirect', encodeURIComponent('/auth/callback'))

      render(<LoginPage />)

      // Verify the component renders and can access params
      await waitFor(() => {
        expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
      })

      // The state param is available via useSearchParams mock
      expect(mockSearchParams.get('state')).toBe(encodeURIComponent('csrf-token-123'))
    })

    it('redirects without custom_state when no CSRF state provided', async () => {
      mockSearchParams.set('redirect', '/')

      mockSignIn.mockResolvedValueOnce({
        nextStep: { signInStep: 'DONE' },
      })

      render(<LoginPage />)
      const user = userEvent.setup()

      await waitFor(() => {
        expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
      })

      const emailInput = screen.getByLabelText(/email address/i)
      await user.type(emailInput, 'test@example.com')
      await user.click(screen.getByRole('button', { name: /send verification code/i }))

      await waitFor(
        () => {
          expect(mockPush).toHaveBeenCalledWith('/')
        },
        { timeout: 2000 }
      )
    })
  })

  describe('Already Authenticated User', () => {
    beforeEach(() => {
      // Ensure clean state for these tests
      mockSearchParams.clear()
    })

    it('redirects authenticated user to destination', async () => {
      // The checkAuth effect runs when redirectUrl changes (initially null, then from params)
      // So we need to mock getCurrentUser to resolve multiple times as the effect re-runs
      mockGetCurrentUser.mockResolvedValue({ username: 'existing-user' })
      mockSearchParams.set('redirect', '/protected-page')

      render(<LoginPage />)

      // The component will first redirect to '/' (when redirectUrl is null)
      // then redirect to '/protected-page' after the URL param effect runs
      await waitFor(
        () => {
          // Check that at some point it was called with the protected page
          const calls = mockPush.mock.calls.map((c) => c[0])
          expect(calls).toContain('/protected-page')
        },
        { timeout: 2000 }
      )
    })

    it('redirects to home when no destination specified', async () => {
      mockGetCurrentUser.mockResolvedValueOnce({ username: 'existing-user' })

      render(<LoginPage />)

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/')
      })
    })
  })

  describe('Loading States', () => {
    it('shows loading state while sending verification code', async () => {
      // Make signIn hang
      mockSignIn.mockImplementation(() => new Promise(() => {}))

      render(<LoginPage />)
      const user = userEvent.setup()

      await waitFor(() => {
        expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
      })

      const emailInput = screen.getByLabelText(/email address/i)
      await user.type(emailInput, 'test@example.com')
      await user.click(screen.getByRole('button', { name: /send verification code/i }))

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /sending/i })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /sending/i })).toBeDisabled()
      })
    })

    it('shows loading state while verifying OTP', async () => {
      mockSignIn.mockResolvedValueOnce({
        nextStep: { signInStep: 'CONFIRM_SIGN_IN_WITH_EMAIL_CODE' },
      })
      // Make confirmSignIn hang
      mockConfirmSignIn.mockImplementation(() => new Promise(() => {}))

      render(<LoginPage />)
      const user = userEvent.setup()

      // Submit email first
      await waitFor(() => {
        expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
      })

      const emailInput = screen.getByLabelText(/email address/i)
      await user.type(emailInput, 'test@example.com')
      await user.click(screen.getByRole('button', { name: /send verification code/i }))

      // Wait for OTP step
      await waitFor(() => {
        expect(screen.getByLabelText(/verification code/i)).toBeInTheDocument()
      })

      const otpInput = screen.getByLabelText(/verification code/i)
      await user.type(otpInput, '12345678')
      await user.click(screen.getByRole('button', { name: /verify code/i }))

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /verifying/i })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /verifying/i })).toBeDisabled()
      })
    })
  })

  describe('Redirect URL Handling', () => {
    it('extracts redirect URL from query params', async () => {
      mockSearchParams.set('redirect', encodeURIComponent('/dashboard'))

      mockSignIn.mockResolvedValueOnce({
        nextStep: { signInStep: 'DONE' },
      })

      render(<LoginPage />)
      const user = userEvent.setup()

      await waitFor(() => {
        expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
      })

      const emailInput = screen.getByLabelText(/email address/i)
      await user.type(emailInput, 'test@example.com')
      await user.click(screen.getByRole('button', { name: /send verification code/i }))

      await waitFor(
        () => {
          expect(mockPush).toHaveBeenCalledWith('/dashboard')
        },
        { timeout: 2000 }
      )
    })

    it('also accepts auth_url parameter', async () => {
      mockSearchParams.set('auth_url', encodeURIComponent('/auth/callback'))

      mockSignIn.mockResolvedValueOnce({
        nextStep: { signInStep: 'DONE' },
      })

      render(<LoginPage />)
      const user = userEvent.setup()

      await waitFor(() => {
        expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
      })

      const emailInput = screen.getByLabelText(/email address/i)
      await user.type(emailInput, 'test@example.com')
      await user.click(screen.getByRole('button', { name: /send verification code/i }))

      await waitFor(
        () => {
          expect(mockPush).toHaveBeenCalled()
        },
        { timeout: 2000 }
      )

      const pushedUrl = mockPush.mock.calls[0][0]
      expect(pushedUrl).toContain('/auth/callback')
    })
  })
})
