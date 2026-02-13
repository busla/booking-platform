/**
 * Integration Tests: Complete Booking Flow with Real EMAIL_OTP Authentication
 *
 * These tests exercise the COMPLETE booking flow including real Cognito EMAIL_OTP
 * verification. Unlike the password-based auth fixture tests, these:
 *   1. Start unauthenticated (no auth fixture)
 *   2. Go through full EMAIL_OTP flow
 *   3. Use OTP Interceptor Lambda to retrieve actual codes from DynamoDB
 *
 * This ensures we catch issues like:
 *   - OTP input field count mismatches (6 vs 8 digits)
 *   - Email delivery failures
 *   - OTP verification errors
 *
 * Prerequisites:
 *   1. OTP Interceptor Lambda deployed (stores codes in DynamoDB for test emails)
 *   2. AWS credentials configured for DynamoDB access
 *   3. Cognito User Pool configured with EMAIL_OTP authentication
 *
 * Test email pattern: test+{timestamp}-{random}@summerhouse.com
 *
 * Run with:
 *   yarn test:e2e:live --grep "Booking Flow with OTP"
 *
 * @see tests/e2e/utils/otp-helper.ts
 * @see infrastructure/modules/otp-interceptor/
 */

import { test, expect, Page } from '@playwright/test'
import { addDays, format } from 'date-fns'
import { generateTestEmail, getOtpForEmail, clearOtpForEmail } from '../utils/otp-helper'

// ============================================================================
// Configuration
// ============================================================================

/** Longer timeout for real API, Cognito, and Stripe interactions */
test.setTimeout(180000)

// Test fixtures
// Note: Name must match schema regex /^[a-zA-ZÀ-ÿ\s'-]+$/ (no digits allowed)
const TEST_CUSTOMER = {
  name: 'Test User',
  phone: '+34 612 345 678',
}

// ============================================================================
// Helpers
// ============================================================================

/**
 * Select a date in the booking calendar.
 * Navigates to the correct month if needed and handles disabled dates.
 *
 * @param page - Playwright page
 * @param date - Date to select
 * @param options - Selection options
 * @returns The actual selected date (may differ from requested if fallback was used)
 */
async function selectDate(
  page: Page,
  date: Date,
  options: { allowFallback?: boolean; minDate?: Date } = {}
): Promise<Date> {
  const { allowFallback = true, minDate } = options
  const dateStr = date.toLocaleDateString()
  const readableDateStr = format(date, 'yyyy-MM-dd')

  let attempts = 0
  const maxAttempts = 24 // Up to 24 months ahead

  while (attempts < maxAttempts) {
    const dayButton = page.locator(`button[data-day="${dateStr}"]`)

    if (await dayButton.isVisible()) {
      const isDisabled = await dayButton.isDisabled()
      if (!isDisabled) {
        await dayButton.click()
        return date
      }

      if (allowFallback) {
        const enabledDays = page.locator('[data-slot="calendar"] button[data-day]:not([disabled])')
        const count = await enabledDays.count()

        for (let i = 0; i < count; i++) {
          const dayBtn = enabledDays.nth(i)
          const dayDateStr = await dayBtn.getAttribute('data-day')
          const dayDate = new Date(dayDateStr!)

          if (dayDate < date) continue
          if (minDate && dayDate <= minDate) continue

          await dayBtn.click()
          console.log(
            `[selectDate] Fallback: requested ${readableDateStr}, selected ${format(dayDate, 'yyyy-MM-dd')}`
          )
          return dayDate
        }
      }
    }

    const nextMonthButton = page.locator('button.rdp-button_next')
    if (await nextMonthButton.isVisible()) {
      await nextMonthButton.click()
      await page.waitForTimeout(200)
    }

    attempts++
  }

  throw new Error(
    `Could not find available date near ${readableDateStr} after ${maxAttempts} navigation attempts`
  )
}

/**
 * Complete the date selection step.
 *
 * @param page - Playwright page
 * @param startOffset - Days from today to start booking
 * @param nights - Number of nights to book
 * @returns Selected check-in and check-out dates
 */
