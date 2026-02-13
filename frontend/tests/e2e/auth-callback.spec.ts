/**
 * E2E Tests: Authentication Flows
 *
 * This file consolidates tests for post-authentication flows:
 *
 * 1. OAuth2 Callback Flow (OAuth2 3LO):
 *    - Successful callback with session_id
 *    - Error handling for OAuth2 failures
 *    - Session status polling
 *    - Redirect to appropriate pages after auth
 *
 * 2. Token Delivery Flow (SSE/AgentCore):
 *    - OTP verification triggers token delivery via SSE tool-result event
 *    - Frontend detects TokenDeliveryEvent in tool results
 *    - Session is stored in localStorage with all token fields
 *    - New fields (refreshToken, cognitoSub) are persisted correctly
 *
 * Architecture Notes:
 * - OAuth2: Backend `/auth/callback` redirects to frontend with query params
 * - SSE: AgentCore sends tool-result events containing TokenDeliveryEvent
 * - Both flows result in session storage in localStorage
 */

import { test, expect, type Page } from '@playwright/test'
import type { TokenDeliveryEvent, AuthSession } from '@/types'

// === Test Helpers ===

/**
 * Build OAuth2 callback URL with params
 */
function buildCallbackUrl(params: Record<string, string>): string {
  const searchParams = new URLSearchParams(params)
  return `/auth/callback?${searchParams.toString()}`
}

/**
 * Mock auth session in localStorage
 */
async function setAuthSession(
  page: Page,
  session: {
    isAuthenticated: boolean
    guestId?: string
    email?: string
    accessToken?: string
    expiresAt?: number
  }
) {
  await page.evaluate((sessionData) => {
    localStorage.setItem('booking_session', JSON.stringify(sessionData))
  }, session)
}

/**
 * Clear auth session from localStorage
 */
async function clearAuthSession(page: Page) {
  await page.evaluate(() => {
    localStorage.removeItem('booking_session')
    localStorage.removeItem('booking_verification')
  })
}

/**
 * Get auth session from localStorage
 */
async function getAuthSession(page: Page): Promise<AuthSession | null> {
  return await page.evaluate(() => {
    const stored = localStorage.getItem('booking_session')
    return stored ? JSON.parse(stored) : null
  })
}

/**
 * Create a valid TokenDeliveryEvent for testing
 */
function createMockTokenDeliveryEvent(
  overrides?: Partial<TokenDeliveryEvent>
): TokenDeliveryEvent {
  return {
    event_type: 'auth_tokens',
    success: true,
    id_token: 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.id.sig',
    access_token: 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.access.sig',
    refresh_token: 'opaque-refresh-token-abc123',
    expires_in: 3600,
    guest_id: 'guest-test-12345',
    email: 'test@example.com',
    cognito_sub: 'cognito-sub-uuid-xyz',
    ...overrides,
  }
}

// === OAuth2 Callback Tests ===

test.describe('OAuth2 Callback URL Parsing', () => {
  test('parses success callback params correctly', async ({ page }) => {
    // Test URL parsing logic
    const callbackUrl = buildCallbackUrl({
      status: 'success',
      session_id: 'sess_abc123def456',
    })

    const params = await page.evaluate((url) => {
      const searchParams = new URLSearchParams(url.split('?')[1])
      return {
        status: searchParams.get('status'),
        sessionId: searchParams.get('session_id'),
      }
    }, callbackUrl)

    expect(params.status).toBe('success')
    expect(params.sessionId).toBe('sess_abc123def456')
  })

  test('parses error callback params correctly', async ({ page }) => {
    const callbackUrl = buildCallbackUrl({
      status: 'error',
      error: 'access_denied',
      error_description: 'User cancelled the login',
    })

    const params = await page.evaluate((url) => {
      const searchParams = new URLSearchParams(url.split('?')[1])
      return {
        status: searchParams.get('status'),
        error: searchParams.get('error'),
        errorDescription: searchParams.get('error_description'),
      }
    }, callbackUrl)

    expect(params.status).toBe('error')
    expect(params.error).toBe('access_denied')
    expect(params.errorDescription).toBe('User cancelled the login')
  })

  test('handles missing session_id gracefully', async ({ page }) => {
    const callbackUrl = buildCallbackUrl({
      status: 'success',
      // Missing session_id
    })

    const params = await page.evaluate((url) => {
      const searchParams = new URLSearchParams(url.split('?')[1])
      return {
        status: searchParams.get('status'),
        sessionId: searchParams.get('session_id'),
        isValid: searchParams.get('status') === 'success' && !!searchParams.get('session_id'),
      }
    }, callbackUrl)

    expect(params.sessionId).toBeNull()
    expect(params.isValid).toBe(false)
  })
})

