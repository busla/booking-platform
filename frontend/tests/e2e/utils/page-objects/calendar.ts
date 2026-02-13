/**
 * Calendar Page Object
 *
 * Helper functions for interacting with the DateRangePicker calendar
 * component in E2E tests.
 */

import { type Page, type Locator, expect } from '@playwright/test'

/**
 * Calendar page object for date selection interactions
 */
export class CalendarPageObject {
  readonly page: Page
  readonly dateRangePicker: Locator
  readonly calendar: Locator

  constructor(page: Page) {
    this.page = page
    this.dateRangePicker = page.locator('.date-range-picker')
    this.calendar = page.locator('[role="grid"]')
  }

  /**
   * Wait for the date picker to be visible
   */
  async waitForVisible(timeout = 10000): Promise<void> {
    await expect(this.dateRangePicker).toBeVisible({ timeout })
  }

  /**
   * Select a date by clicking on the day button
   * @param day - Day number to select (1-31)
   * @param monthOffset - Which month to select from (0 = current visible, 1 = next month)
   */
  async selectDate(day: number, monthOffset = 0): Promise<void> {
    const calendars = this.page.locator('[role="grid"]')
    const targetCalendar = calendars.nth(monthOffset)

    const dayButton = targetCalendar.getByRole('gridcell', { name: String(day) })
    await dayButton.click()
  }

  /**
   * Select a date range by clicking check-in and check-out dates
   * @param checkInDay - Check-in day (1-31)
   * @param checkOutDay - Check-out day (1-31)
   * @param checkOutMonthOffset - Month offset for check-out (0 = same month, 1 = next month)
   */
  async selectDateRange(
    checkInDay: number,
    checkOutDay: number,
    checkOutMonthOffset = 0
  ): Promise<void> {
    // Select check-in date (first visible month)
    await this.selectDate(checkInDay, 0)

    // Select check-out date
    await this.selectDate(checkOutDay, checkOutMonthOffset)
  }

  /**
   * Navigate to the next month(s)
   * @param times - Number of times to click next
   */
  async navigateToNextMonth(times = 1): Promise<void> {
    const nextButton = this.page.getByRole('button', { name: /next/i })
    for (let i = 0; i < times; i++) {
      await nextButton.click()
    }
  }

  /**
   * Navigate to the previous month(s)
   * @param times - Number of times to click previous
   */
  async navigateToPreviousMonth(times = 1): Promise<void> {
    const prevButton = this.page.getByRole('button', { name: /previous/i })
    for (let i = 0; i < times; i++) {
      await prevButton.click()
    }
  }

  /**
   * Get the currently displayed month name(s)
   */
  async getDisplayedMonths(): Promise<string[]> {
    const monthLabels = this.page.locator('[class*="month-caption"], [class*="month-name"]')
    return monthLabels.allTextContents()
  }

  /**
   * Check if a specific date is available (not disabled)
   * @param day - Day number to check
   * @param monthOffset - Which month (0 = first visible, 1 = second visible)
   */
  async isDateAvailable(day: number, monthOffset = 0): Promise<boolean> {
    const calendars = this.page.locator('[role="grid"]')
    const targetCalendar = calendars.nth(monthOffset)
    const dayButton = targetCalendar.getByRole('gridcell', { name: String(day) })

    const isDisabled = await dayButton.getAttribute('aria-disabled')
    return isDisabled !== 'true'
  }

  /**
   * Get all disabled dates in the visible calendar
   */
  async getDisabledDates(): Promise<string[]> {
    const disabledCells = this.page.locator('[role="gridcell"][aria-disabled="true"]')
    return disabledCells.allTextContents()
  }
}

/**
 * Factory function to create a CalendarPageObject
 */
export function createCalendar(page: Page): CalendarPageObject {
  return new CalendarPageObject(page)
}
