/**
 * Booking Form Page Object
 *
 * Helper functions for interacting with the multi-step booking form
 * in E2E tests. The booking flow has 4 steps:
 * 1. Date Selection
 * 2. Authentication
 * 3. Guest Details / Review
 * 4. Payment
 */

import { type Page, type Locator, expect } from '@playwright/test'

/**
 * Booking step enum for clarity
 */
export enum BookingStep {
  DATES = 1,
  AUTH = 2,
  DETAILS = 3,
  PAYMENT = 4,
}

/**
 * Booking form page object for multi-step form interactions
 */
export class BookingFormPageObject {
  readonly page: Page
  readonly form: Locator
  readonly stepIndicator: Locator

  constructor(page: Page) {
    this.page = page
    this.form = page.locator('[data-testid="booking-form"], form')
    this.stepIndicator = page.locator('[class*="step-indicator"], [class*="stepper"]')
  }

  /**
   * Navigate to the booking page
   */
  async goto(): Promise<void> {
    await this.page.goto('/booking')
  }

  /**
   * Get the current step number (1-4)
   */
  async getCurrentStep(): Promise<number> {
    // Look for active step indicator
    const activeStep = this.page.locator('[class*="active"], [aria-current="step"]')
    if (await activeStep.count() > 0) {
      const text = await activeStep.first().textContent()
      const match = text?.match(/\d/)
      return match ? parseInt(match[0]) : 1
    }
    return 1
  }

  /**
   * Check if on a specific step
   */
  async isOnStep(step: BookingStep): Promise<boolean> {
    const currentStep = await this.getCurrentStep()
    return currentStep === step
  }

  /**
   * Click the "Continue" or "Next" button to proceed
   */
  async clickContinue(): Promise<void> {
    const continueButton = this.page.getByRole('button', { name: /continue|next|proceed/i })
    await continueButton.click()
  }

  /**
   * Click the "Back" button to go to previous step
   */
  async clickBack(): Promise<void> {
    const backButton = this.page.getByRole('button', { name: /back|previous/i })
    await backButton.click()
  }

  /**
   * Fill in guest details form
   */
  async fillGuestDetails(details: {
    name?: string
    email?: string
    phone?: string
  }): Promise<void> {
    if (details.name) {
      const nameInput = this.page.getByLabel(/name/i)
      await nameInput.fill(details.name)
    }
    if (details.email) {
      const emailInput = this.page.getByLabel(/email/i)
      await emailInput.fill(details.email)
    }
    if (details.phone) {
      const phoneInput = this.page.getByLabel(/phone/i)
      await phoneInput.fill(details.phone)
    }
  }

  /**
   * Click the "Verify Email" button on the auth step
   */
  async clickVerifyEmail(): Promise<void> {
    const verifyButton = this.page.getByRole('button', { name: /verify.*email|send.*code/i })
    await verifyButton.click()
  }

  /**
   * Wait for loading state to complete
   */
  async waitForLoading(): Promise<void> {
    // Wait for any loading spinners to disappear
    const loadingIndicator = this.page.locator('[class*="loading"], [class*="spinner"]')
    await expect(loadingIndicator).toBeHidden({ timeout: 30000 })
  }

  /**
   * Check if the continue button is enabled
   */
  async isContinueEnabled(): Promise<boolean> {
    const continueButton = this.page.getByRole('button', { name: /continue|next|proceed/i })
    return continueButton.isEnabled()
  }

  /**
   * Get validation error messages on the current step
   */
  async getValidationErrors(): Promise<string[]> {
    const errorMessages = this.page.locator('[role="alert"], [class*="error-message"], .text-destructive')
    return errorMessages.allTextContents()
  }

  /**
   * Get the booking summary (dates, price, etc.)
   */
  async getBookingSummary(): Promise<{
    checkIn?: string
    checkOut?: string
    nights?: string
    guests?: string
    total?: string
  }> {
    const summary: Record<string, string | undefined> = {}

    const checkInText = this.page.locator('text=/check.*in/i').first()
    if (await checkInText.isVisible()) {
      summary.checkIn = await checkInText.textContent() ?? undefined
    }

    const checkOutText = this.page.locator('text=/check.*out/i').first()
    if (await checkOutText.isVisible()) {
      summary.checkOut = await checkOutText.textContent() ?? undefined
    }

    const totalText = this.page.locator('text=/total|€|EUR/i').first()
    if (await totalText.isVisible()) {
      summary.total = await totalText.textContent() ?? undefined
    }

    return summary
  }

  /**
   * Navigate directly to a specific step (if allowed by the flow)
   */
  async goToStep(targetStep: BookingStep): Promise<void> {
    const currentStep = await this.getCurrentStep()

    if (targetStep > currentStep) {
      // Move forward
      for (let i = currentStep; i < targetStep; i++) {
        await this.clickContinue()
        await this.page.waitForTimeout(500)
      }
    } else if (targetStep < currentStep) {
      // Move backward
      for (let i = currentStep; i > targetStep; i--) {
        await this.clickBack()
        await this.page.waitForTimeout(500)
      }
    }
  }

  /**
   * Complete the date selection step with specific dates
   */
  async completeDateSelection(checkInDay: number, checkOutDay: number): Promise<void> {
    // Import calendar helper dynamically to avoid circular deps
    const { createCalendar } = await import('./calendar')
    const calendar = createCalendar(this.page)

    await calendar.waitForVisible()
    await calendar.selectDateRange(checkInDay, checkOutDay)
    await this.clickContinue()
  }

  /**
   * Complete the auth step with guest details
   */
  async completeAuthStep(details: {
    name: string
    email: string
    phone?: string
  }): Promise<void> {
    await this.fillGuestDetails(details)
    await this.clickVerifyEmail()
  }
}

/**
 * Factory function to create a BookingFormPageObject
 */
export function createBookingForm(page: Page): BookingFormPageObject {
  return new BookingFormPageObject(page)
}