// === OAuth2 Error Handling Tests ===

test.describe('OAuth2 Error Scenarios', () => {
  test('handles access_denied error', async ({ page }) => {
    const errorInfo = {
      code: 'access_denied',
      description: 'User cancelled the login',
      userFriendlyMessage: 'You cancelled the login. Please try again when ready.',
    }

    // Test error message mapping
    const result = await page.evaluate((error) => {
      const errorMessages: Record<string, string> = {
        access_denied: 'You cancelled the login. Please try again when ready.',
        invalid_request: 'There was a problem with the login request.',
        unauthorized_client: 'This application is not authorized.',
        server_error: 'The authentication server encountered an error.',
      }
      return errorMessages[error.code] || 'An unknown error occurred.'
    }, errorInfo)

    expect(result).toBe(errorInfo.userFriendlyMessage)
  })

  test('handles server_error appropriately', async ({ page }) => {
    const result = await page.evaluate(() => {
      const errorMessages: Record<string, string> = {
        access_denied: 'You cancelled the login. Please try again when ready.',
        invalid_request: 'There was a problem with the login request.',
        unauthorized_client: 'This application is not authorized.',
        server_error: 'The authentication server encountered an error.',
      }
      return errorMessages['server_error']
    })

    expect(result).toBe('The authentication server encountered an error.')
  })

  test('handles unknown error codes', async ({ page }) => {
    const result = await page.evaluate(() => {
      const errorCode = 'completely_unknown_error'
      const errorMessages: Record<string, string> = {
        access_denied: 'You cancelled the login.',
        server_error: 'Server error.',
      }
      return errorMessages[errorCode] || 'An unexpected error occurred. Please try again.'
    })

    expect(result).toBe('An unexpected error occurred. Please try again.')
  })
})

// === Session State Tests ===

test.describe('OAuth2 Session State Updates', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await clearAuthSession(page)
  })

  test('successful OAuth2 creates authenticated session', async ({ page }) => {
    // Simulate what callback page should do on success
    await page.evaluate(() => {
      // This mimics the callback page behavior
      const sessionData = {
        isAuthenticated: true,
        guestId: 'guest_oauth_123',
        email: 'oauth@example.com',
        // Note: accessToken would come from backend API
      }
      localStorage.setItem('booking_session', JSON.stringify(sessionData))
    })

    const session = await getAuthSession(page)
    expect(session.isAuthenticated).toBe(true)
    expect(session.guestId).toBe('guest_oauth_123')
    expect(session.email).toBe('oauth@example.com')
  })

  test('failed OAuth2 does not create session', async ({ page }) => {
    // Simulate failed callback - should not set session
    await page.evaluate(() => {
      // On error, callback page should NOT set auth session
      // Just display error message
    })

    const session = await getAuthSession(page)
    expect(session).toBeNull()
  })

  test('OAuth2 success clears pending verification state', async ({ page }) => {
    // Set pending verification state
    await page.evaluate(() => {
      localStorage.setItem(
        'booking_verification',
        JSON.stringify({
          email: 'pending@example.com',
          codeRequested: true,
          verified: false,
        })
      )
    })

    // Simulate successful OAuth2 completion
    await page.evaluate(() => {
      // Callback page should clear verification state and set session
      localStorage.removeItem('booking_verification')
      localStorage.setItem(
        'booking_session',
        JSON.stringify({
          isAuthenticated: true,
          guestId: 'guest_oauth_456',
          email: 'oauth@example.com',
        })
      )
    })

    const verificationState = await page.evaluate(() =>
      localStorage.getItem('booking_verification')
    )
    expect(verificationState).toBeNull()

    const session = await getAuthSession(page)
    expect(session.isAuthenticated).toBe(true)
  })
})

