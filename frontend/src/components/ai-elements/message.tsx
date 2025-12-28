/**
 * Message Components for AI Elements
 *
 * These components handle the display of individual chat messages.
 * Based on the ai-elements package patterns for AI SDK v6.
 */

'use client'

import * as React from 'react'

// === Message ===

type MessageRole = 'user' | 'assistant' | 'system'

interface MessageProps extends React.HTMLAttributes<HTMLDivElement> {
  from: MessageRole
  children: React.ReactNode
}

export function Message({ from, children, className = '', ...props }: MessageProps) {
  const isUser = from === 'user'

  return (
    <div
      className={`message flex ${isUser ? 'justify-end' : 'justify-start'} ${className}`}
      data-role={from}
      {...props}
    >
      <div
        className={`message-bubble max-w-[80%] ${
          isUser
            ? 'bg-blue-600 text-white rounded-2xl rounded-br-md'
            : 'bg-gray-100 text-gray-900 rounded-2xl rounded-bl-md'
        } px-4 py-3`}
      >
        {children}
      </div>
    </div>
  )
}

// === MessageContent ===

interface MessageContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

export function MessageContent({ children, className = '', ...props }: MessageContentProps) {
  return (
    <div className={`message-content ${className}`} {...props}>
      {children}
    </div>
  )
}

// === MessageResponse ===

interface MessageResponseProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

export function MessageResponse({ children, className = '', ...props }: MessageResponseProps) {
  return (
    <div
      className={`message-response prose prose-sm max-w-none ${className}`}
      {...props}
    >
      {typeof children === 'string' ? (
        <p className="m-0 whitespace-pre-wrap">{children}</p>
      ) : (
        children
      )}
    </div>
  )
}

// === MessageActions ===

interface MessageActionsProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

export function MessageActions({ children, className = '', ...props }: MessageActionsProps) {
  return (
    <div
      className={`message-actions flex items-center gap-1 mt-1 ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}

// === MessageAction ===

interface MessageActionProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  label: string
  children: React.ReactNode
}

export function MessageAction({
  label,
  children,
  className = '',
  ...props
}: MessageActionProps) {
  return (
    <button
      type="button"
      className={`message-action inline-flex items-center gap-1 px-2 py-1 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors ${className}`}
      title={label}
      aria-label={label}
      {...props}
    >
      {children}
      <span className="sr-only">{label}</span>
    </button>
  )
}

// === MessageLoading ===

type MessageLoadingProps = React.HTMLAttributes<HTMLDivElement>

export function MessageLoading({ className = '', ...props }: MessageLoadingProps) {
  return (
    <div className={`message-loading flex gap-1 ${className}`} {...props}>
      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
    </div>
  )
}
