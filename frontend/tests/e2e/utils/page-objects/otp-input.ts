/**
 * OTP Input Page Object
 *
 * Helper functions for interacting with the 8-digit OTP/verification
 * code input component in E2E tests.
 */

import { type Page, type Locator, expect } from '@playwright/test'

/**
 * OTP input page object for verification code interactions
 */
export class OTPInputPageObject {
  readonly page: Page
  readonly container: Locator

  constructor(page: Page) {
    this.page = page
    // The OTP input container with multiple digit inputs
    this.container = page.getByLabel(/verification code|code/i)
  }

  /**
   * Wait for the OTP input UI to be visible
   */
  async waitForVisible(timeout = 10000): Promise<void> {
    await expect(this.container).toBeVisible({ timeout })
  }

  /**
   * Enter an 8-digit OTP code
   * @param code - 8-digit verification code string
   */
  async enterCode(code: string): Promise<void> {
    if (code.length !== 8 || !/^\d{8}$/.test(code)) {
      throw new Error('OTP code must be exactly 8 digits')
    }

    // Find all individual digit inputs
    const digitInputs = this.page.locator('input[maxlength="1"]')
    const count = await digitInputs.count()

    if (count === 8) {
      // Individual digit inputs - fill each one
      for (let i = 0; i < 8; i++) {
        await digitInputs.nth(i).fill(code[i])
      }
    } else {
      // Single input field - type the full code
      await this.container.fill(code)
    }
  }

  /**
   * Paste an 8-digit OTP code using clipboard
   * @param code - 8-digit verification code string
   */
  async pasteCode(code: string): Promise<void> {
    // Focus the first input
    const firstInput = this.page.locator('input[maxlength="1"]').first()
    await firstInput.focus()

    // Paste the code
    await this.page.evaluate((otp) => {
      const input = document.activeElement as HTMLInputElement
      if (input) {
        const event = new Event('paste', { bubbles: true })
        Object.defineProperty(event, 'clipboardData', {
          value: {
            getData: () => otp,
          },
        })
        input.dispatchEvent(event)
      }
    }, code)
  }

  /**
   * Clear all OTP digits
   */
  async clear(): Promise<void> {
    const digitInputs = this.page.locator('input[maxlength="1"]')
    const count = await digitInputs.count()

    if (count === 8) {
      for (let i = 0; i < 8; i++) {
        await digitInputs.nth(i).clear()
      }
    } else {
      await this.container.clear()
    }
  }

  /**
   * Get the currently entered code
   */
  async getEnteredCode(): Promise<string> {
    const digitInputs = this.page.locator('input[maxlength="1"]')
    const count = await digitInputs.count()

    if (count === 8) {
      const digits: string[] = []
      for (let i = 0; i < 8; i++) {
        const value = await digitInputs.nth(i).inputValue()
        digits.push(value)
      }
      return digits.join('')
    }

    return await this.container.inputValue()
  }

  /**
   * Check if the resend code option is available
   */
  async isResendAvailable(): Promise<boolean> {
    const resendButton = this.page.getByRole('button', { name: /resend/i })
    return resendButton.isVisible()
  }

  /**
   * Click the resend code button
   */
  async clickResend(): Promise<void> {
    const resendButton = this.page.getByRole('button', { name: /resend/i })
    await resendButton.click()
  }

  /**
   * Check if the "change email" option is available
   */
  async isChangeEmailAvailable(): Promise<boolean> {
    const changeButton = this.page.getByRole('button', { name: /change|different email/i })
    return changeButton.isVisible()
  }

  /**
   * Click to change/edit email address
   */
  async clickChangeEmail(): Promise<void> {
    const changeButton = this.page.getByRole('button', { name: /change|different email/i })
    await changeButton.click()
  }

  /**
   * Get the email address that the code was sent to (if displayed)
   */
  async getSentToEmail(): Promise<string | null> {
    const emailText = this.page.locator('text=/sent.*@.*\\..*/')
    if (await emailText.isVisible()) {
      const text = await emailText.textContent()
      const match = text?.match(/[\w.-]+@[\w.-]+\.\w+/)
      return match ? match[0] : null
    }
    return null
  }
}

/**
 * Factory function to create an OTPInputPageObject
 */
export function createOTPInput(page: Page): OTPInputPageObject {
  return new OTPInputPageObject(page)
}