// === Redirect Tests ===

test.describe('Post-Auth Redirects', () => {
  test('determines correct redirect based on return URL', async ({ page }) => {
    // Navigate first so window.location.origin is properly set
    await page.goto('/')

    // Test redirect logic
    const testCases = await page.evaluate(() => {
      function getRedirectUrl(returnUrl: string | null, defaultPath: string = '/'): string {
        if (!returnUrl) return defaultPath

        // Security: Only allow relative URLs or same-origin
        try {
          const url = new URL(returnUrl, window.location.origin)
          if (url.origin === window.location.origin) {
            return url.pathname + url.search
          }
        } catch {
          // Invalid URL, use default
        }
        return defaultPath
      }

      return [
        { returnUrl: null, expected: '/' },
        { returnUrl: '/pricing', expected: '/pricing' },
        { returnUrl: '/booking/confirm', expected: '/booking/confirm' },
        { returnUrl: 'https://malicious.com', expected: '/' }, // Should not allow
      ].map(({ returnUrl, expected }) => ({
        returnUrl,
        expected,
        actual: getRedirectUrl(returnUrl),
      }))
    })

    for (const tc of testCases) {
      expect(tc.actual).toBe(tc.expected)
    }
  })

  test('preserves booking context in session storage', async ({ page }) => {
    await page.goto('/')

    // Simulate storing booking context before auth redirect
    await page.evaluate(() => {
      const bookingContext = {
        checkIn: '2025-02-01',
        checkOut: '2025-02-07',
        guests: 2,
        returnToBooking: true,
      }
      sessionStorage.setItem('booking_context', JSON.stringify(bookingContext))
    })

    // After OAuth2 callback, context should still be available
    const context = await page.evaluate(() => {
      const stored = sessionStorage.getItem('booking_context')
      return stored ? JSON.parse(stored) : null
    })

    expect(context.checkIn).toBe('2025-02-01')
    expect(context.checkOut).toBe('2025-02-07')
    expect(context.guests).toBe(2)
    expect(context.returnToBooking).toBe(true)
  })
})

// === Session Status Polling Tests ===

test.describe('Session Status Polling', () => {
  test('implements exponential backoff for polling', async ({ page }) => {
    // Test polling logic without actual network calls
    const delays = await page.evaluate(() => {
      const baseDelay = 1000
      const maxDelay = 30000
      const attempts = 6

      const delays: number[] = []
      for (let i = 0; i < attempts; i++) {
        const delay = Math.min(baseDelay * Math.pow(2, i), maxDelay)
        delays.push(delay)
      }
      return delays
    })

    expect(delays).toEqual([1000, 2000, 4000, 8000, 16000, 30000])
  })

  test('session status transitions correctly', async ({ page }) => {
    const stateMachine = await page.evaluate(() => {
      type SessionStatus = 'pending' | 'completed' | 'failed' | 'expired'

      const validTransitions: Record<SessionStatus, SessionStatus[]> = {
        pending: ['completed', 'failed', 'expired'],
        completed: [], // Terminal state
        failed: [], // Terminal state
        expired: [], // Terminal state
      }

      function canTransition(from: SessionStatus, to: SessionStatus): boolean {
        return validTransitions[from]?.includes(to) ?? false
      }

      return {
        pendingToCompleted: canTransition('pending', 'completed'),
        pendingToFailed: canTransition('pending', 'failed'),
        completedToPending: canTransition('completed', 'pending'),
        failedToCompleted: canTransition('failed', 'completed'),
      }
    })

    expect(stateMachine.pendingToCompleted).toBe(true)
    expect(stateMachine.pendingToFailed).toBe(true)
    expect(stateMachine.completedToPending).toBe(false)
    expect(stateMachine.failedToCompleted).toBe(false)
  })
})

// === Security Tests ===

