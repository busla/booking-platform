'use client'

/**
 * useAuthenticatedUser - Simplified EMAIL_OTP authentication hook.
 *
 * Flow:
 * 1. User enters email → initiateAuth()
 * 2. Try signIn (existing user) or signUp (new user)
 * 3. Cognito sends OTP email → state becomes 'awaiting_otp'
 * 4. User enters OTP → confirmOtp()
 * 5. Confirm via confirmSignIn or confirmSignUp → state becomes 'authenticated'
 *
 * Refactored for simplicity as part of 020-frontend-cleanup.
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import {
  signIn,
  signUp,
  confirmSignIn,
  confirmSignUp,
  autoSignIn,
  getCurrentUser,
  fetchAuthSession,
  signOut as amplifySignOut,
} from 'aws-amplify/auth'
import { authEvents } from '@/lib/api-client/auth-events'

// ============================================================================
// Types
// ============================================================================

export type AuthStep =
  | 'anonymous'     // Initial state, show form
  | 'sending_otp'   // OTP request in progress
  | 'awaiting_otp'  // OTP sent, waiting for user input
  | 'verifying'     // OTP verification in progress
  | 'authenticated' // Success

export type ErrorType = 'network' | 'auth' | 'validation' | 'rate_limit' | null

export interface AuthenticatedUser {
  email: string
  name?: string
  sub: string
}

export interface UseAuthenticatedUserReturn {
  step: AuthStep
  user: AuthenticatedUser | null
  error: string | null
  errorType: ErrorType
  /** True if user is signing up (6-digit code), false if signing in (8-digit code) */
  isNewUser: boolean
  initiateAuth: (email: string) => Promise<void>
  confirmOtp: (code: string) => Promise<void>
  signOut: () => Promise<void>
  retry: () => void
}

// ============================================================================
// Helpers
// ============================================================================

/** Extract user info from Amplify session */
async function fetchUserFromSession(): Promise<AuthenticatedUser> {
  const currentUser = await getCurrentUser()
  const session = await fetchAuthSession()
  const claims = session.tokens?.idToken?.payload
  return {
    email: claims?.email as string,
    name: claims?.name as string | undefined,
    sub: currentUser.userId,
  }
}

/** Categorize errors for appropriate UI feedback */
function categorizeError(err: unknown): { type: ErrorType; message: string } {
  if (!(err instanceof Error)) {
    return { type: 'auth', message: 'An unexpected error occurred' }
  }

  const name = err.name
  const msg = err.message.toLowerCase()

  // Network errors
  if (name === 'NetworkError' || msg.includes('network') || msg.includes('fetch')) {
    return { type: 'network', message: 'Unable to connect. Check your internet.' }
  }

  // Rate limiting
  if (name === 'LimitExceededException') {
    return { type: 'rate_limit', message: 'Too many attempts. Please wait.' }
  }

  // Invalid code
  if (name === 'CodeMismatchException') {
    return { type: 'auth', message: 'Invalid code. Please try again.' }
  }

  // Expired code
  if (name === 'ExpiredCodeException') {
    return { type: 'auth', message: 'Code expired. Please request a new one.' }
  }

  // Session expired
  if (name === 'NotAuthorizedException' || msg.includes('expired')) {
    return { type: 'auth', message: 'Session expired. Please sign in again.' }
  }

  return { type: 'auth', message: err.message }
}

/** Check if error indicates user doesn't exist */
function isUserNotFoundError(err: unknown): boolean {
  if (!(err instanceof Error)) return false
  return err.name === 'UserNotFoundException'
}

// ============================================================================
// Hook
// ============================================================================

