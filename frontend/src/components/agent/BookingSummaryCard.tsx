/**
 * Booking Summary Card
 *
 * Displays a summary of a reservation with key details.
 * Used in chat messages to show booking confirmations and status.
 */

'use client'

import * as React from 'react'

// === Types ===

interface BookingSummaryCardProps {
  reservationId: string
  checkIn: string
  checkOut: string
  nights: number
  guests: {
    adults: number
    children?: number
  }
  totalAmount: number
  paymentStatus: string
  reservationStatus: string
  className?: string
}

// === Helper Functions ===

function formatDate(dateStr: string): string {
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-GB', {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    })
  } catch {
    return dateStr
  }
}

function getStatusColor(status: string): { bg: string; text: string } {
  switch (status.toLowerCase()) {
    case 'confirmed':
      return { bg: 'bg-green-100', text: 'text-green-800' }
    case 'pending':
      return { bg: 'bg-yellow-100', text: 'text-yellow-800' }
    case 'cancelled':
      return { bg: 'bg-red-100', text: 'text-red-800' }
    case 'paid':
      return { bg: 'bg-green-100', text: 'text-green-800' }
    case 'refunded':
      return { bg: 'bg-gray-100', text: 'text-gray-800' }
    default:
      return { bg: 'bg-gray-100', text: 'text-gray-600' }
  }
}

// === Component ===

export function BookingSummaryCard({
  reservationId,
  checkIn,
  checkOut,
  nights,
  guests,
  totalAmount,
  paymentStatus,
  reservationStatus,
  className = '',
}: BookingSummaryCardProps) {
  const statusColors = getStatusColor(reservationStatus)
  const paymentColors = getStatusColor(paymentStatus)

  const totalGuests = guests.adults + (guests.children || 0)

  return (
    <div
      className={`booking-summary-card border border-gray-200 rounded-xl overflow-hidden ${className}`}
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-4 py-3">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-wide opacity-80">
              Reservation
            </p>
            <p className="font-mono font-semibold">{reservationId}</p>
          </div>
          <div
            className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors.bg} ${statusColors.text}`}
          >
            {reservationStatus}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4 bg-white">
        {/* Dates */}
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <p className="text-xs text-gray-500 uppercase tracking-wide">
              Check-in
            </p>
            <p className="font-medium text-gray-900">{formatDate(checkIn)}</p>
            <p className="text-xs text-gray-500">From 3:00 PM</p>
          </div>
          <div className="flex flex-col items-center px-3">
            <span className="text-gray-400">→</span>
            <span className="text-xs text-gray-500">{nights} nights</span>
          </div>
          <div className="flex-1 text-right">
            <p className="text-xs text-gray-500 uppercase tracking-wide">
              Check-out
            </p>
            <p className="font-medium text-gray-900">{formatDate(checkOut)}</p>
            <p className="text-xs text-gray-500">By 11:00 AM</p>
          </div>
        </div>

        {/* Divider */}
        <div className="border-t border-gray-100" />

        {/* Guests & Payment */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide">
              Guests
            </p>
            <p className="font-medium text-gray-900">
              {guests.adults} adult{guests.adults !== 1 ? 's' : ''}
              {guests.children ? `, ${guests.children} child${guests.children !== 1 ? 'ren' : ''}` : ''}
            </p>
            <p className="text-xs text-gray-500">{totalGuests} total</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-500 uppercase tracking-wide">
              Payment
            </p>
            <span
              className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${paymentColors.bg} ${paymentColors.text}`}
            >
              {paymentStatus}
            </span>
          </div>
        </div>

        {/* Total */}
        <div className="border-t border-gray-100 pt-3">
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Total</span>
            <span className="text-xl font-bold text-gray-900">
              €{totalAmount.toFixed(2)}
            </span>
          </div>
        </div>
      </div>

      {/* Footer */}
      {reservationStatus.toLowerCase() === 'confirmed' && (
        <div className="bg-green-50 px-4 py-2 text-center">
          <p className="text-sm text-green-800">
            ✓ Your booking is confirmed! See you soon.
          </p>
        </div>
      )}
      {reservationStatus.toLowerCase() === 'pending' &&
        paymentStatus.toLowerCase() === 'pending' && (
          <div className="bg-yellow-50 px-4 py-2 text-center">
            <p className="text-sm text-yellow-800">
              ⏳ Complete payment to confirm your booking
            </p>
          </div>
        )}
    </div>
  )
}

export default BookingSummaryCard