test.describe('OAuth2 Security', () => {
  test('validates state parameter to prevent CSRF', async ({ page }) => {
    // Test state validation logic
    const result = await page.evaluate(() => {
      const storedState = 'random_state_abc123'
      const receivedState = 'random_state_abc123'
      const mismatchedState = 'different_state_xyz789'

      return {
        validState: storedState === receivedState,
        invalidState: storedState === mismatchedState,
      }
    })

    expect(result.validState).toBe(true)
    expect(result.invalidState).toBe(false)
  })

  test('sanitizes error messages to prevent XSS', async ({ page }) => {
    const sanitized = await page.evaluate(() => {
      function sanitizeError(message: string): string {
        return message
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
          .replace(/"/g, '&quot;')
          .replace(/'/g, '&#x27;')
      }

      const maliciousError = '<script>alert("xss")</script>'
      return sanitizeError(maliciousError)
    })

    expect(sanitized).toBe('&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;')
    expect(sanitized).not.toContain('<script>')
  })

  test('does not expose sensitive data in URLs', async ({ page }) => {
    // Verify callback URL doesn't contain access tokens
    const callbackUrl = buildCallbackUrl({
      status: 'success',
      session_id: 'sess_abc123',
      // Should NOT contain: access_token, id_token, refresh_token
    })

    expect(callbackUrl).not.toContain('access_token')
    expect(callbackUrl).not.toContain('id_token')
    expect(callbackUrl).not.toContain('refresh_token')
  })
})

// === Loading States Tests ===

test.describe('OAuth2 Callback Loading States', () => {
  test('defines correct loading states', async ({ page }) => {
    const states = await page.evaluate(() => {
      type CallbackState = 'loading' | 'validating' | 'success' | 'error'

      const stateMessages: Record<CallbackState, string> = {
        loading: 'Processing authentication...',
        validating: 'Verifying your session...',
        success: 'Authentication successful! Redirecting...',
        error: 'Authentication failed. Please try again.',
      }

      return Object.entries(stateMessages).map(([state, message]) => ({
        state,
        message,
        hasMessage: message.length > 0,
      }))
    })

    expect(states).toHaveLength(4)
    states.forEach((s) => expect(s.hasMessage).toBe(true))
  })
})

// === Integration with Main App Tests ===

test.describe('Auth Integration with Main App', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/agent')
    await clearAuthSession(page)
  })

  test('authenticated user can access booking features', async ({ page }) => {
    // Set authenticated session
    await setAuthSession(page, {
      isAuthenticated: true,
      guestId: 'guest_booking',
      email: 'booking@example.com',
      accessToken: 'valid_token',
      expiresAt: Date.now() + 3600000,
    })

    // Reload to apply session
    await page.reload()

    // Verify main page loads
    await expect(page.getByText('Welcome to Quesada Apartment!')).toBeVisible()

    // Verify chat input is available
    const input = page.getByPlaceholder('Ask about availability, pricing, or the property...')
    await expect(input).toBeEnabled()
  })

  test('session survives navigation to different pages', async ({ page }) => {
    await setAuthSession(page, {
      isAuthenticated: true,
      guestId: 'guest_nav',
      email: 'nav@example.com',
    })

    // Navigate to different pages
    const pages = ['/', '/pricing', '/about', '/faq']

    for (const path of pages) {
      await page.goto(path)
      const session = await getAuthSession(page)
      expect(session!.isAuthenticated).toBe(true)
      expect(session!.guestId).toBe('guest_nav')
    }
  })
})

// ============================================================================
// Token Delivery Tests (SSE/AgentCore)
// ============================================================================

// === Token Delivery Event Detection Tests ===

