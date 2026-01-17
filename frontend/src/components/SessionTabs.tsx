/**
 * セッションタブコンポーネント
 *
 * 複数のチャットセッションをタブ形式で表示・切り替えできるコンポーネント
 *
 * 【機能】
 * - タブクリックでセッション切り替え
 * - 「×」ボタンでセッション削除（確認ダイアログあり）
 * - 「+」ボタンで新規セッション作成
 *
 * 【注意】
 * - セッションが1つの場合は削除ボタンを非表示（最低1つは必要）
 * - 削除は復元できないため、確認ダイアログを表示
 */
import type { ChatSession } from '../hooks/useSessions'

interface SessionTabsProps {
  sessions: ChatSession[]
  activeSessionId: string
  onSelectSession: (id: string) => void
  onNewSession: () => void
  onCloseSession: (id: string) => void
}

export function SessionTabs({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  onCloseSession,
}: SessionTabsProps) {
  /**
   * セッション削除ハンドラー
   * - stopPropagation: 親要素（タブ）のクリックイベントが発火しないようにする
   * - 確認ダイアログで誤削除を防止
   */
  const handleClose = (e: React.MouseEvent, session: ChatSession) => {
    e.stopPropagation()

    // 削除確認ダイアログ
    const confirmed = window.confirm(
      `「${session.title}」を削除しますか？\n削除後は復元できません。`
    )
    if (confirmed) {
      onCloseSession(session.id)
    }
  }

  return (
    <div className="session-tabs" role="tablist" aria-label="チャットセッション">
      <div className="tabs-container">
        {sessions.map((session) => {
          const isActive = session.id === activeSessionId

          return (
            <button
              key={session.id}
              role="tab"
              aria-selected={isActive}
              aria-controls={`session-panel-${session.id}`}
              className={`tab ${isActive ? 'active' : ''}`}
              onClick={() => onSelectSession(session.id)}
            >
              <span className="tab-title">{session.title}</span>
              {/* セッションが1つの場合は削除ボタンを非表示 */}
              {sessions.length > 1 && (
                <span
                  role="button"
                  className="tab-close"
                  onClick={(e) => handleClose(e, session)}
                  aria-label={`「${session.title}」を閉じる`}
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      handleClose(e as unknown as React.MouseEvent, session)
                    }
                  }}
                >
                  ×
                </span>
              )}
            </button>
          )
        })}
        <button
          className="new-tab-button"
          onClick={onNewSession}
          aria-label="新しい会話を作成"
        >
          +
        </button>
      </div>
    </div>
  )
}
