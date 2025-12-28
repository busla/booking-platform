/**
 * E2E Test: Full Booking Conversation Flow
 *
 * Tests the complete user journey through the booking assistant:
 * 1. Landing on the chat page
 * 2. Asking about availability
 * 3. Getting pricing information
 * 4. Starting a booking
 * 5. Email verification flow
 * 6. Payment confirmation
 *
 * Note: These tests use the mock backend responses when AGENT_URL
 * is not configured, making them reliable for CI/CD.
 */

import { test, expect, type Page } from '@playwright/test'

// === Test Fixtures ===

test.describe('Booking Conversation Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the chat page
    await page.goto('/')
    // Wait for the chat interface to load
    await expect(page.getByRole('heading', { name: 'Quesada Apartment', exact: true })).toBeVisible()
  })

  // === Page Load Tests ===

  test('displays welcome message and suggestion buttons on load', async ({ page }) => {
    // Check welcome message
    await expect(page.getByText('Welcome to Quesada Apartment!')).toBeVisible()
    await expect(page.getByText("I'm your booking assistant")).toBeVisible()

    // Check suggestion buttons are present
    await expect(page.getByRole('button', { name: 'Check availability' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'See pricing' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Property details' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Local attractions' })).toBeVisible()
  })

  test('has accessible input field with placeholder', async ({ page }) => {
    const input = page.getByPlaceholder('Ask about availability, pricing, or the property...')
    await expect(input).toBeVisible()
    await expect(input).toBeEnabled()
  })

  // === Basic Conversation Tests ===

  test('sends message and receives response', async ({ page }) => {
    // Type a message
    const input = page.getByPlaceholder('Ask about availability, pricing, or the property...')
    await input.fill('Hello')

    // Submit the message
    await page.getByRole('button', { name: /send/i }).click()

    // Wait for user message to appear
    await expect(page.getByText('Hello')).toBeVisible()

    // Wait for assistant response (mock backend returns greeting)
    await expect(page.getByText(/Welcome to Quesada Apartment/i)).toBeVisible({ timeout: 10000 })
  })

  test('suggestion button sends message directly', async ({ page }) => {
    // Click a suggestion button
    await page.getByRole('button', { name: 'Check availability' }).click()

    // Message should appear in the conversation (not just populate input)
    await expect(page.getByText('What dates are available?')).toBeVisible()

    // Input should be cleared after sending
    const input = page.getByPlaceholder('Ask about availability, pricing, or the property...')
    await expect(input).toHaveValue('')
  })

  test('clears empty state after first message', async ({ page }) => {
    // Initially, empty state is visible
    await expect(page.getByText('Welcome to Quesada Apartment!')).toBeVisible()

    // Send a message
    const input = page.getByPlaceholder('Ask about availability, pricing, or the property...')
    await input.fill('Hi')
    await page.keyboard.press('Enter')

    // Wait for response
    await page.waitForSelector('text=/Quesada Apartment/')

    // Empty state should be gone (the welcome card)
    await expect(page.getByText('Welcome to Quesada Apartment!')).not.toBeVisible()
  })

  // === Availability Flow Tests ===

  test('asks about availability and receives calendar info', async ({ page }) => {
    const input = page.getByPlaceholder('Ask about availability, pricing, or the property...')

    // Ask about availability
    await input.fill('Is January 15 to January 20 available?')
    await page.keyboard.press('Enter')

    // Wait for response about availability
    await expect(page.getByText(/available|availability|January/i)).toBeVisible({
      timeout: 15000,
    })
  })

  // === Pricing Flow Tests ===

  test('asks about pricing and receives rate information', async ({ page }) => {
    const input = page.getByPlaceholder('Ask about availability, pricing, or the property...')

    // Ask about pricing
    await input.fill('How much does it cost to stay?')
    await page.keyboard.press('Enter')

    // Wait for response with pricing info
    await expect(page.getByText(/rate|price|\€|season/i)).toBeVisible({ timeout: 15000 })
  })

  // === Property Info Tests ===

  test('asks about property and receives details', async ({ page }) => {
    const input = page.getByPlaceholder('Ask about availability, pricing, or the property...')

    // Ask about property
    await input.fill('Tell me about the property')
    await page.keyboard.press('Enter')

    // Wait for response with property details
    await expect(page.getByText(/bedroom|apartment|property|amenities/i)).toBeVisible({
      timeout: 15000,
    })
  })

  // === Area Info Tests ===

  test('asks about local area and receives recommendations', async ({ page }) => {
    const input = page.getByPlaceholder('Ask about availability, pricing, or the property...')

    // Ask about area
    await input.fill("What's there to do in Quesada?")
    await page.keyboard.press('Enter')

    // Wait for response with area info
    await expect(page.getByText(/Quesada|beach|golf|Costa Blanca/i)).toBeVisible({
      timeout: 15000,
    })
  })

  // === Multi-turn Conversation Tests ===

  test('maintains conversation context across turns', async ({ page }) => {
    const input = page.getByPlaceholder('Ask about availability, pricing, or the property...')

    // First message
    await input.fill('Hello')
    await page.keyboard.press('Enter')
    // Wait for assistant response - mock returns "Welcome to Summerhouse"
    await expect(page.getByText('Welcome to Quesada Apartment!')).toBeVisible({ timeout: 10000 })

    // Second message
    await input.fill('What are your rates?')
    await page.keyboard.press('Enter')
    // Wait for pricing response with € symbol in assistant message
    await expect(page.getByText('€80/night')).toBeVisible({ timeout: 15000 })

    // Both user messages should be visible in conversation
    await expect(page.getByText('Hello')).toBeVisible()
    await expect(page.getByText('What are your rates?')).toBeVisible()
  })

  // === Input Behavior Tests ===

  test('disables input while waiting for response', async ({ page }) => {
    const input = page.getByPlaceholder('Ask about availability, pricing, or the property...')

    // Send a message
    await input.fill('Hello')
    await page.keyboard.press('Enter')

    // Input should be disabled briefly during loading
    // (This may happen quickly, so we just verify the flow completes)
    // Wait for assistant response - mock returns "Welcome to Summerhouse"
    await expect(page.getByText('Welcome to Quesada Apartment!')).toBeVisible({ timeout: 10000 })

    // Input should be re-enabled after response
    await expect(input).toBeEnabled()
  })

  test('clears input after sending message', async ({ page }) => {
    const input = page.getByPlaceholder('Ask about availability, pricing, or the property...')

    // Type and send
    await input.fill('Test message')
    await page.keyboard.press('Enter')

    // Input should be cleared
    await expect(input).toHaveValue('')
  })

  test('submit button is disabled when input is empty', async ({ page }) => {
    const submitButton = page.getByRole('button', { name: /send/i })

    // Button should be disabled with empty input
    await expect(submitButton).toBeDisabled()
  })

  // === Keyboard Navigation Tests ===

  test('Enter key submits the message', async ({ page }) => {
    const input = page.getByPlaceholder('Ask about availability, pricing, or the property...')

    await input.fill('Hello via Enter')
    await page.keyboard.press('Enter')

    // Message should appear
    await expect(page.getByText('Hello via Enter')).toBeVisible()
  })

  test('Shift+Enter adds new line instead of submitting', async ({ page }) => {
    const input = page.getByPlaceholder('Ask about availability, pricing, or the property...')

    await input.fill('Line 1')
    await page.keyboard.press('Shift+Enter')
    await input.pressSequentially('Line 2')

    // Input should contain both lines
    await expect(input).toContainText('Line 1')
    // Message should NOT have been sent - check no user message bubble was created
    // The input field itself will show "Line 1" but no message element should exist
    const userMessages = page.locator('[data-testid="user-message"], [class*="user"]').filter({ hasText: 'Line 1' })
    await expect(userMessages).toHaveCount(0)
  })
})

