/**
 * ╔══════════════════════════════════════════════════════════════════════════════╗
 * ║  App.tsx - フロントエンドのメインコンポーネント                                ║
 * ╠══════════════════════════════════════════════════════════════════════════════╣
 * ║                                                                              ║
 * ║  🎯 役割:                                                                    ║
 * ║     アプリ全体の状態管理と画面の切り替えを担当する「親コンポーネント」          ║
 * ║     - 未ログイン → LoginScreen を表示                                        ║
 * ║     - ログイン済 → ChatScreen を表示                                         ║
 * ║                                                                              ║
 * ║  📁 構成:                                                                    ║
 * ║     App.tsx（このファイル）                                                   ║
 * ║       ├── LoginScreen.tsx  : ログイン画面                                    ║
 * ║       └── ChatScreen.tsx   : チャット画面                                    ║
 * ║                                                                              ║
 * ║  🔧 カスタムフック（状態管理）:                                               ║
 * ║     - useAuth     : 認証状態（ログイン/ログアウト）                           ║
 * ║     - useChat     : チャット送受信                                      　　     ║
 * ║     - useSessions : 複数セッション管理                                   　　    ║
 * ║                                                                              ║
 * ║  📚 詳細: learning/md/03_フロントエンド解説.md                            　　    ║
 * ║                                                                              ║
 * ║  ⚠️  通常このファイルを編集する必要はありません                              　　　　 ║
 * ║      UIのカスタマイズは ChatScreen.tsx や styles.css で行ってください     　　   　 ║
 * ║                                                                              ║
 * ╚══════════════════════════════════════════════════════════════════════════════╝
 */
import { ChatScreen } from './components/ChatScreen'
import { LoginScreen } from './components/LoginScreen'
import { useAuth } from './hooks/useAuth'
import { useChat } from './hooks/useChat'
import { useSessions } from './hooks/useSessions'

/**
 * デバッグモード: 開発環境でのみ有効
 * - true: 認証をスキップしてチャット画面を表示（画面確認用）
 * - false: 通常の認証フローを使用
 *
 * 本番ビルド（npm run build）では自動的に false になります
 */
const DEBUG_SHOW_CHAT = import.meta.env.DEV && import.meta.env.VITE_DEBUG_MODE === 'true' ? true : false

function App() {
  const { user, loading, error: authError, loginWithGoogle, logout } = useAuth()

  // セッション管理（詳細は useSessions.ts のコメント参照）
  const {
    sessions,
    activeSession,
    activeSessionId,
    createSession,
    switchSession,
    closeSession,
    updateSessionMessages,
  } = useSessions()

  // チャット状態管理（セッションと連携）
  const { messages, isLoading, error: chatError, sendMessage } = useChat({
    activeSession,
    onMessagesUpdate: updateSessionMessages,
  })

  // ローディング中（認証状態の確認中）
  if (loading && !DEBUG_SHOW_CHAT) {
    return (
      <div className="loading-screen">
        <div className="spinner" />
        <p>読み込み中...</p>
      </div>
    )
  }

  // 未ログイン → ログイン画面を表示
  if (!user && !DEBUG_SHOW_CHAT) {
    return <LoginScreen onLogin={loginWithGoogle} error={authError} />
  }

  // ログイン済み（またはデバッグモード）→ チャット画面を表示
  // デバッグモード時はダミーユーザーを使用
  const displayUser = user || { email: 'demo@example.com', displayName: 'Demo User' }

  return (
    <ChatScreen
      user={displayUser}
      messages={messages}
      isLoading={isLoading}
      error={chatError}
      onSendMessage={sendMessage}
      onLogout={logout}
      sessions={sessions}
      activeSessionId={activeSessionId}
      onSelectSession={switchSession}
      onNewSession={createSession}
      onCloseSession={closeSession}
    />
  )
}

export default App
