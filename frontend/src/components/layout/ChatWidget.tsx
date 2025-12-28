/**
 * ChatWidget Component
 *
 * A persistent floating chat widget that provides access to the booking agent
 * from any page. Uses the same ai-elements components as the main chat interface.
 *
 * Features:
 * - Floating button that opens a slide-up chat panel
 * - Hidden on home page (where chat is the main interface)
 * - Maintains conversation state while navigating
 * - Accessible with keyboard navigation
 */

'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import { usePathname } from 'next/navigation'
import { useChat } from '@ai-sdk/react'
import { DefaultChatTransport } from 'ai'
import {
  Conversation,
  ConversationContent,
  ConversationEmptyState,
  Message,
  MessageContent,
  MessageResponse,
  MessageLoading,
  Input,
  PromptInputTextarea,
  PromptInputSubmit,
  PromptInputWrapper,
} from '@/components/ai-elements'

// === Icons ===

function ChatIcon({ className = '' }: { className?: string }) {
  return (
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
      className={className}
    >
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  )
}

function CloseIcon({ className = '' }: { className?: string }) {
  return (
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
      className={className}
    >
      <path d="M18 6 6 18" />
      <path d="m6 6 12 12" />
    </svg>
  )
}

function SunIcon({ className = '' }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="32"
      height="32"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2" />
      <path d="M12 20v2" />
      <path d="m4.93 4.93 1.41 1.41" />
      <path d="m17.66 17.66 1.41 1.41" />
      <path d="M2 12h2" />
      <path d="M20 12h2" />
      <path d="m6.34 17.66-1.41 1.41" />
      <path d="m19.07 4.93-1.41 1.41" />
    </svg>
  )
}

// === ChatWidget Component ===

