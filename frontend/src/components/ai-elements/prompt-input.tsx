/**
 * Prompt Input Components for AI Elements
 *
 * These components provide the input interface for sending messages.
 * Based on the ai-elements package patterns for AI SDK v6.
 */

'use client'

import * as React from 'react'

// === Input (Form Wrapper) ===

interface InputProps extends React.FormHTMLAttributes<HTMLFormElement> {
  children: React.ReactNode
}

export function Input({ children, className = '', onSubmit, ...props }: InputProps) {
  return (
    <form
      className={`prompt-input ${className}`}
      onSubmit={onSubmit}
      {...props}
    >
      {children}
    </form>
  )
}

// === PromptInputTextarea ===

type PromptInputTextareaProps = React.TextareaHTMLAttributes<HTMLTextAreaElement>

export const PromptInputTextarea = React.forwardRef<
  HTMLTextAreaElement,
  PromptInputTextareaProps
>(function PromptInputTextarea({ className = '', onKeyDown, ...props }, ref) {
  const textareaRef = React.useRef<HTMLTextAreaElement>(null)
  const combinedRef = (ref as React.RefObject<HTMLTextAreaElement>) || textareaRef

  // Auto-resize textarea
  React.useEffect(() => {
    const textarea = combinedRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`
    }
  }, [props.value, combinedRef])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      const form = e.currentTarget.form
      if (form) {
        form.requestSubmit()
      }
    }
    onKeyDown?.(e)
  }

  return (
    <textarea
      ref={combinedRef}
      className={`prompt-input-textarea w-full resize-none border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${className}`}
      rows={1}
      onKeyDown={handleKeyDown}
      {...props}
    />
  )
})

// === PromptInputSubmit ===

type SubmitStatus = 'ready' | 'streaming' | 'disabled'

interface PromptInputSubmitProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  status?: SubmitStatus
}

export function PromptInputSubmit({
  status = 'ready',
  disabled,
  className = '',
  children,
  ...props
}: PromptInputSubmitProps) {
  const isDisabled = disabled || status === 'disabled'
  const isStreaming = status === 'streaming'

  return (
    <button
      type="submit"
      disabled={isDisabled}
      className={`prompt-input-submit inline-flex items-center justify-center w-8 h-8 rounded-lg transition-colors ${
        isDisabled
          ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
          : isStreaming
            ? 'bg-red-500 text-white hover:bg-red-600'
            : 'bg-blue-600 text-white hover:bg-blue-700'
      } ${className}`}
      aria-label={isStreaming ? 'Stop generating' : 'Send message'}
      {...props}
    >
      {children || (
        isStreaming ? (
          // Stop icon
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="currentColor"
          >
            <rect x="6" y="6" width="12" height="12" rx="2" />
          </svg>
        ) : (
          // Send icon (arrow up)
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="m5 12 7-7 7 7" />
            <path d="M12 19V5" />
          </svg>
        )
      )}
    </button>
  )
}

// === PromptInputWrapper (for combining textarea + button) ===

interface PromptInputWrapperProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

export function PromptInputWrapper({
  children,
  className = '',
  ...props
}: PromptInputWrapperProps) {
  return (
    <div
      className={`prompt-input-wrapper relative flex items-end gap-2 ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}