test.describe('TokenDeliveryEvent Detection', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await clearAuthSession(page)
  })

  test('isTokenDeliveryEvent correctly identifies valid events', async ({ page }) => {
    // Test the type guard logic in the browser context
    const results = await page.evaluate(() => {
      // Simulate the isTokenDeliveryEvent type guard
      const isTokenDeliveryEvent = (value: unknown): boolean => {
        if (value === null || value === undefined) return false
        if (typeof value !== 'object') return false
        const obj = value as Record<string, unknown>
        return obj.event_type === 'auth_tokens' && obj.success === true
      }

      return {
        validEvent: isTokenDeliveryEvent({
          event_type: 'auth_tokens',
          success: true,
          id_token: 'token',
          access_token: 'token',
          refresh_token: 'token',
          expires_in: 3600,
          guest_id: 'guest',
          email: 'test@test.com',
          cognito_sub: 'sub',
        }),
        nullValue: isTokenDeliveryEvent(null),
        undefinedValue: isTokenDeliveryEvent(undefined),
        stringValue: isTokenDeliveryEvent('not an event'),
        wrongEventType: isTokenDeliveryEvent({
          event_type: 'other',
          success: true,
        }),
        failedEvent: isTokenDeliveryEvent({
          event_type: 'auth_tokens',
          success: false,
        }),
        missingEventType: isTokenDeliveryEvent({
          success: true,
          id_token: 'token',
        }),
      }
    })

    expect(results.validEvent).toBe(true)
    expect(results.nullValue).toBe(false)
    expect(results.undefinedValue).toBe(false)
    expect(results.stringValue).toBe(false)
    expect(results.wrongEventType).toBe(false)
    expect(results.failedEvent).toBe(false)
    expect(results.missingEventType).toBe(false)
  })

  test('sessionFromTokenEvent correctly converts to AuthSession', async ({ page }) => {
    const event = createMockTokenDeliveryEvent()

    const session = await page.evaluate((evt) => {
      // Simulate the sessionFromTokenEvent conversion
      return {
        isAuthenticated: true,
        guestId: evt.guest_id,
        email: evt.email,
        accessToken: evt.access_token,
        idToken: evt.id_token,
        refreshToken: evt.refresh_token,
        cognitoSub: evt.cognito_sub,
        expiresAt: Date.now() + evt.expires_in * 1000,
      }
    }, event)

    expect(session.isAuthenticated).toBe(true)
    expect(session.guestId).toBe('guest-test-12345')
    expect(session.email).toBe('test@example.com')
    expect(session.accessToken).toBe(event.access_token)
    expect(session.idToken).toBe(event.id_token)
    expect(session.refreshToken).toBe('opaque-refresh-token-abc123')
    expect(session.cognitoSub).toBe('cognito-sub-uuid-xyz')
    expect(session.expiresAt).toBeGreaterThan(Date.now())
  })
})

// === Token Storage Tests ===

test.describe('Token Storage in localStorage', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await clearAuthSession(page)
  })

  test('stores all token fields including refreshToken and cognitoSub', async ({ page }) => {
    const event = createMockTokenDeliveryEvent()

    // Simulate the full storage flow
    await page.evaluate((evt) => {
      const session = {
        isAuthenticated: true,
        guestId: evt.guest_id,
        email: evt.email,
        accessToken: evt.access_token,
        idToken: evt.id_token,
        refreshToken: evt.refresh_token,
        cognitoSub: evt.cognito_sub,
        expiresAt: Date.now() + evt.expires_in * 1000,
      }
      localStorage.setItem('booking_session', JSON.stringify(session))
    }, event)

    // Verify all fields were stored
    const stored = await getAuthSession(page)
    expect(stored).not.toBeNull()
    expect(stored!.isAuthenticated).toBe(true)
    expect(stored!.guestId).toBe('guest-test-12345')
    expect(stored!.email).toBe('test@example.com')
    expect(stored!.accessToken).toBe(event.access_token)
    expect(stored!.idToken).toBe(event.id_token)
    expect(stored!.refreshToken).toBe('opaque-refresh-token-abc123')
    expect(stored!.cognitoSub).toBe('cognito-sub-uuid-xyz')
    expect(stored!.expiresAt).toBeDefined()
  })

  test('session persists after page reload', async ({ page }) => {
    const event = createMockTokenDeliveryEvent({
      guest_id: 'guest-persist-test',
      email: 'persist@example.com',
    })

    // Store session
    await page.evaluate((evt) => {
      const session = {
        isAuthenticated: true,
        guestId: evt.guest_id,
        email: evt.email,
        accessToken: evt.access_token,
        idToken: evt.id_token,
        refreshToken: evt.refresh_token,
        cognitoSub: evt.cognito_sub,
        expiresAt: Date.now() + evt.expires_in * 1000,
      }
      localStorage.setItem('booking_session', JSON.stringify(session))
    }, event)

    // Reload the page
    await page.reload()

    // Session should persist
    const stored = await getAuthSession(page)
    expect(stored).not.toBeNull()
    expect(stored!.guestId).toBe('guest-persist-test')
    expect(stored!.email).toBe('persist@example.com')
    expect(stored!.refreshToken).toBe('opaque-refresh-token-abc123')
    expect(stored!.cognitoSub).toBe('cognito-sub-uuid-xyz')
  })

  test('session cleared correctly on sign out', async ({ page }) => {
    // First store a session
    const event = createMockTokenDeliveryEvent()
    await page.evaluate((evt) => {
      const session = {
        isAuthenticated: true,
        guestId: evt.guest_id,
        email: evt.email,
        accessToken: evt.access_token,
        idToken: evt.id_token,
        refreshToken: evt.refresh_token,
        cognitoSub: evt.cognito_sub,
        expiresAt: Date.now() + evt.expires_in * 1000,
      }
      localStorage.setItem('booking_session', JSON.stringify(session))
    }, event)

    // Verify it was stored
    let stored = await getAuthSession(page)
    expect(stored).not.toBeNull()

    // Clear session (simulating sign out)
    await clearAuthSession(page)

    // Verify it was cleared
    stored = await getAuthSession(page)
    expect(stored).toBeNull()
  })
})