export function ChatWidget() {
  const pathname = usePathname()
  const [isOpen, setIsOpen] = useState(false)
  const [input, setInput] = useState('')
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // AI SDK v6 useChat hook - must be called before any conditional returns
  const { messages, status, error, sendMessage } = useChat({
    transport: new DefaultChatTransport({
      api: '/api/chat',
    }),
  })

  const isLoading = status === 'streaming' || status === 'submitted'

  // Handle form submission
  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault()
      if (!input.trim() || isLoading) return

      sendMessage({ text: input })
      setInput('')
      inputRef.current?.focus()
    },
    [input, isLoading, sendMessage]
  )

  // Handle input change
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
  }, [])

  // Extract text from message parts (v6 format)
  const getMessageText = (message: (typeof messages)[0]): string => {
    if ('parts' in message && Array.isArray(message.parts)) {
      return message.parts
        .filter((part): part is { type: 'text'; text: string } => part.type === 'text')
        .map((part) => part.text)
        .join('')
    }
    if ('content' in message && typeof message.content === 'string') {
      return message.content
    }
    return ''
  }

  // Focus input when panel opens
  useEffect(() => {
    if (!isOpen || !inputRef.current) return
    // Small delay to ensure panel is visible before focusing
    const timer = setTimeout(() => inputRef.current?.focus(), 100)
    return () => clearTimeout(timer)
  }, [isOpen])

  // Handle escape key to close
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false)
      }
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen])

  // Don't render on home page where chat is the main interface
  // This conditional return MUST come after all hooks
  if (pathname === '/') {
    return null
  }

  return (
    <>
      {/* Floating Chat Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="chat-widget-button"
        aria-label={isOpen ? 'Close chat' : 'Open chat'}
        aria-expanded={isOpen}
      >
        {isOpen ? <CloseIcon /> : <ChatIcon />}
        {/* Unread indicator when closed with messages */}
        {!isOpen && messages.length > 0 && <span className="chat-widget-badge" />}
      </button>

      {/* Chat Panel */}
      {isOpen && (
        <div className="chat-widget-panel" role="dialog" aria-label="Chat with booking assistant">
          {/* Panel Header */}
          <div className="chat-widget-header">
            <h2>Chat with us</h2>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="chat-widget-close"
              aria-label="Close chat"
            >
              <CloseIcon />
            </button>
          </div>

          {/* Chat Content */}
          <Conversation className="chat-widget-conversation">
            <ConversationContent className="chat-widget-messages">
              {messages.length === 0 ? (
                <ConversationEmptyState
                  icon={<SunIcon className="text-yellow-500" />}
                  title="Hi there!"
                  description="Ask me about availability, pricing, or the property."
                />
              ) : (
                <>
                  {messages.map((message) => (
                    <Message key={message.id} from={message.role as 'user' | 'assistant'}>
                      <MessageContent>
                        {message.role === 'assistant' ? (
                          <MessageResponse>{getMessageText(message)}</MessageResponse>
                        ) : (
                          <span className="whitespace-pre-wrap">{getMessageText(message)}</span>
                        )}
                      </MessageContent>
                    </Message>
                  ))}

                  {/* Loading indicator */}
                  {isLoading && messages[messages.length - 1]?.role === 'user' && (
                    <Message from="assistant">
                      <MessageContent>
                        <MessageLoading />
                      </MessageContent>
                    </Message>
                  )}
                </>
              )}
            </ConversationContent>
          </Conversation>

          {/* Error Display */}
          {error && (
            <div className="chat-widget-error">
              <p>Error: {error.message}</p>
            </div>
          )}

          {/* Input Area */}
          <div className="chat-widget-input">
            <Input onSubmit={handleSubmit}>
              <PromptInputWrapper>
                <PromptInputTextarea
                  ref={inputRef}
                  value={input}
                  onChange={handleInputChange}
                  placeholder="Type a message..."
                  disabled={isLoading}
                />
                <PromptInputSubmit
                  status={isLoading ? 'streaming' : input.trim() ? 'ready' : 'disabled'}
                  disabled={!input.trim() || isLoading}
                />
              </PromptInputWrapper>
            </Input>
          </div>
        </div>
      )}

      <style jsx>{`
        .chat-widget-button {
          position: fixed;
          bottom: 1.5rem;
          right: 1.5rem;
          width: 56px;
          height: 56px;
          border-radius: 50%;
          background: var(--color-primary);
          color: white;
          border: none;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 4px 12px rgba(29, 78, 216, 0.4);
          z-index: 1000;
          transition: transform 0.2s, box-shadow 0.2s;
        }

        .chat-widget-button:hover {
          transform: scale(1.05);
          box-shadow: 0 6px 16px rgba(29, 78, 216, 0.5);
        }

        .chat-widget-button:focus-visible {
          outline: 3px solid rgba(29, 78, 216, 0.5);
          outline-offset: 2px;
        }

        .chat-widget-badge {
          position: absolute;
          top: -2px;
          right: -2px;
          width: 12px;
          height: 12px;
          background: #10b981;
          border: 2px solid white;
          border-radius: 50%;
        }

        .chat-widget-panel {
          position: fixed;
          bottom: 6rem;
          right: 1.5rem;
          width: 380px;
          max-width: calc(100vw - 2rem);
          height: 500px;
          max-height: calc(100vh - 8rem);
          background: white;
          border-radius: 16px;
          box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
          display: flex;
          flex-direction: column;
          z-index: 999;
          overflow: hidden;
          animation: slideUp 0.3s ease-out;
        }

        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .chat-widget-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 1rem 1rem 1rem 1.25rem;
          background: var(--color-primary);
          color: white;
        }

        .chat-widget-header h2 {
          margin: 0;
          font-size: 1rem;
          font-weight: 600;
        }

        .chat-widget-close {
          background: transparent;
          border: none;
          color: white;
          cursor: pointer;
          padding: 0.25rem;
          border-radius: 4px;
          display: flex;
          align-items: center;
          justify-content: center;
          opacity: 0.8;
          transition: opacity 0.2s;
        }

        .chat-widget-close:hover {
          opacity: 1;
        }

        .chat-widget-error {
          padding: 0.5rem 1rem;
          background: #fef2f2;
          border-top: 1px solid #fecaca;
        }

        .chat-widget-error p {
          margin: 0;
          font-size: 0.75rem;
          color: #dc2626;
        }

        .chat-widget-input {
          padding: 0.75rem;
          border-top: 1px solid var(--border-color);
          background: white;
        }

        /* Mobile adjustments */
        @media (max-width: 480px) {
          .chat-widget-panel {
            right: 0;
            bottom: 0;
            width: 100%;
            max-width: 100%;
            height: 100%;
            max-height: 100%;
            border-radius: 0;
          }

          .chat-widget-button {
            bottom: 1rem;
            right: 1rem;
          }
        }
      `}</style>
    </>
  )
}

export default ChatWidget
