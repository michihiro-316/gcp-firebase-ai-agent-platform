/**
 * メインアプリケーション
 *
 * 認証状態に応じてログイン画面またはチャット画面を表示します。
 */
import { useAuth } from './hooks/useAuth'
import { useChat } from './hooks/useChat'
import { LoginScreen } from './components/LoginScreen'
import { ChatScreen } from './components/ChatScreen'

function App() {
  const { user, loading, error: authError, loginWithGoogle, logout } = useAuth()
  const { messages, isLoading, error: chatError, sendMessage, resetChat } = useChat()

  // ローディング中
  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner" />
        <p>読み込み中...</p>
      </div>
    )
  }

  // 未ログイン
  if (!user) {
    return <LoginScreen onLogin={loginWithGoogle} error={authError} />
  }

  // ログイン済み
  return (
    <ChatScreen
      user={user}
      messages={messages}
      isLoading={isLoading}
      error={chatError}
      onSendMessage={sendMessage}
      onResetChat={resetChat}
      onLogout={logout}
    />
  )
}

export default App
