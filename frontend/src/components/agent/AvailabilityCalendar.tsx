/**
 * Availability Calendar Component
 *
 * Displays a visual calendar showing availability status for each date.
 * Used to show availability in chat responses and booking interface.
 */

'use client'

import * as React from 'react'

// === Types ===

type DateStatus = 'available' | 'booked' | 'blocked' | 'selected'

interface CalendarDate {
  date: string
  status: DateStatus
}

interface AvailabilityCalendarProps {
  month: number
  year: number
  dates: CalendarDate[]
  selectedRange?: { start: string; end: string }
  onDateSelect?: (date: string) => void
  className?: string
}

// === Helper Functions ===

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]

const DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

function getDaysInMonth(year: number, month: number): number {
  return new Date(year, month + 1, 0).getDate()
}

function getFirstDayOfMonth(year: number, month: number): number {
  // Returns 0 (Monday) to 6 (Sunday) for ISO week
  const day = new Date(year, month, 1).getDay()
  return day === 0 ? 6 : day - 1
}

function formatDateKey(year: number, month: number, day: number): string {
  return `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
}

function getStatusStyles(status: DateStatus, isToday: boolean, isPast: boolean): string {
  const base = 'relative flex items-center justify-center rounded-full transition-colors'

  if (isPast) {
    return `${base} text-gray-300 cursor-not-allowed`
  }

  switch (status) {
    case 'available':
      return `${base} bg-green-50 text-green-700 hover:bg-green-100 cursor-pointer ${isToday ? 'ring-2 ring-green-500 ring-offset-1' : ''}`
    case 'booked':
      return `${base} bg-red-50 text-red-400 cursor-not-allowed ${isToday ? 'ring-2 ring-red-300 ring-offset-1' : ''}`
    case 'blocked':
      return `${base} bg-gray-100 text-gray-400 cursor-not-allowed ${isToday ? 'ring-2 ring-gray-400 ring-offset-1' : ''}`
    case 'selected':
      return `${base} bg-blue-600 text-white ${isToday ? 'ring-2 ring-blue-400 ring-offset-1' : ''}`
    default:
      return `${base} text-gray-700 hover:bg-gray-100 ${isToday ? 'ring-2 ring-gray-400 ring-offset-1' : ''}`
  }
}

// === Component ===

export function AvailabilityCalendar({
  month,
  year,
  dates,
  selectedRange,
  onDateSelect,
  className = '',
}: AvailabilityCalendarProps) {
  const daysInMonth = getDaysInMonth(year, month)
  const firstDay = getFirstDayOfMonth(year, month)

  const today = new Date()
  const todayStr = formatDateKey(
    today.getFullYear(),
    today.getMonth(),
    today.getDate()
  )

  // Build lookup map for dates
  const dateStatusMap = React.useMemo(() => {
    const map = new Map<string, DateStatus>()
    dates.forEach((d) => map.set(d.date, d.status))

    // Apply selected range if provided
    if (selectedRange) {
      const start = new Date(selectedRange.start)
      const end = new Date(selectedRange.end)
      const current = new Date(start)

      while (current < end) {
        const isoString = current.toISOString().split('T')[0]
        if (isoString) {
          map.set(isoString, 'selected')
        }
        current.setDate(current.getDate() + 1)
      }
    }

    return map
  }, [dates, selectedRange])

  // Generate calendar grid
  const calendarDays = React.useMemo(() => {
    const days: Array<{ day: number; dateKey: string } | null> = []

    // Empty cells before first day
    for (let i = 0; i < firstDay; i++) {
      days.push(null)
    }

    // Days of month
    for (let day = 1; day <= daysInMonth; day++) {
      days.push({
        day,
        dateKey: formatDateKey(year, month, day),
      })
    }

    return days
  }, [year, month, daysInMonth, firstDay])

  const handleDateClick = (dateKey: string, status: DateStatus | undefined, isPast: boolean) => {
    if (!onDateSelect || isPast || status === 'booked' || status === 'blocked') {
      return
    }
    onDateSelect(dateKey)
  }

  return (
    <div className={`availability-calendar ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h4 className="font-semibold text-gray-900">
          {MONTH_NAMES[month]} {year}
        </h4>
        <div className="flex items-center gap-3 text-xs">
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-green-100 border border-green-300" />
            Available
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-red-100 border border-red-300" />
            Booked
          </span>
        </div>
      </div>

      {/* Day names */}
      <div className="grid grid-cols-7 gap-1 mb-2">
        {DAY_NAMES.map((name) => (
          <div
            key={name}
            className="text-center text-xs font-medium text-gray-500 py-1"
          >
            {name}
          </div>
        ))}
      </div>

      {/* Calendar grid */}
      <div className="grid grid-cols-7 gap-1">
        {calendarDays.map((item, index) => {
          if (!item) {
            return <div key={`empty-${index}`} className="aspect-square" />
          }

          const { day, dateKey } = item
          const status = dateStatusMap.get(dateKey)
          const isToday = dateKey === todayStr
          const isPast = dateKey < todayStr

          return (
            <button
              key={dateKey}
              type="button"
              className={`aspect-square text-sm font-medium ${getStatusStyles(status || 'available', isToday, isPast)}`}
              onClick={() => handleDateClick(dateKey, status, isPast)}
              disabled={isPast || status === 'booked' || status === 'blocked'}
              aria-label={`${day} ${MONTH_NAMES[month]}: ${status || 'available'}`}
            >
              {day}
            </button>
          )
        })}
      </div>

      {/* Legend */}
      <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-500">
        <p>Click available dates to select. Minimum stay requirements may apply.</p>
      </div>
    </div>
  )
}

export default AvailabilityCalendar