async function completeDateSelectionStep(
  page: Page,
  startOffset: number = 90,
  nights: number = 5
): Promise<{ checkIn: Date; checkOut: Date }> {
  await page.goto('/book')
  await page.waitForLoadState('networkidle')

  await expect(page.locator('[data-slot="calendar"]').first()).toBeVisible({ timeout: 10000 })

  const requestedCheckIn = addDays(new Date(), startOffset)
  const checkIn = await selectDate(page, requestedCheckIn)
  const checkOut = addDays(checkIn, nights)
  const minCheckOutDate = addDays(checkIn, nights - 1)
  await selectDate(page, checkOut, { minDate: minCheckOutDate })

  await expect(page.getByText(/night/i)).toBeVisible({ timeout: 10000 })

  // Click Continue to proceed to auth step
  await page.getByRole('button', { name: /^continue$/i }).click()

  return { checkIn, checkOut }
}

/**
 * Fill and submit the auth step form, triggering OTP send.
 *
 * @param page - Playwright page
 * @param email - Test email address
 */
async function fillAuthStepForm(page: Page, email: string): Promise<void> {
  // Should be on auth step
  await expect(page.getByText(/verify identity/i)).toBeVisible({ timeout: 10000 })

  // Fill form fields
  await page.getByLabel(/full name/i).fill(TEST_CUSTOMER.name)
  await page.getByLabel(/email/i).fill(email)
  await page.getByLabel(/phone/i).fill(TEST_CUSTOMER.phone)

  // Click Verify Email to trigger OTP
  await page.getByRole('button', { name: /verify email/i }).click()

  // Wait for OTP view to appear (shows code input or "Sending...")
  // The sending state is transient, so wait for OTP input
  await expect(page.getByLabel(/verification code|code/i)).toBeVisible({ timeout: 30000 })
}

/**
 * Retrieve OTP from DynamoDB and enter it in the UI.
 *
 * @param page - Playwright page
 * @param email - Test email to retrieve OTP for
 */
async function enterOtpCode(page: Page, email: string): Promise<void> {
  console.log(`[OTP] Retrieving OTP for ${email}...`)

  // Get OTP from DynamoDB (polls with 500ms interval, uses default 15s timeout)
  const otpCode = await getOtpForEmail(email)
  console.log(`[OTP] Retrieved code: ${otpCode.substring(0, 2)}****** (${otpCode.length} digits)`)

  // Verify we have a 6-digit code (Cognito SignUp verification codes are 6 digits)
  // Note: SignIn EMAIL_OTP codes are 8 digits, but E2E tests always create new users (SignUp flow)
  expect(otpCode).toHaveLength(6)

  // The OTP input is an InputOTP component with a hidden input element
  // that overlays the visual slots and handles keyboard input
  const otpSlots = page.locator('[data-slot="otp-slot"]')
  await expect(otpSlots).toHaveCount(6)

  // The actual input element has id="otp-input" and intercepts pointer events
  // Focus and type into it directly instead of clicking the slot divs
  const otpInput = page.locator('#otp-input')
  await otpInput.focus()
  await page.keyboard.type(otpCode)

  // Auto-submit happens when all 6 digits are entered (see handleOtpChange in AuthStep.tsx)
  // SignUp codes are 6 digits, SignIn codes are 8 digits - E2E tests use new users (SignUp)
  // Wait for verification to complete (shows "Verifying..." then advances)

  // Wait for Guest Details step (successful verification)
  // Note: There's an empty alert container (toast) in the DOM that's always present,
  // so we can't use getByRole('alert') to detect errors reliably.
  // Instead, wait for success and check for error text if timeout.
  const guestDetails = page.getByText('Guest Details')

  try {
    await expect(guestDetails).toBeVisible({ timeout: 30000 })
    console.log('[OTP] Verification successful, on Guest Details step')
  } catch {
    // Check if there's an actual error message displayed
    // Look for error text within the auth step card, not global alert containers
    const errorInCard = page.locator('.bg-destructive\\/10, .bg-amber-100').first()
    if (await errorInCard.isVisible().catch(() => false)) {
      const errorText = await errorInCard.textContent()
      throw new Error(`OTP verification failed: ${errorText}`)
    }
    // Re-throw original timeout error if no specific error found
    throw new Error('OTP verification timed out - Guest Details step not reached')
  }
}

/**
 * Complete the guest details step.
 *
 * @param page - Playwright page
 */
async function completeGuestDetailsStep(page: Page): Promise<void> {
  await expect(page.getByText('Guest Details')).toBeVisible({ timeout: 5000 })

  // Guest details now only contains guest count and special requests
  // (name/email/phone collected in auth step)

  // Click Continue to Payment
  const continueButton = page.getByRole('button', { name: /continue to payment/i })
  await expect(continueButton).toBeEnabled({ timeout: 5000 })
  await continueButton.click()

  // Wait for payment step
  await expect(page.getByText('Complete Payment')).toBeVisible({ timeout: 30000 })
}