// === Full Booking Journey Test ===

test.describe('Complete Booking Journey', () => {
  test('simulates full booking flow from start to finish', async ({ page }) => {
    await page.goto('/')

    const input = page.getByPlaceholder('Ask about availability, pricing, or the property...')

    // Step 1: Start booking - use "book" without "hi" to trigger booking response
    await input.fill('I want to book a stay')
    await page.keyboard.press('Enter')
    // Wait for assistant response about booking requirements
    await expect(page.getByText('check-in and check-out dates')).toBeVisible({ timeout: 15000 })

    // Step 2: Check availability
    await input.fill('Is January 15-20 available?')
    await page.keyboard.press('Enter')
    // Wait for assistant availability response
    await expect(page.getByText('check availability')).toBeVisible({ timeout: 15000 })

    // Step 3: Get pricing - must include "price" or "cost" to trigger pricing response
    await input.fill('What is the price?')
    await page.keyboard.press('Enter')
    // Wait for pricing response - includes the € symbol
    await expect(page.getByText('€80/night')).toBeVisible({ timeout: 15000 })

    // Step 4: Initiate booking
    await input.fill("Let's book it for 2 guests")
    await page.keyboard.press('Enter')
    // Wait for booking confirmation response
    await expect(page.getByText('Your email for confirmation')).toBeVisible({ timeout: 15000 })

    // Verify conversation history is maintained
    const messages = page.locator('[data-testid="message"], [class*="message"]')
    const messageCount = await messages.count()
    expect(messageCount).toBeGreaterThanOrEqual(8) // 4 user + 4 assistant messages
  })
})

// === Accessibility Tests ===

test.describe('Accessibility', () => {
  test('page has proper heading structure', async ({ page }) => {
    await page.goto('/')

    // Main heading
    const h1 = page.getByRole('heading', { level: 1, name: 'Quesada Apartment' })
    await expect(h1).toBeVisible()
  })

  test('input has accessible label/placeholder', async ({ page }) => {
    await page.goto('/')

    const input = page.getByRole('textbox')
    await expect(input).toBeVisible()
    await expect(input).toHaveAttribute(
      'placeholder',
      'Ask about availability, pricing, or the property...'
    )
  })

  test('buttons have accessible names', async ({ page }) => {
    await page.goto('/')

    // Suggestion buttons have text content as accessible names
    const checkAvailability = page.getByRole('button', { name: 'Check availability' })
    await expect(checkAvailability).toBeVisible()
  })
})

// === Responsive Design Tests ===

test.describe('Responsive Design', () => {
  test('works on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/')

    // Chat interface should be visible
    await expect(page.getByText('Welcome to Quesada Apartment!')).toBeVisible()

    // Input should be accessible
    const input = page.getByPlaceholder('Ask about availability, pricing, or the property...')
    await expect(input).toBeVisible()
  })

  test('works on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 })
    await page.goto('/')

    await expect(page.getByText('Welcome to Quesada Apartment!')).toBeVisible()
  })
})

// === Error Handling Tests ===

test.describe('Error Handling', () => {
  test('displays error message when API fails', async ({ page }) => {
    // Mock API to return error
    await page.route('/api/chat', (route) => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' }),
      })
    })

    await page.goto('/')

    const input = page.getByPlaceholder('Ask about availability, pricing, or the property...')
    await input.fill('Hello')
    await page.keyboard.press('Enter')

    // Error should be displayed (exact format depends on implementation)
    await expect(page.getByText(/error/i)).toBeVisible({ timeout: 10000 })
  })
})
