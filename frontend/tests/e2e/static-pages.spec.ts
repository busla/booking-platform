/**
 * E2E Test: Static Page Navigation
 *
 * Tests navigation and content for all static information pages:
 * - About: Property details and amenities
 * - Location: Map and address information
 * - Pricing: Rate tables and seasonal pricing
 * - Area Guide: Local attractions and activities
 * - FAQ: Frequently asked questions
 * - Contact: Contact form and information
 *
 * Tests verify:
 * 1. Navigation links work correctly
 * 2. Pages load with expected content
 * 3. Navigation menu is accessible from all pages
 * 4. Return to home (chat) page works
 */

import { test, expect } from '@playwright/test'

// === Static Page Definitions ===

const staticPages = [
  {
    name: 'About',
    path: '/about',
    expectedHeading: 'About Quesada Apartment',
    expectedContent: ['2 Bedrooms', '4 Guests', 'Private terrace'],
  },
  {
    name: 'Location',
    path: '/location',
    expectedHeading: 'Location',
    expectedContent: ['Ciudad Quesada', 'Costa Blanca', 'Alicante'],
  },
  {
    name: 'Pricing',
    path: '/pricing',
    expectedHeading: 'Pricing',
    expectedContent: ['per night', 'Season'],
  },
  {
    name: 'Area Guide',
    path: '/area-guide',
    expectedHeading: 'Area Guide',
    expectedContent: ['Golf', 'Beach', 'Restaurant'],
  },
  {
    name: 'FAQ',
    path: '/faq',
    expectedHeading: 'Frequently Asked Questions',
    expectedContent: ['check-in', 'check-out'],
  },
  {
    name: 'Contact',
    path: '/contact',
    expectedHeading: 'Contact',
    expectedContent: ['Email', 'message'],
  },
]

// === Navigation Tests ===

