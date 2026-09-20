import { useEffect, useMemo, useState } from 'react'

const API_URL = 'http://localhost:8000/ask'

const starterMessages = [
  { role: 'assistant', content: 'Ask me anything about the project, RAG, or vector search.' },
]

export default function App() {
  const [question, setQuestion] = useState('What is an AI agent?')
  const [messages, setMessages] = useState(starterMessages)
  const [loading, setLoading] = useState(false)
  const [sessionId] = useState(() => `session-${Date.now()}`)
  const [location, setLocation] = useState(null)
  const [locationError, setLocationError] = useState('')

  useEffect(() => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation is not supported by this browser.')
      return
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        })
      },
      () => {
        setLocationError('Location permission denied. You can still ask for a city-based weather forecast.')
      },
      { enableHighAccuracy: true }
    )
  }, [])

  const askQuestion = async () => {
    if (!question.trim()) return

    const userMessage = { role: 'user', content: question }
    const assistantPlaceholder = { role: 'assistant', content: '' }
    const nextMessages = [...messages, userMessage, assistantPlaceholder]
    setMessages(nextMessages)
    setQuestion('')
    setLoading(true)

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question,
          session_id: sessionId,
          stream: true,
          latitude: location?.latitude ?? null,
          longitude: location?.longitude ?? null,
        }),
      })

      if (!response.body) {
        throw new Error('No response body')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let assistantIndex = nextMessages.length - 1

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const chunks = buffer.split(/(?<=\S)(?=\S)/)
        buffer = ''

        for (const piece of chunks) {
          if (!piece) continue
          setMessages((current) => {
            const updated = [...current]
            updated[assistantIndex] = {
              ...updated[assistantIndex],
              content: (updated[assistantIndex]?.content || '') + piece,
            }
            return updated
          })
        }
      }
    } catch (error) {
      setMessages((current) => [
        ...current,
        { role: 'assistant', content: 'Error connecting to the backend. Make sure the API is running on port 8000.' },
      ])
    } finally {
      setLoading(false)
    }
  }

  const recentMessages = useMemo(() => messages.slice(-8), [messages])

  return (
    <div className="app-shell">
      <aside className="history-panel">
        <h2>Chat history</h2>
        <ul>
          {recentMessages.map((message, index) => (
            <li key={`${message.role}-${index}`} className={message.role}>
              <strong>{message.role === 'user' ? 'You' : 'Agent'}:</strong> {message.content || '...'}
            </li>
          ))}
        </ul>
      </aside>

      <main className="chat-panel">
        <h1>Minimal AI Agent</h1>
        <p className="subtitle">RAG + memory + streaming + local model</p>

        {location && (
          <p className="subtitle">Using your current location for weather queries.</p>
        )}

        {locationError && <p className="subtitle error">{locationError}</p>}

        <div className="message-list">
          {messages.map((message, index) => (
            <div key={`${message.role}-${index}`} className={`message ${message.role}`}>
              <strong>{message.role === 'user' ? 'You' : 'Agent'}</strong>
              <p>{message.content || '...'}</p>
            </div>
          ))}
        </div>

        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          rows={5}
          placeholder="Ask your agent a question..."
        />

        <button onClick={askQuestion} disabled={loading}>
          {loading ? 'Thinking...' : 'Ask agent'}
        </button>
      </main>
    </div>
  )
}