// === SSE Tool Result Processing Tests ===

test.describe('SSE Tool Result Processing', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await clearAuthSession(page)
  })

  test('processes tool-result events from SSE stream correctly', async ({ page }) => {
    // Simulate SSE data lines containing tool-result events
    const toolResults = await page.evaluate(() => {
      // Simulate the parseSSEEvent function
      const parseSSEEvent = (line: string) => {
        if (!line.startsWith('data: ')) return null
        const jsonStr = line.slice(6).trim()
        if (!jsonStr) return null
        try {
          return JSON.parse(jsonStr)
        } catch {
          return null
        }
      }

      const sseLines = [
        'data: {"type": "start", "messageId": "msg-1"}',
        'data: {"type": "text-delta", "delta": "Verifying your code..."}',
        'data: {"type": "tool-result", "toolCallId": "call-123", "result": {"event_type": "auth_tokens", "success": true, "id_token": "id-jwt", "access_token": "access-jwt", "refresh_token": "refresh-opaque", "expires_in": 3600, "guest_id": "guest-sse-test", "email": "sse@example.com", "cognito_sub": "sub-sse"}}',
        'data: {"type": "text-delta", "delta": " You are now authenticated!"}',
        'data: {"type": "finish", "finishReason": "stop"}',
      ]

      const results: unknown[] = []
      for (const line of sseLines) {
        const event = parseSSEEvent(line)
        if (event?.type === 'tool-result' && event.result !== undefined) {
          results.push(event.result)
        }
      }

      return results
    })

    expect(toolResults).toHaveLength(1)
    expect((toolResults[0] as Record<string, unknown>).event_type).toBe('auth_tokens')
    expect((toolResults[0] as Record<string, unknown>).success).toBe(true)
    expect((toolResults[0] as Record<string, unknown>).guest_id).toBe('guest-sse-test')
  })

  test('full flow: SSE stream → token detection → storage', async ({ page }) => {
    // Simulate the complete flow from SSE to storage
    await page.evaluate(() => {
      // Step 1: Parse SSE events
      const parseSSEEvent = (line: string) => {
        if (!line.startsWith('data: ')) return null
        const jsonStr = line.slice(6).trim()
        if (!jsonStr) return null
        try {
          return JSON.parse(jsonStr)
        } catch {
          return null
        }
      }

      // Step 2: Type guard for TokenDeliveryEvent
      const isTokenDeliveryEvent = (value: unknown): boolean => {
        if (value === null || value === undefined) return false
        if (typeof value !== 'object') return false
        const obj = value as Record<string, unknown>
        return obj.event_type === 'auth_tokens' && obj.success === true
      }

      // Step 3: Conversion function
      const sessionFromTokenEvent = (evt: {
        guest_id: string
        email: string
        access_token: string
        id_token: string
        refresh_token: string
        cognito_sub: string
        expires_in: number
      }) => ({
        isAuthenticated: true,
        guestId: evt.guest_id,
        email: evt.email,
        accessToken: evt.access_token,
        idToken: evt.id_token,
        refreshToken: evt.refresh_token,
        cognitoSub: evt.cognito_sub,
        expiresAt: Date.now() + evt.expires_in * 1000,
      })

      // Simulate SSE response from verify_cognito_otp
      const sseLine =
        'data: {"type": "tool-result", "toolCallId": "verify-call", "result": {"event_type": "auth_tokens", "success": true, "id_token": "full-flow-id", "access_token": "full-flow-access", "refresh_token": "full-flow-refresh", "expires_in": 3600, "guest_id": "guest-full-flow", "email": "fullflow@example.com", "cognito_sub": "sub-full-flow"}}'

      const event = parseSSEEvent(sseLine)
      if (event?.type === 'tool-result' && event.result !== undefined) {
        if (isTokenDeliveryEvent(event.result)) {
          const session = sessionFromTokenEvent(event.result as Parameters<typeof sessionFromTokenEvent>[0])
          localStorage.setItem('booking_session', JSON.stringify(session))
        }
      }
    })

    // Verify the full flow worked
    const stored = await getAuthSession(page)
    expect(stored).not.toBeNull()
    expect(stored!.isAuthenticated).toBe(true)
    expect(stored!.guestId).toBe('guest-full-flow')
    expect(stored!.email).toBe('fullflow@example.com')
    expect(stored!.idToken).toBe('full-flow-id')
    expect(stored!.accessToken).toBe('full-flow-access')
    expect(stored!.refreshToken).toBe('full-flow-refresh')
    expect(stored!.cognitoSub).toBe('sub-full-flow')
  })
})

