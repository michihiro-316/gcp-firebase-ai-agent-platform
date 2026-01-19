/**
 * セッション管理フック
 *
 * 複数のチャットセッションを管理し、ローカルストレージに永続化します。
 *
 * 【主な機能】
 * - セッションの作成・切り替え・削除
 * - ローカルストレージへの自動保存
 * - 最初のメッセージからタイトル自動生成
 *
 * 【制限事項】
 * - 最大10セッションまで保存（容量制限のため）
 * - ブラウザのローカルストレージに保存（デバイス間同期なし）
 * - ストレージクリア時にデータが消失
 *
 * 【使用例】
 * const { sessions, activeSession, createSession, switchSession } = useSessions()
 */
import { useState, useCallback, useEffect } from 'react'
import type { Message } from './useChat'

/** ローカルストレージのキー */
const STORAGE_KEY = 'chat_sessions'

/**
 * 最大セッション数
 * - ローカルストレージの容量制限（5-10MB）を考慮
 * - 1セッション約8KB（20メッセージ想定）× 10 = 約80KB
 */
const MAX_SESSIONS = 10

/** デフォルトのセッションタイトル */
const DEFAULT_SESSION_TITLE = '新しい会話'

/**
 * チャットセッションの型定義
 */
export interface ChatSession {
  /** 一意のセッションID */
  id: string
  /** セッションのタイトル（最初のメッセージから自動生成） */
  title: string
  /** このセッションのメッセージ履歴 */
  messages: Message[]
  /** バックエンドとの会話スレッドID */
  threadId: string | null
  /** 作成日時（Unix timestamp） */
  createdAt: number
  /** 最終更新日時（Unix timestamp） */
  updatedAt: number
}

/**
 * セッションIDを生成
 * 形式: session_{timestamp}_{ランダム文字列}
 */
function generateSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

/**
 * 新しい空のセッションを作成
 */
function createNewSession(): ChatSession {
  return {
    id: generateSessionId(),
    title: DEFAULT_SESSION_TITLE,
    messages: [],
    threadId: null,
    createdAt: Date.now(),
    updatedAt: Date.now(),
  }
}

/**
 * ローカルストレージからセッション一覧を読み込み
 * エラー時は空配列を返す（データ破損時の安全対策）
 */
function loadSessionsFromStorage(): ChatSession[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch {
    // ストレージ読み込みエラーは握りつぶす（起動を妨げないため）
  }
  return []
}

/**
 * セッション一覧をローカルストレージに保存
 */
function saveSessionsToStorage(sessions: ChatSession[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions))
  } catch {
    // ストレージ書き込みエラーは握りつぶす（容量超過など）
  }
}

/**
 * メッセージ内容からタイトルを生成
 * - 最大20文字まで
 * - 改行はスペースに変換
 */
function generateTitleFromMessage(content: string): string {
  const maxLength = 20
  const trimmed = content.trim().replace(/\n/g, ' ')
  if (trimmed.length <= maxLength) {
    return trimmed
  }
  return trimmed.substring(0, maxLength) + '...'
}

/**
 * セッション管理フック
 */
export function useSessions() {
  /**
   * セッション一覧
   * - useState の初期化関数（() => ...）を使用
   * - 初期化関数は初回レンダリング時に1回だけ実行される
   * - これにより毎レンダリング時のストレージ読み込みを防止
   */
  const [sessions, setSessions] = useState<ChatSession[]>(() => {
    const loaded = loadSessionsFromStorage()
    // セッションがない場合は新規作成
    return loaded.length === 0 ? [createNewSession()] : loaded
  })

  /**
   * アクティブなセッションのID
   * - 最初のセッション（最新）をデフォルトで選択
   */
  const [activeSessionId, setActiveSessionId] = useState<string>(
    () => sessions[0]?.id || ''
  )

  /**
   * セッション変更時に自動保存
   * - sessionsが変更されるたびにローカルストレージを更新
   */
  useEffect(() => {
    saveSessionsToStorage(sessions)
  }, [sessions])

  /**
   * 現在アクティブなセッションを取得
   * - 見つからない場合は最初のセッションを返す（安全対策）
   */
  const activeSession = sessions.find(s => s.id === activeSessionId) || sessions[0]

  /**
   * 新しいセッションを作成
   * - 最大数を超えたら古いものを自動削除
   */
  const createSession = useCallback(() => {
    const newSession = createNewSession()
    setSessions(prev => {
      const updated = [newSession, ...prev]
      // 最大数を超えたら古いものを削除（末尾から）
      if (updated.length > MAX_SESSIONS) {
        return updated.slice(0, MAX_SESSIONS)
      }
      return updated
    })
    setActiveSessionId(newSession.id)
    return newSession.id
  }, [])

  /**
   * セッションを切り替え
   */
  const switchSession = useCallback((sessionId: string) => {
    setActiveSessionId(sessionId)
  }, [])

  /**
   * セッションを削除
   * - 全て削除された場合は新しいセッションを自動作成
   * - アクティブセッションが削除された場合は隣のセッションを選択
   */
  const closeSession = useCallback((sessionId: string) => {
    setSessions(prev => {
      // 削除対象以外のセッションを抽出
      const remainingSessions = prev.filter(s => s.id !== sessionId)

      // 全て削除された場合は新しいセッションを作成
      if (remainingSessions.length === 0) {
        const newSession = createNewSession()
        setActiveSessionId(newSession.id)
        return [newSession]
      }

      // 削除されたのがアクティブセッションだった場合、次のセッションを選択
      if (sessionId === activeSessionId) {
        // 削除前のインデックスを取得
        const deletedIndex = prev.findIndex(s => s.id === sessionId)
        // 同じ位置か、末尾の場合は1つ前を選択
        const nextIndex = Math.min(deletedIndex, remainingSessions.length - 1)
        setActiveSessionId(remainingSessions[nextIndex].id)
      }

      return remainingSessions
    })
  }, [activeSessionId])

  /**
   * セッションのメッセージを更新
   * - useChat から呼ばれる
   * - タイトルが「新しい会話」の場合、最初のユーザーメッセージから自動生成
   */
  const updateSessionMessages = useCallback((
    sessionId: string,
    messages: Message[],
    threadId: string | null
  ) => {
    setSessions(prev => prev.map(session => {
      if (session.id !== sessionId) return session

      // タイトル自動生成（まだ「新しい会話」の場合のみ）
      let title = session.title
      if (title === DEFAULT_SESSION_TITLE && messages.length > 0) {
        const firstUserMessage = messages.find(m => m.role === 'user')
        if (firstUserMessage) {
          title = generateTitleFromMessage(firstUserMessage.content)
        }
      }

      return {
        ...session,
        messages,
        threadId,
        title,
        updatedAt: Date.now(),
      }
    }))
  }, [])

  return {
    /** セッション一覧（新しい順） */
    sessions,
    /** 現在アクティブなセッション */
    activeSession,
    /** 現在アクティブなセッションのID */
    activeSessionId,
    /** 新しいセッションを作成 */
    createSession,
    /** セッションを切り替え */
    switchSession,
    /** セッションを削除 */
    closeSession,
    /** メッセージを更新（useChat連携用） */
    updateSessionMessages,
  }
}