// ============================================================================
// Tests: Complete Booking Flow with Real EMAIL_OTP
// ============================================================================

// Wrap all OTP tests in a parent describe with serial mode to prevent
// concurrent Lambda invocations across describe blocks
test.describe('Booking Flow with OTP', () => {
  // Serial mode at the parent level ensures all child describe blocks run sequentially
  // This prevents Lambda concurrency issues and Cognito rate limiting
  test.describe.configure({ mode: 'serial' })

test.describe('Full Flow', () => {
  let testEmail: string

  test.beforeEach(async () => {
    // Generate unique test email for each test
    testEmail = generateTestEmail()
    console.log(`[Test] Using email: ${testEmail}`)

    // Small delay between tests to avoid Cognito rate limiting
    // Cognito may throttle rapid SignUp requests
    await new Promise((resolve) => setTimeout(resolve, 1000))
  })

  test.afterEach(async () => {
    // Clean up OTP from DynamoDB (optional, TTL auto-deletes)
    try {
      await clearOtpForEmail(testEmail)
    } catch {
      // Ignore cleanup errors
    }
  })

  test('unauthenticated user can complete booking with real EMAIL_OTP', async ({ page }) => {
    // Step 1: Date Selection
    console.log('[Test] Step 1: Date Selection')
    const { checkIn, checkOut } = await completeDateSelectionStep(page, 100, 5)
    console.log(`[Test] Selected dates: ${format(checkIn, 'yyyy-MM-dd')} to ${format(checkOut, 'yyyy-MM-dd')}`)

    // Step 2: Auth Step - Fill form and trigger OTP
    console.log('[Test] Step 2: Auth Step - Filling form')
    await fillAuthStepForm(page, testEmail)

    // Step 3: Enter OTP code from DynamoDB
    console.log('[Test] Step 3: Entering OTP code')
    await enterOtpCode(page, testEmail)

    // Step 4: Guest Details
    console.log('[Test] Step 4: Guest Details')
    await completeGuestDetailsStep(page)

    // Verify we're on payment step
    await expect(page.getByText('Complete Payment')).toBeVisible()
    await expect(page.getByText('Booking Summary')).toBeVisible()
    await expect(page.getByRole('button', { name: /proceed to payment/i })).toBeEnabled()
  })

  test('OTP input has exactly 6 slots for SignUp verification codes', async ({ page }) => {
    // Navigate to auth step
    await completeDateSelectionStep(page, 110, 5)

    // Fill form and trigger OTP
    await page.getByLabel(/full name/i).fill(TEST_CUSTOMER.name)
    await page.getByLabel(/email/i).fill(testEmail)
    await page.getByLabel(/phone/i).fill(TEST_CUSTOMER.phone)
    await page.getByRole('button', { name: /verify email/i }).click()

    // Wait for OTP input
    await expect(page.getByLabel(/verification code|code/i)).toBeVisible({ timeout: 30000 })

    // Verify exactly 6 OTP slots
    // Note: Cognito SignUp codes are 6 digits, SignIn EMAIL_OTP codes are 8 digits
    // E2E tests always create new users (unique test emails) so we always get SignUp flow
    const otpSlots = page.locator('[data-slot="otp-slot"]')
    await expect(otpSlots).toHaveCount(6)
  })

  test('complete flow proceeds to Stripe checkout', async ({ page }) => {
    // Complete full flow
    await completeDateSelectionStep(page, 120, 5)
    await fillAuthStepForm(page, testEmail)
    await enterOtpCode(page, testEmail)
    await completeGuestDetailsStep(page)

    // Click Proceed to Payment
    await page.getByRole('button', { name: /proceed to payment/i }).click()

    // Should show loading state
    await expect(page.getByText(/creating session|redirecting/i)).toBeVisible({ timeout: 5000 })

    // Wait for redirect to Stripe Checkout
    await page.waitForURL(/checkout\.stripe\.com/, { timeout: 30000 })

    // Verify we're on Stripe
    expect(page.url()).toContain('checkout.stripe.com')
  })
})

test.describe('Error Handling', () => {
  let testEmail: string

  test.beforeEach(async () => {
    testEmail = generateTestEmail()

    // Small delay between tests to avoid Cognito rate limiting
    await new Promise((resolve) => setTimeout(resolve, 1000))
  })

  test.afterEach(async () => {
    try {
      await clearOtpForEmail(testEmail)
    } catch {
      // Ignore cleanup errors
    }
  })

  test('shows validation errors for empty auth form', async ({ page }) => {
    await completeDateSelectionStep(page, 130, 5)

    // Click verify without filling form
    await page.getByRole('button', { name: /verify email/i }).click()

    // Should show validation errors
    await expect(page.getByText(/name must be at least 2 characters/i)).toBeVisible()
    await expect(page.getByText(/valid email/i)).toBeVisible()
    await expect(page.getByText(/phone number must be at least 7/i)).toBeVisible()
  })

  test('shows error for invalid OTP code', async ({ page }) => {
    await completeDateSelectionStep(page, 140, 5)
    await fillAuthStepForm(page, testEmail)

    // Enter wrong OTP code - use the actual input element
    // Note: Using 6 digits since E2E tests always create new users (SignUp flow)
    const otpInput = page.locator('#otp-input')
    await otpInput.focus()
    await page.keyboard.type('123456') // Wrong code (6 digits to trigger auto-submit)

    // Should show error - use text matcher instead of getByRole('alert')
    // because Next.js route announcer also has role="alert"
    await expect(page.getByText(/invalid|incorrect|mismatch|error occurred/i)).toBeVisible({
      timeout: 15000,
    })
  })

  test('resend code button works', async ({ page }) => {
    await completeDateSelectionStep(page, 150, 5)
    await fillAuthStepForm(page, testEmail)

    // Click resend code
    await page.getByRole('button', { name: /resend|send again/i }).click()

    // Should remain on OTP view and not error
    await expect(page.getByLabel(/verification code|code/i)).toBeVisible({ timeout: 10000 })
  })

  test('change email button returns to form', async ({ page }) => {
    await completeDateSelectionStep(page, 160, 5)
    await fillAuthStepForm(page, testEmail)

    // Click change email
    await page.getByRole('button', { name: /change email/i }).click()

    // Should return to form view
    await expect(page.getByLabel(/full name/i)).toBeVisible({ timeout: 5000 })
    await expect(page.getByLabel(/email/i)).toBeVisible()
  })
})

test.describe('Session Persistence', () => {
  let testEmail: string

  test.beforeEach(async () => {
    testEmail = generateTestEmail()

    // Longer delay for Session Persistence tests (run later in suite)
    // to give Cognito rate limits time to reset
    await new Promise((resolve) => setTimeout(resolve, 2000))
  })

  test.afterEach(async () => {
    try {
      await clearOtpForEmail(testEmail)
    } catch {
      // Ignore cleanup errors
    }
  })

  test('auth form data persists when navigating back and forth', async ({ page }) => {
    await completeDateSelectionStep(page, 170, 5)

    // Fill auth form
    await page.getByLabel(/full name/i).fill(TEST_CUSTOMER.name)
    await page.getByLabel(/email/i).fill(testEmail)
    await page.getByLabel(/phone/i).fill(TEST_CUSTOMER.phone)

    // Go back to dates
    await page.getByRole('button', { name: /back/i }).click()
    await expect(page.getByText(/select your dates/i)).toBeVisible()

    // Continue back to auth
    await page.getByRole('button', { name: /continue/i }).click()

    // Form data should be preserved
    await expect(page.getByLabel(/full name/i)).toHaveValue(TEST_CUSTOMER.name)
    await expect(page.getByLabel(/email/i)).toHaveValue(testEmail)
    await expect(page.getByLabel(/phone/i)).toHaveValue(TEST_CUSTOMER.phone)
  })

  test('completed auth persists on page reload', async ({ page }) => {
    // Complete the full auth flow
    await completeDateSelectionStep(page, 180, 5)
    await fillAuthStepForm(page, testEmail)
    await enterOtpCode(page, testEmail)
    await completeGuestDetailsStep(page)

    // Get guest name from summary for verification
    await expect(page.getByText(TEST_CUSTOMER.name)).toBeVisible()

    // Reload page
    await page.reload()
    await page.waitForLoadState('networkidle')

    // Should still be on payment step (session storage preserves state)
    await expect(page.getByText('Complete Payment')).toBeVisible({ timeout: 10000 })
    await expect(page.getByText(TEST_CUSTOMER.name)).toBeVisible()
  })
})

}) // End of parent 'Booking Flow with OTP' describe block
