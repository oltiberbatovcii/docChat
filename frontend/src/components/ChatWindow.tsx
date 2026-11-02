import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { sendChat } from '../api/client'
import type { Message } from '../types'
import { MessageBubble } from './MessageBubble'

export function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([])
  const [question, setQuestion] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const text = question.trim()
    if (!text || isLoading) return

    setMessages((previous) => [...previous, { role: 'user', text }])
    setQuestion('')
    setIsLoading(true)
    setError(null)
    try {
      const { answer, sources } = await sendChat(text)
      setMessages((previous) => [...previous, { role: 'assistant', text: answer, sources }])
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <section className="chat" aria-label="Chat">
      <div className="messages" aria-live="polite">
        {messages.length === 0 && !isLoading && (
          <p className="hint">Upload a document (PDF, Word, Markdown or text), then ask a question about it.</p>
        )}
        {messages.map((message, index) => (
          <MessageBubble key={index} message={message} />
        ))}
        {isLoading && <p className="hint">Thinking… the first answer can take a few minutes.</p>}
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <div ref={bottomRef} />
      </div>

      <form className="composer" onSubmit={handleSubmit}>
        <input
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask about your documents…"
          aria-label="Your question"
          maxLength={1000}
        />
        <button className="button" type="submit" disabled={isLoading || !question.trim()}>
          Send
        </button>
      </form>
    </section>
  )
}
