/**
 * チャット画面コンポーネント
 */
import { useState, useRef, useEffect } from 'react'
import { User } from 'firebase/auth'
import { Message } from '../hooks/useChat'

interface ChatScreenProps {
  user: User
  messages: Message[]
  isLoading: boolean
  error: string | null
  onSendMessage: (message: string) => void
  onResetChat: () => void
  onLogout: () => void
}

export function ChatScreen({
  user,
  messages,
  isLoading,
  error,
  onSendMessage,
  onResetChat,
  onLogout,
}: ChatScreenProps) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // メッセージが追加されたら自動スクロール
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // メッセージ送信
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && !isLoading) {
      onSendMessage(input)
      setInput('')
    }
  }

  return (
    <div className="chat-screen">
      {/* ヘッダー */}
      <header className="header">
        <h1>AIエージェント</h1>
        <div className="header-actions">
          <span className="user-email">{user.email}</span>
          <button className="header-button" onClick={onResetChat}>
            新しい会話
          </button>
          <button className="header-button" onClick={onLogout}>
            ログアウト
          </button>
        </div>
      </header>

      {/* メッセージ一覧 */}
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="empty-state">
            <p>メッセージを入力して会話を始めましょう</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className={`message ${msg.role}`}>
              <div className="message-content">
                {msg.content || (msg.role === 'assistant' && '...')}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* エラー表示 */}
      {error && (
        <div className="error-banner">
          {error}
        </div>
      )}

      {/* 入力フォーム */}
      <form className="input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="メッセージを入力..."
          disabled={isLoading}
          className="message-input"
        />
        <button
          type="submit"
          disabled={!input.trim() || isLoading}
          className="send-button"
        >
          {isLoading ? '送信中...' : '送信'}
        </button>
      </form>
    </div>
  )
}
