/**
 * Conversation Components for AI Elements
 *
 * These components provide the structure for a chat conversation interface.
 * Based on the ai-elements package patterns for AI SDK v6.
 */

'use client'

import * as React from 'react'

// === Context ===

interface ConversationContextValue {
  scrollToBottom: () => void
  isAtBottom: boolean
  contentRef: React.RefObject<HTMLDivElement>
}

const ConversationContext = React.createContext<ConversationContextValue | null>(null)

export function useConversation() {
  const context = React.useContext(ConversationContext)
  if (!context) {
    throw new Error('useConversation must be used within a Conversation component')
  }
  return context
}

// === Conversation ===

interface ConversationProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

export function Conversation({ children, className = '', ...props }: ConversationProps) {
  const contentRef = React.useRef<HTMLDivElement>(null)
  const [isAtBottom, setIsAtBottom] = React.useState(true)

  const scrollToBottom = React.useCallback(() => {
    if (contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight
    }
  }, [])

  // Track scroll position
  React.useEffect(() => {
    const element = contentRef.current
    if (!element) return

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = element
      const atBottom = scrollHeight - scrollTop - clientHeight < 100
      setIsAtBottom(atBottom)
    }

    element.addEventListener('scroll', handleScroll)
    return () => element.removeEventListener('scroll', handleScroll)
  }, [])

  const contextValue = React.useMemo(
    () => ({ scrollToBottom, isAtBottom, contentRef }),
    [scrollToBottom, isAtBottom]
  )

  return (
    <ConversationContext.Provider value={contextValue}>
      <div
        className={`conversation flex flex-col flex-1 overflow-hidden relative ${className}`}
        {...props}
      >
        {children}
      </div>
    </ConversationContext.Provider>
  )
}

// === ConversationContent ===

interface ConversationContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

export function ConversationContent({
  children,
  className = '',
  ...props
}: ConversationContentProps) {
  const { contentRef, scrollToBottom } = useConversation()

  // Auto-scroll on new content (when at bottom)
  const childCount = React.Children.count(children)
  const prevChildCount = React.useRef(childCount)

  React.useEffect(() => {
    // Auto-scroll when new messages are added
    if (childCount > prevChildCount.current) {
      scrollToBottom()
    }
    prevChildCount.current = childCount
  }, [childCount, scrollToBottom])

  return (
    <div
      ref={contentRef}
      className={`conversation-content flex-1 overflow-y-auto p-4 space-y-4 ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}

// === ConversationEmptyState ===

interface ConversationEmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  icon?: React.ReactNode
  title?: string
  description?: string
  children?: React.ReactNode
}

export function ConversationEmptyState({
  icon,
  title = 'No messages yet',
  description = 'Start a conversation to see messages here',
  children,
  className = '',
  ...props
}: ConversationEmptyStateProps) {
  return (
    <div
      className={`conversation-empty-state flex flex-col items-center justify-center h-full text-center p-8 ${className}`}
      {...props}
    >
      {icon && <div className="mb-4 text-gray-400">{icon}</div>}
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-500 max-w-sm">{description}</p>
      {children && <div className="mt-4">{children}</div>}
    </div>
  )
}

// === ConversationScrollButton ===

interface ConversationScrollButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children?: React.ReactNode
}

export function ConversationScrollButton({
  children,
  className = '',
  ...props
}: ConversationScrollButtonProps) {
  const { scrollToBottom, isAtBottom } = useConversation()

  if (isAtBottom) return null

  return (
    <button
      type="button"
      onClick={scrollToBottom}
      className={`conversation-scroll-button absolute bottom-20 left-1/2 -translate-x-1/2 bg-white border border-gray-200 rounded-full p-2 shadow-md hover:shadow-lg transition-shadow ${className}`}
      aria-label="Scroll to bottom"
      {...props}
    >
      {children || (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M12 5v14" />
          <path d="m19 12-7 7-7-7" />
        </svg>
      )}
    </button>
  )
}
