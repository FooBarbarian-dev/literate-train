import { useState, useRef, useEffect, useCallback } from 'react'
import client from '../api/client'

const SUGGESTIONS = [
  'What MITRE techniques are commonly used in ransomware attacks?',
  'Find CVEs with a CVSS score above 9.0 affecting Windows',
  'Summarize recent log activity across all operations',
]

export default function ChatPage() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [threadId, setThreadId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Auto-grow the textarea
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px'
  }, [input])

  const send = useCallback(async () => {
    const text = input.trim()
    if (!text || loading) return

    setInput('')
    setError('')
    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setLoading(true)

    try {
      const { data } = await client.post('/chat/', {
        message: text,
        thread_id: threadId,
      }, { timeout: 150000 })
      setThreadId(data.thread_id)
      setMessages((prev) => [...prev, { role: 'assistant', content: data.reply }])
    } catch (err) {
      const msg =
        err.response?.data?.error ||
        'Failed to get a response. Check that the LLM service is running.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }, [input, loading, threadId])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  const newThread = () => {
    setMessages([])
    setThreadId(null)
    setError('')
    textareaRef.current?.focus()
  }

  return (
    <div className="chat-page">
      <div className="chat-header">
        <div>
          <h1>Threat Intel Assistant</h1>
          <p className="chat-header-sub">
            Ask about MITRE ATT&amp;CK techniques, CVEs, and your operation data
          </p>
        </div>
        {messages.length > 0 && (
          <button className="btn btn-ghost btn-sm" onClick={newThread}>
            New Conversation
          </button>
        )}
      </div>

      <div className="chat-body">
        {messages.length === 0 ? (
          <div className="chat-empty">
            <div className="chat-empty-icon">&#x1F6E1;</div>
            <p>
              Ask about CVEs, MITRE ATT&amp;CK techniques, or your logged
              operations.
            </p>
            <div className="chat-suggestions">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  className="chat-suggestion"
                  onClick={() => setInput(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="chat-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-bubble chat-bubble-${msg.role}`}>
                <div className="chat-bubble-label">
                  {msg.role === 'user' ? 'You' : 'Assistant'}
                </div>
                <div className="chat-bubble-content">{msg.content}</div>
              </div>
            ))}
            {loading && (
              <div className="chat-bubble chat-bubble-assistant">
                <div className="chat-bubble-label">Assistant</div>
                <div className="chat-thinking">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {error && <div className="alert alert-error chat-alert">{error}</div>}

      <div className="chat-input-bar">
        <textarea
          ref={textareaRef}
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about CVEs, ATT&CK techniques, or your operation logs… (Enter to send, Shift+Enter for newline)"
          rows={1}
          disabled={loading}
        />
        <button
          className="btn btn-primary"
          onClick={send}
          disabled={loading || !input.trim()}
        >
          Send
        </button>
      </div>
    </div>
  )
}