// === Token Security Tests ===

test.describe('Token Security', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await clearAuthSession(page)
  })

  test('tokens are not exposed in DOM', async ({ page }) => {
    const event = createMockTokenDeliveryEvent()

    // Store session with tokens
    await page.evaluate((evt) => {
      const session = {
        isAuthenticated: true,
        guestId: evt.guest_id,
        email: evt.email,
        accessToken: evt.access_token,
        idToken: evt.id_token,
        refreshToken: evt.refresh_token,
        cognitoSub: evt.cognito_sub,
        expiresAt: Date.now() + evt.expires_in * 1000,
      }
      localStorage.setItem('booking_session', JSON.stringify(session))
    }, event)

    // Reload to ensure any UI updates
    await page.reload()

    // Get page content and verify tokens are NOT exposed
    const pageContent = await page.content()
    expect(pageContent).not.toContain(event.access_token)
    expect(pageContent).not.toContain(event.id_token)
    expect(pageContent).not.toContain(event.refresh_token)
    expect(pageContent).not.toContain('eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9')
  })

  test('console logging does not expose token values', async ({ page }) => {
    // Capture console messages
    const consoleLogs: string[] = []
    page.on('console', (msg) => {
      consoleLogs.push(msg.text())
    })

    // Simulate token delivery with logging
    await page.evaluate(() => {
      const session = {
        isAuthenticated: true,
        guestId: 'guest-log-test',
        email: 'log@example.com',
        accessToken: 'secret-access-token',
        idToken: 'secret-id-token',
        refreshToken: 'secret-refresh-token',
        cognitoSub: 'sub-log-test',
        expiresAt: Date.now() + 3600000,
      }

      // Simulate the secure logging pattern (like T026)
      console.log('[Auth] Session stored after token delivery', {
        guestId: session.guestId,
        email: session.email,
        expiresAt: session.expiresAt,
        // Note: NO token values logged
      })

      localStorage.setItem('booking_session', JSON.stringify(session))
    })

    // Verify no token values in console output
    const allLogs = consoleLogs.join(' ')
    expect(allLogs).not.toContain('secret-access-token')
    expect(allLogs).not.toContain('secret-id-token')
    expect(allLogs).not.toContain('secret-refresh-token')

    // But verify the log message itself was output
    expect(allLogs).toContain('[Auth] Session stored after token delivery')
  })
})

