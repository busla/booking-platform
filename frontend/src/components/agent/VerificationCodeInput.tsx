/**
 * Verification Code Input Component
 *
 * A specialized input for entering 6-digit verification codes.
 * Used for email verification in the booking flow.
 */

'use client'

import * as React from 'react'

// === Types ===

interface VerificationCodeInputProps {
  length?: number
  onComplete?: (code: string) => void
  onChange?: (code: string) => void
  disabled?: boolean
  error?: string
  autoFocus?: boolean
  className?: string
}

// === Component ===

export function VerificationCodeInput({
  length = 6,
  onComplete,
  onChange,
  disabled = false,
  error,
  autoFocus = true,
  className = '',
}: VerificationCodeInputProps) {
  const [values, setValues] = React.useState<string[]>(Array(length).fill(''))
  const inputRefs = React.useRef<(HTMLInputElement | null)[]>([])

  // Focus first input on mount
  React.useEffect(() => {
    if (autoFocus && inputRefs.current[0]) {
      inputRefs.current[0].focus()
    }
  }, [autoFocus])

  // Call onChange when values change
  React.useEffect(() => {
    const code = values.join('')
    onChange?.(code)
  }, [values, onChange])

  const handleChange = (index: number, value: string) => {
    // Only allow single digits
    const digit = value.replace(/\D/g, '').slice(-1)

    const newValues = [...values]
    newValues[index] = digit
    setValues(newValues)

    // Move to next input if digit entered
    if (digit && index < length - 1) {
      inputRefs.current[index + 1]?.focus()
    }

    // Check if complete
    const code = newValues.join('')
    if (code.length === length && !newValues.includes('')) {
      onComplete?.(code)
    }
  }

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    // Handle backspace
    if (e.key === 'Backspace') {
      e.preventDefault()

      if (values[index]) {
        // Clear current input
        const newValues = [...values]
        newValues[index] = ''
        setValues(newValues)
      } else if (index > 0) {
        // Move to previous input and clear
        const newValues = [...values]
        newValues[index - 1] = ''
        setValues(newValues)
        inputRefs.current[index - 1]?.focus()
      }
    }

    // Handle arrow keys
    if (e.key === 'ArrowLeft' && index > 0) {
      e.preventDefault()
      inputRefs.current[index - 1]?.focus()
    }
    if (e.key === 'ArrowRight' && index < length - 1) {
      e.preventDefault()
      inputRefs.current[index + 1]?.focus()
    }
  }

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault()
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, length)

    if (pastedData) {
      const newValues = [...values]
      for (let i = 0; i < pastedData.length; i++) {
        const digit = pastedData[i]
        if (digit !== undefined) {
          newValues[i] = digit
        }
      }
      setValues(newValues)

      // Focus last filled input or first empty
      const focusIndex = Math.min(pastedData.length, length - 1)
      inputRefs.current[focusIndex]?.focus()

      // Check if complete
      if (pastedData.length === length) {
        onComplete?.(pastedData)
      }
    }
  }

  const handleFocus = (e: React.FocusEvent<HTMLInputElement>) => {
    e.target.select()
  }

  return (
    <div className={`verification-code-input ${className}`}>
      <div className="flex items-center justify-center gap-2">
        {values.map((value, index) => (
          <React.Fragment key={index}>
            <input
              ref={(el) => {
                inputRefs.current[index] = el
              }}
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              maxLength={1}
              value={value}
              onChange={(e) => handleChange(index, e.target.value)}
              onKeyDown={(e) => handleKeyDown(index, e)}
              onPaste={handlePaste}
              onFocus={handleFocus}
              disabled={disabled}
              className={`w-12 h-14 text-center text-2xl font-bold border-2 rounded-lg transition-colors
                ${error ? 'border-red-400 focus:border-red-500 focus:ring-red-200' : 'border-gray-200 focus:border-blue-500 focus:ring-blue-200'}
                ${disabled ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-white text-gray-900'}
                focus:outline-none focus:ring-2
              `}
              aria-label={`Digit ${index + 1} of ${length}`}
            />
            {/* Add separator after 3rd digit */}
            {index === 2 && (
              <span className="text-gray-400 text-xl font-light">-</span>
            )}
          </React.Fragment>
        ))}
      </div>

      {error && (
        <p className="mt-2 text-sm text-red-600 text-center" role="alert">
          {error}
        </p>
      )}

      <p className="mt-3 text-xs text-gray-500 text-center">
        Enter the 6-digit code sent to your email
      </p>
    </div>
  )
}

// === Wrapper Component for Chat ===

interface VerificationCodeCardProps {
  email: string
  onSubmit: (code: string) => void
  onResend?: () => void
  isLoading?: boolean
  error?: string
  expiresInMinutes?: number
  className?: string
}

export function VerificationCodeCard({
  email,
  onSubmit,
  onResend,
  isLoading = false,
  error,
  expiresInMinutes = 10,
  className = '',
}: VerificationCodeCardProps) {
  const [code, setCode] = React.useState('')
  const [resendDisabled, setResendDisabled] = React.useState(false)
  const [resendCountdown, setResendCountdown] = React.useState(0)

  const handleResend = () => {
    if (resendDisabled || !onResend) return

    onResend()
    setResendDisabled(true)
    setResendCountdown(30)

    const interval = setInterval(() => {
      setResendCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(interval)
          setResendDisabled(false)
          return 0
        }
        return prev - 1
      })
    }, 1000)
  }

  return (
    <div
      className={`verification-code-card bg-white border border-gray-200 rounded-xl p-6 ${className}`}
    >
      {/* Header */}
      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center w-12 h-12 bg-blue-100 rounded-full mb-3">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="text-blue-600"
          >
            <rect width="20" height="16" x="2" y="4" rx="2" />
            <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-gray-900">
          Verify your email
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          We sent a code to <span className="font-medium">{email}</span>
        </p>
      </div>

      {/* Code Input */}
      <VerificationCodeInput
        onComplete={onSubmit}
        onChange={setCode}
        disabled={isLoading}
        error={error}
      />

      {/* Submit Button */}
      <button
        type="button"
        onClick={() => code.length === 6 && onSubmit(code)}
        disabled={code.length !== 6 || isLoading}
        className={`w-full mt-6 py-3 px-4 rounded-lg font-medium transition-colors
          ${code.length === 6 && !isLoading
            ? 'bg-blue-600 text-white hover:bg-blue-700'
            : 'bg-gray-100 text-gray-400 cursor-not-allowed'
          }
        `}
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <svg
              className="animate-spin h-5 w-5"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            Verifying...
          </span>
        ) : (
          'Verify Code'
        )}
      </button>

      {/* Resend Link */}
      {onResend && (
        <div className="mt-4 text-center">
          <button
            type="button"
            onClick={handleResend}
            disabled={resendDisabled}
            className={`text-sm ${
              resendDisabled
                ? 'text-gray-400 cursor-not-allowed'
                : 'text-blue-600 hover:text-blue-700 hover:underline'
            }`}
          >
            {resendDisabled
              ? `Resend code in ${resendCountdown}s`
              : "Didn't receive the code? Resend"}
          </button>
        </div>
      )}

      {/* Expiry Note */}
      <p className="mt-4 text-xs text-gray-400 text-center">
        Code expires in {expiresInMinutes} minutes
      </p>
    </div>
  )
}

export default VerificationCodeInput
