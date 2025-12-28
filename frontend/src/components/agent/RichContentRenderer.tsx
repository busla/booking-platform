/**
 * Rich Content Renderer
 *
 * Renders structured responses from the booking agent, detecting
 * and delegating to specialized components based on content type.
 * Supports availability calendars, booking summaries, pricing tables, etc.
 */

'use client'

import * as React from 'react'
import { BookingSummaryCard } from './BookingSummaryCard'
import { AvailabilityCalendar } from './AvailabilityCalendar'

// === Types ===

/**
 * Structured content types that can be rendered.
 * These match the tool response structures from the backend.
 */
export interface AvailabilityData {
  type: 'availability'
  check_in: string
  check_out: string
  is_available: boolean
  unavailable_dates?: string[]
  message?: string
}

export interface CalendarData {
  type: 'calendar'
  month: number
  year: number
  dates: Array<{
    date: string
    status: 'available' | 'booked' | 'blocked'
  }>
}

export interface PricingData {
  type: 'pricing'
  check_in: string
  check_out: string
  nights: number
  nightly_rate_eur: number
  cleaning_fee_eur: number
  total_eur: number
  season_name?: string
  message?: string
}

export interface BookingSummaryData {
  type: 'booking_summary'
  reservation_id: string
  check_in: string
  check_out: string
  nights: number
  num_adults: number
  num_children?: number
  total_amount_eur: number
  payment_status: string
  reservation_status: string
  message?: string
}

export interface SeasonalRatesData {
  type: 'seasonal_rates'
  seasons: Array<{
    name: string
    period?: string
    start_date?: string
    end_date?: string
    nightly_rate_eur: number
    minimum_nights: number
  }>
  cleaning_fee_eur: number
  message?: string
}

export type RichContent =
  | AvailabilityData
  | CalendarData
  | PricingData
  | BookingSummaryData
  | SeasonalRatesData
  | { type: 'text'; content: string }

// === Content Detection ===

/**
 * Attempts to parse structured data from a message.
 * Returns null if no structured content is detected.
 */
export function detectStructuredContent(text: string): RichContent | null {
  // Try to detect JSON-like structured responses
  // This is a simple heuristic - in production, the agent would return
  // structured data in a more explicit format
  try {
    // Check for code blocks with JSON
    const jsonMatch = text.match(/```json\n([\s\S]*?)\n```/)
    if (jsonMatch && jsonMatch[1]) {
      const parsed = JSON.parse(jsonMatch[1])
      if (parsed.type) {
        return parsed as RichContent
      }
    }

    // Check for inline JSON objects
    const inlineMatch = text.match(/\{[\s\S]*"type"[\s\S]*\}/)
    if (inlineMatch && inlineMatch[0]) {
      const parsed = JSON.parse(inlineMatch[0])
      if (parsed.type) {
        return parsed as RichContent
      }
    }
  } catch {
    // Not valid JSON, return null
  }

  return null
}

// === Main Component ===

interface RichContentRendererProps {
  content: string | RichContent
  className?: string
}

export function RichContentRenderer({
  content,
  className = '',
}: RichContentRendererProps) {
  // If content is a string, try to detect structured data
  const structuredContent: RichContent | null =
    typeof content === 'string'
      ? detectStructuredContent(content) || { type: 'text', content }
      : content

  // Render based on content type
  switch (structuredContent.type) {
    case 'availability':
      return (
        <AvailabilityResult
          data={structuredContent}
          className={className}
        />
      )

    case 'calendar':
      return (
        <AvailabilityCalendar
          month={structuredContent.month}
          year={structuredContent.year}
          dates={structuredContent.dates}
          className={className}
        />
      )

    case 'pricing':
      return (
        <PricingResult
          data={structuredContent}
          className={className}
        />
      )

    case 'booking_summary':
      return (
        <BookingSummaryCard
          reservationId={structuredContent.reservation_id}
          checkIn={structuredContent.check_in}
          checkOut={structuredContent.check_out}
          nights={structuredContent.nights}
          guests={{ adults: structuredContent.num_adults, children: structuredContent.num_children }}
          totalAmount={structuredContent.total_amount_eur}
          paymentStatus={structuredContent.payment_status}
          reservationStatus={structuredContent.reservation_status}
          className={className}
        />
      )

    case 'seasonal_rates':
      return (
        <SeasonalRatesTable
          data={structuredContent}
          className={className}
        />
      )

    case 'text':
    default:
      return (
        <div className={`whitespace-pre-wrap ${className}`}>
          {typeof content === 'string' ? content : structuredContent.content}
        </div>
      )
  }
}