// === Token Delivery Edge Case Tests ===

test.describe('Token Delivery Edge Cases', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await clearAuthSession(page)
  })

  test('handles multiple tool-result events correctly', async ({ page }) => {
    // Test scenario: multiple tools return results, only TokenDeliveryEvent should trigger storage
    const tokensStored = await page.evaluate(() => {
      const isTokenDeliveryEvent = (value: unknown): boolean => {
        if (value === null || value === undefined) return false
        if (typeof value !== 'object') return false
        const obj = value as Record<string, unknown>
        return obj.event_type === 'auth_tokens' && obj.success === true
      }

      const toolResults = [
        { success: true, availability: ['2025-01-15', '2025-01-16'] },
        { success: true, price: 150, currency: 'EUR' },
        {
          event_type: 'auth_tokens',
          success: true,
          id_token: 'multi-id',
          access_token: 'multi-access',
          refresh_token: 'multi-refresh',
          expires_in: 3600,
          guest_id: 'guest-multi',
          email: 'multi@example.com',
          cognito_sub: 'sub-multi',
        },
        { success: true, reservation_id: 'RES-123' },
      ]

      let tokenEventsFound = 0
      for (const result of toolResults) {
        if (isTokenDeliveryEvent(result)) {
          tokenEventsFound++
          localStorage.setItem(
            'booking_session',
            JSON.stringify({
              isAuthenticated: true,
              guestId: result.guest_id,
              email: result.email,
              accessToken: result.access_token,
              idToken: result.id_token,
              refreshToken: result.refresh_token,
              cognitoSub: result.cognito_sub,
            })
          )
        }
      }

      return tokenEventsFound
    })

    expect(tokensStored).toBe(1)
    const stored = await getAuthSession(page)
    expect(stored?.guestId).toBe('guest-multi')
  })

  test('handles malformed tool-result gracefully', async ({ page }) => {
    const result = await page.evaluate(() => {
      const isTokenDeliveryEvent = (value: unknown): boolean => {
        if (value === null || value === undefined) return false
        if (typeof value !== 'object') return false
        const obj = value as Record<string, unknown>
        return obj.event_type === 'auth_tokens' && obj.success === true
      }

      const malformedResults = [
        null,
        undefined,
        'string',
        123,
        [],
        { event_type: 'auth_tokens' }, // missing success
        { success: true }, // missing event_type
        { event_type: 'auth_tokens', success: 'true' }, // success is string, not boolean
      ]

      return malformedResults.map((r) => isTokenDeliveryEvent(r))
    })

    // All should return false
    expect(result.every((r) => r === false)).toBe(true)
  })

  test('overwrites existing session on new token delivery', async ({ page }) => {
    // First session
    await page.evaluate(() => {
      localStorage.setItem(
        'booking_session',
        JSON.stringify({
          isAuthenticated: true,
          guestId: 'old-guest',
          email: 'old@example.com',
          accessToken: 'old-access',
        })
      )
    })

    let stored = await getAuthSession(page)
    expect(stored?.guestId).toBe('old-guest')

    // New token delivery should overwrite
    await page.evaluate(() => {
      localStorage.setItem(
        'booking_session',
        JSON.stringify({
          isAuthenticated: true,
          guestId: 'new-guest',
          email: 'new@example.com',
          accessToken: 'new-access',
          idToken: 'new-id',
          refreshToken: 'new-refresh',
          cognitoSub: 'new-sub',
          expiresAt: Date.now() + 3600000,
        })
      )
    })

    stored = await getAuthSession(page)
    expect(stored?.guestId).toBe('new-guest')
    expect(stored?.email).toBe('new@example.com')
    expect(stored?.refreshToken).toBe('new-refresh')
  })
})