export function useAuthenticatedUser(): UseAuthenticatedUserReturn {
  const [step, setStep] = useState<AuthStep>('anonymous')
  const [user, setUser] = useState<AuthenticatedUser | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [errorType, setErrorType] = useState<ErrorType>(null)
  const [isNewUser, setIsNewUser] = useState(false)

  // Track pending email for OTP confirmation
  const pendingEmail = useRef<string>('')

  // ──────────────────────────────────────────────────────────────────────────
  // Check existing session on mount
  // ──────────────────────────────────────────────────────────────────────────
  useEffect(() => {
    async function checkSession() {
      try {
        const userData = await fetchUserFromSession()
        setUser(userData)
        setStep('authenticated')
      } catch {
        setStep('anonymous')
      }
    }
    checkSession()
  }, [])

  // ──────────────────────────────────────────────────────────────────────────
  // Handle 401 from API (session expired)
  // ──────────────────────────────────────────────────────────────────────────
  useEffect(() => {
    const unsubscribe = authEvents.on('auth-required', async () => {
      try { await amplifySignOut() } catch { /* ignore */ }
      setUser(null)
      setStep('anonymous')
      setError('Session expired. Please sign in again.')
      setErrorType('auth')
    })
    return unsubscribe
  }, [])

  // ──────────────────────────────────────────────────────────────────────────
  // initiateAuth - Start EMAIL_OTP flow
  // ──────────────────────────────────────────────────────────────────────────
  const initiateAuth = useCallback(async (email: string) => {
    setError(null)
    setErrorType(null)
    setStep('sending_otp')
    pendingEmail.current = email
    setIsNewUser(false)

    try {
      // Try sign in for existing user
      const result = await signIn({
        username: email,
        options: { authFlowType: 'USER_AUTH', preferredChallenge: 'EMAIL_OTP' },
      })

      // Handle different response states
      if (result.nextStep.signInStep === 'CONFIRM_SIGN_IN_WITH_EMAIL_CODE') {
        // Normal flow - OTP sent
        setStep('awaiting_otp')
        return
      }

      if (result.nextStep.signInStep === 'CONTINUE_SIGN_IN_WITH_FIRST_FACTOR_SELECTION') {
        // Cognito asking for factor selection - check if EMAIL_OTP is available
        const challenges = (result.nextStep as { availableChallenges?: string[] }).availableChallenges || []
        const hasEmailOtp = challenges.some(c => c.toUpperCase() === 'EMAIL_OTP')

        if (!hasEmailOtp) {
          // No EMAIL_OTP = user doesn't exist (prevent_user_existence_errors enabled)
          throw Object.assign(new Error('User not found'), { name: 'UserNotFoundException' })
        }

        // Select EMAIL_OTP factor
        const selectResult = await confirmSignIn({ challengeResponse: 'EMAIL_OTP' })
        if (selectResult.nextStep.signInStep === 'CONFIRM_SIGN_IN_WITH_EMAIL_CODE') {
          setStep('awaiting_otp')
          return
        }
      }

      if (result.isSignedIn) {
        // Already authenticated
        const userData = await fetchUserFromSession()
        setUser(userData)
        setStep('authenticated')
        return
      }

      // Unexpected state
      throw new Error(`Unexpected auth state: ${result.nextStep.signInStep}`)

    } catch (err) {
      // Handle UserAlreadyAuthenticatedException
      if (err instanceof Error && err.name === 'UserAlreadyAuthenticatedException') {
        try {
          const userData = await fetchUserFromSession()
          setUser(userData)
          setStep('authenticated')
          return
        } catch { /* fall through to error */ }
      }

      // New user - try signUp
      if (isUserNotFoundError(err)) {
        await handleSignUp(email)
        return
      }

      // Auth error
      const { type, message } = categorizeError(err)
      setError(message)
      setErrorType(type)
      setStep('anonymous')
    }
  }, [])

  // ──────────────────────────────────────────────────────────────────────────
  // handleSignUp - Create new user with EMAIL_OTP
  // ──────────────────────────────────────────────────────────────────────────
  async function handleSignUp(email: string) {
    setIsNewUser(true)

    try {
      const result = await signUp({
        username: email,
        password: crypto.randomUUID(), // Required but unused for EMAIL_OTP
        options: {
          userAttributes: { email },
          autoSignIn: { authFlowType: 'USER_AUTH' },
        },
      })

      if (result.nextStep.signUpStep === 'CONFIRM_SIGN_UP') {
        // OTP sent for new user
        setStep('awaiting_otp')
        return
      }

      if (result.isSignUpComplete) {
        // Unexpected immediate completion - try autoSignIn
        const autoResult = await autoSignIn()
        if (autoResult.isSignedIn) {
          const userData = await fetchUserFromSession()
          setUser(userData)
          setStep('authenticated')
          return
        }
      }

      throw new Error(`Unexpected signup state: ${result.nextStep.signUpStep}`)

    } catch (err) {
      const { type, message } = categorizeError(err)
      setError(message)
      setErrorType(type)
      setStep('anonymous')
    }
  }

  // ──────────────────────────────────────────────────────────────────────────
  // confirmOtp - Verify OTP code
  // ──────────────────────────────────────────────────────────────────────────
  const confirmOtp = useCallback(async (code: string) => {
    setError(null)
    setErrorType(null)
    setStep('verifying')

    try {
      if (isNewUser) {
        // New user: confirmSignUp → autoSignIn (6-digit code)
        await confirmSignUp({
          username: pendingEmail.current,
          confirmationCode: code,
        })

        const autoResult = await autoSignIn()
        if (!autoResult.isSignedIn) {
          throw new Error('Auto sign-in failed after signup')
        }
      } else {
        // Existing user: confirmSignIn (8-digit code)
        const result = await confirmSignIn({ challengeResponse: code })
        if (!result.isSignedIn) {
          throw new Error('Sign-in verification failed')
        }
      }

      // Success - fetch user data
      const userData = await fetchUserFromSession()
      setUser(userData)
      setStep('authenticated')

    } catch (err) {
      const { type, message } = categorizeError(err)
      setError(message)
      setErrorType(type)
      setStep('awaiting_otp') // Stay on OTP screen for retry
    }
  }, [isNewUser])

  // ──────────────────────────────────────────────────────────────────────────
  // signOut - Clear session
  // ──────────────────────────────────────────────────────────────────────────
  const signOut = useCallback(async () => {
    await amplifySignOut()
    setUser(null)
    setStep('anonymous')
  }, [])

  // ──────────────────────────────────────────────────────────────────────────
  // retry - Reset to try again
  // ──────────────────────────────────────────────────────────────────────────
  const retry = useCallback(() => {
    setError(null)
    setErrorType(null)
    setIsNewUser(false)
    pendingEmail.current = ''
    setStep('anonymous')
  }, [])

  return { step, user, error, errorType, isNewUser, initiateAuth, confirmOtp, signOut, retry }
}