// === Sub-components ===

interface AvailabilityResultProps {
  data: AvailabilityData
  className?: string
}

function AvailabilityResult({ data, className = '' }: AvailabilityResultProps) {
  return (
    <div className={`availability-result ${className}`}>
      <div
        className={`flex items-center gap-2 p-3 rounded-lg ${
          data.is_available
            ? 'bg-green-50 text-green-800'
            : 'bg-red-50 text-red-800'
        }`}
      >
        <span className="text-lg">
          {data.is_available ? '✓' : '✗'}
        </span>
        <div>
          <p className="font-medium">
            {data.is_available ? 'Available!' : 'Not Available'}
          </p>
          <p className="text-sm opacity-80">
            {data.check_in} → {data.check_out}
          </p>
          {data.unavailable_dates && data.unavailable_dates.length > 0 && (
            <p className="text-sm mt-1">
              Unavailable: {data.unavailable_dates.join(', ')}
            </p>
          )}
        </div>
      </div>
      {data.message && (
        <p className="mt-2 text-sm text-gray-600">{data.message}</p>
      )}
    </div>
  )
}

interface PricingResultProps {
  data: PricingData
  className?: string
}

function PricingResult({ data, className = '' }: PricingResultProps) {
  return (
    <div className={`pricing-result bg-gray-50 rounded-lg p-4 ${className}`}>
      <div className="flex justify-between items-center mb-3">
        <h4 className="font-semibold text-gray-900">Price Quote</h4>
        {data.season_name && (
          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
            {data.season_name}
          </span>
        )}
      </div>

      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-600">
            {data.nights} nights × €{data.nightly_rate_eur.toFixed(2)}
          </span>
          <span>€{(data.nights * data.nightly_rate_eur).toFixed(2)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Cleaning fee</span>
          <span>€{data.cleaning_fee_eur.toFixed(2)}</span>
        </div>
        <div className="border-t pt-2 flex justify-between font-semibold">
          <span>Total</span>
          <span>€{data.total_eur.toFixed(2)}</span>
        </div>
      </div>

      {data.message && (
        <p className="mt-3 text-sm text-gray-600">{data.message}</p>
      )}
    </div>
  )
}

interface SeasonalRatesTableProps {
  data: SeasonalRatesData
  className?: string
}

function SeasonalRatesTable({ data, className = '' }: SeasonalRatesTableProps) {
  return (
    <div className={`seasonal-rates ${className}`}>
      <h4 className="font-semibold text-gray-900 mb-3">Seasonal Rates</h4>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left p-2 font-medium">Season</th>
              <th className="text-left p-2 font-medium">Period</th>
              <th className="text-right p-2 font-medium">Rate/Night</th>
              <th className="text-right p-2 font-medium">Min Stay</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {data.seasons.map((season, index) => (
              <tr key={index} className="hover:bg-gray-50">
                <td className="p-2 font-medium">{season.name}</td>
                <td className="p-2 text-gray-600">
                  {season.period ||
                    (season.start_date && season.end_date
                      ? `${season.start_date} - ${season.end_date}`
                      : '—')}
                </td>
                <td className="p-2 text-right">
                  €{season.nightly_rate_eur.toFixed(2)}
                </td>
                <td className="p-2 text-right">
                  {season.minimum_nights} nights
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="mt-2 text-xs text-gray-500">
        + €{data.cleaning_fee_eur.toFixed(2)} cleaning fee per stay
      </p>

      {data.message && (
        <p className="mt-3 text-sm text-gray-600">{data.message}</p>
      )}
    </div>
  )
}

export default RichContentRenderer
