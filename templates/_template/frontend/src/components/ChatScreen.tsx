/**
 * チャット画面コンポーネント
 */
import { useState, useRef, useEffect } from 'react'
import { Message } from '../hooks/useChat'
import type { ChatSession } from '../hooks/useSessions'
import { SessionTabs } from './SessionTabs'
import { useRenderer } from '../hooks/useRenderer'
import { getMessageRenderer } from '../renderers'

interface User {
  email: string | null
  displayName: string | null
}

interface ChatScreenProps {
  user: User
  messages: Message[]
  isLoading: boolean
  error: string | null
  onSendMessage: (message: string) => void
  onLogout: () => void
  // セッション関連
  sessions: ChatSession[]
  activeSessionId: string
  onSelectSession: (id: string) => void
  onNewSession: () => void
  onCloseSession: (id: string) => void
  // 顧客ID（レンダラー選択用）
  customerId?: string
}

export function ChatScreen({
  user,
  messages,
  isLoading,
  error,
  onSendMessage,
  onLogout,
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  onCloseSession,
  customerId,
}: ChatScreenProps) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // レンダラー設定と顧客別レンダラーを取得
  const { config, customerId: configCustomerId } = useRenderer()
  // props の customerId を優先、なければ config から取得
  const effectiveCustomerId = customerId ?? configCustomerId
  const MessageRenderer = getMessageRenderer(effectiveCustomerId)

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
          <button className="header-button" onClick={onLogout}>
            ログアウト
          </button>
        </div>
      </header>

      {/* セッションタブ */}
      <SessionTabs
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={onSelectSession}
        onNewSession={onNewSession}
        onCloseSession={onCloseSession}
      />

      {/* メッセージ一覧 */}
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="empty-state">
            <p>メッセージを入力して会話を始めましょう</p>
          </div>
        ) : (
          messages.map((msg) => (
            <MessageRenderer key={msg.id} message={msg} config={config} />
          ))
        )}

        {/* 待機中UI（アクセシビリティ対応） */}
        {isLoading && (
          <div className="thinking-indicator" role="status" aria-label="AIが考え中です">
            <div className="thinking-dots" aria-hidden="true">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <p>AIが考え中...</p>
          </div>
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