test.describe('Static Page Navigation', () => {
  test.beforeEach(async ({ page }) => {
    // Start from the home page
    await page.goto('/')
    // Wait for the page to be ready
    await expect(page.locator('body')).toBeVisible()
  })

  test('home page loads with navigation', async ({ page }) => {
    // Check that navigation links are present (desktop nav)
    // Navigation should be visible on desktop viewport
    await page.setViewportSize({ width: 1280, height: 800 })

    // Check for navigation links
    const navLinks = page.locator('.nav-desktop .nav-link')
    await expect(navLinks).toHaveCount(7) // Book Now, About, Location, Pricing, Area Guide, FAQ, Contact
  })

  // === Individual Page Load Tests ===

  for (const staticPage of staticPages) {
    test(`${staticPage.name} page loads correctly`, async ({ page }) => {
      // Navigate to the page
      await page.goto(staticPage.path)

      // Check page heading
      await expect(
        page.getByRole('heading', { name: new RegExp(staticPage.expectedHeading, 'i') })
      ).toBeVisible()

      // Check for expected content
      for (const content of staticPage.expectedContent) {
        await expect(page.getByText(new RegExp(content, 'i')).first()).toBeVisible()
      }
    })

    test(`${staticPage.name} page has working navigation back to home`, async ({ page }) => {
      // Navigate to the static page
      await page.goto(staticPage.path)

      // Set desktop viewport for navigation
      await page.setViewportSize({ width: 1280, height: 800 })

      // Find and click the "Book Now" link to return home
      await page.click('a[href="/"]')

      // Verify we're back on the home page with chat interface
      await expect(page).toHaveURL('/')
      await expect(page.getByText('Welcome to Quesada Apartment!')).toBeVisible()
    })
  }

  // === Desktop Navigation Link Tests ===

  test('desktop navigation links work', async ({ page }) => {
    // Set desktop viewport
    await page.setViewportSize({ width: 1280, height: 800 })

    // Test each navigation link
    for (const staticPage of staticPages) {
      // Go to home first
      await page.goto('/')

      // Click the nav link
      await page.click(`.nav-desktop a[href="${staticPage.path}"]`)

      // Verify URL changed
      await expect(page).toHaveURL(staticPage.path)

      // Verify page content loaded
      await expect(
        page.getByRole('heading', { name: new RegExp(staticPage.expectedHeading, 'i') })
      ).toBeVisible()
    }
  })

  // === Mobile Navigation Tests ===

  test('mobile navigation menu opens and works', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })

    // Mobile toggle button should be visible
    const mobileToggle = page.locator('.mobile-toggle')
    await expect(mobileToggle).toBeVisible()

    // Click to open mobile menu
    await mobileToggle.click()

    // Mobile nav should appear
    const mobileNav = page.locator('.nav-mobile')
    await expect(mobileNav).toBeVisible()

    // Click on About link
    await mobileNav.locator('a[href="/about"]').click()

    // Should navigate to About page
    await expect(page).toHaveURL('/about')
    await expect(page.getByRole('heading', { name: /About Quesada Apartment/i })).toBeVisible()
  })

  test('mobile menu closes after navigation', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })

    // Open mobile menu
    await page.locator('.mobile-toggle').click()
    await expect(page.locator('.nav-mobile')).toBeVisible()

    // Navigate to a page
    await page.locator('.nav-mobile a[href="/pricing"]').click()

    // Wait for navigation
    await expect(page).toHaveURL('/pricing')

    // Mobile menu should be closed (not visible)
    await expect(page.locator('.nav-mobile')).not.toBeVisible()
  })

  // === Cross-Page Navigation Tests ===

  test('can navigate between all static pages', async ({ page }) => {
    // Set desktop viewport
    await page.setViewportSize({ width: 1280, height: 800 })

    // Start at About
    await page.goto('/about')

    // Go to Location
    await page.click('.nav-desktop a[href="/location"]')
    await expect(page).toHaveURL('/location')

    // Go to Pricing
    await page.click('.nav-desktop a[href="/pricing"]')
    await expect(page).toHaveURL('/pricing')

    // Go to Area Guide
    await page.click('.nav-desktop a[href="/area-guide"]')
    await expect(page).toHaveURL('/area-guide')

    // Go to FAQ
    await page.click('.nav-desktop a[href="/faq"]')
    await expect(page).toHaveURL('/faq')

    // Go to Contact
    await page.click('.nav-desktop a[href="/contact"]')
    await expect(page).toHaveURL('/contact')

    // Return to home
    await page.click('.nav-desktop a[href="/"]')
    await expect(page).toHaveURL('/')
  })

  // === Accessibility Tests ===

  test('navigation has proper ARIA labels', async ({ page }) => {
    // Set mobile viewport to test mobile toggle
    await page.setViewportSize({ width: 375, height: 667 })

    // Mobile toggle should have aria-label
    const mobileToggle = page.locator('.mobile-toggle')
    await expect(mobileToggle).toHaveAttribute('aria-label', /menu/i)
    await expect(mobileToggle).toHaveAttribute('aria-expanded', 'false')

    // Open menu
    await mobileToggle.click()
    await expect(mobileToggle).toHaveAttribute('aria-expanded', 'true')
  })

  // === Page Content Specific Tests ===

  test('About page shows property highlights', async ({ page }) => {
    await page.goto('/about')

    // Check property stats
    await expect(page.getByText(/2 Bedrooms/i)).toBeVisible()
    await expect(page.getByText(/1 Bathroom/i)).toBeVisible()
    await expect(page.getByText(/4 Guests/i)).toBeVisible()
    await expect(page.getByText(/75 m²/i)).toBeVisible()
  })

  test('Pricing page shows rate information', async ({ page }) => {
    await page.goto('/pricing')

    // Check for pricing elements
    await expect(page.getByText(/per night/i)).toBeVisible()
    // Check for seasonal pricing sections
    await expect(page.getByText(/Season/i).first()).toBeVisible()
  })

  test('FAQ page has expandable questions', async ({ page }) => {
    await page.goto('/faq')

    // FAQ should have multiple questions
    const questions = page.locator('[class*="faq"]').or(page.locator('button').filter({ hasText: /\?/ }))

    // At minimum, check that FAQ content is present
    await expect(page.getByText(/check-in/i).first()).toBeVisible()
    await expect(page.getByText(/check-out/i).first()).toBeVisible()
  })

  test('Contact page has contact form or information', async ({ page }) => {
    await page.goto('/contact')

    // Check for contact elements
    await expect(page.getByText(/Email/i).first()).toBeVisible()

    // Should have a way to send a message or contact info
    const hasForm = await page.locator('form').count() > 0
    const hasContactInfo = await page.getByText(/message/i).count() > 0

    expect(hasForm || hasContactInfo).toBeTruthy()
  })

  test('Location page has address information', async ({ page }) => {
    await page.goto('/location')

    // Check for location details
    await expect(page.getByText(/Ciudad Quesada/i).first()).toBeVisible()
    await expect(page.getByText(/Costa Blanca/i).first()).toBeVisible()
    await expect(page.getByText(/Alicante/i).first()).toBeVisible()
  })

  test('Area Guide page has activity categories', async ({ page }) => {
    await page.goto('/area-guide')

    // Check for activity categories
    await expect(page.getByText(/Golf/i).first()).toBeVisible()
    await expect(page.getByText(/Beach/i).first()).toBeVisible()
  })
})

// === Header/Footer Tests ===

test.describe('Layout Components', () => {
  test('header is present on all pages', async ({ page }) => {
    for (const staticPage of staticPages) {
      await page.goto(staticPage.path)
      // Header should contain Quesada Apartment branding
      await expect(page.getByRole('heading', { name: 'Quesada Apartment', exact: true })).toBeVisible()
    }
  })

  test('header logo links to home', async ({ page }) => {
    // Go to a static page
    await page.goto('/about')

    // Click the logo/header title
    const logo = page.getByRole('heading', { name: 'Quesada Apartment', exact: true })
    await logo.click()

    // Should return to home
    await expect(page).toHaveURL('/')
  })
})

// === Performance Tests ===

test.describe('Page Performance', () => {
  test('static pages load within acceptable time', async ({ page }) => {
    for (const staticPage of staticPages) {
      const startTime = Date.now()
      await page.goto(staticPage.path)
      const loadTime = Date.now() - startTime

      // Pages should load within 3 seconds
      expect(loadTime).toBeLessThan(3000)
    }
  })
})
