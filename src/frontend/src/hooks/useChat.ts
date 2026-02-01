/**
 * チャットフック
 *
 * AIエージェントとの会話を管理します。
 * セッション管理フックと連携して動作します。
 */
import { useState, useCallback, useEffect } from 'react'
import { sendChatMessage } from '../services/api'
import type { ChatSession } from './useSessions'

/** メッセージの型 */
export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
}

/** useChat のオプション型 */
interface UseChatOptions {
  activeSession: ChatSession | null
  onMessagesUpdate: (sessionId: string, messages: Message[], threadId: string | null) => void
}

/**
 * ユニークなIDを生成
 * crypto.randomUUID()を使用して衝突のないIDを生成
 * Date.now()はミリ秒単位のため、高速な連続呼び出しで衝突する可能性がある
 */
function generateUniqueId(): string {
  return crypto.randomUUID()
}

export function useChat(options?: UseChatOptions) {
  const { activeSession, onMessagesUpdate } = options || {}

  const [messages, setMessages] = useState<Message[]>(activeSession?.messages || [])
  const [threadId, setThreadId] = useState<string | null>(activeSession?.threadId || null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // アクティブセッションが変更されたらメッセージを復元
  useEffect(() => {
    if (activeSession) {
      setMessages(activeSession.messages)
      setThreadId(activeSession.threadId)
      setError(null)
    }
  }, [activeSession?.id])

  // メッセージを送信
  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return

    setError(null)
    setIsLoading(true)

    // ユーザーメッセージを追加
    const userMessage: Message = {
      id: generateUniqueId(),
      role: 'user',
      content,
    }

    const updatedMessagesWithUser = [...messages, userMessage]
    setMessages(updatedMessagesWithUser)

    try {
      // 同期でレスポンスを取得
      const { response, threadId: newThreadId } = await sendChatMessage(content, threadId)

      // アシスタントメッセージを追加
      const assistantMessage: Message = {
        id: generateUniqueId(),
        role: 'assistant',
        content: response,
      }

      const finalMessages = [...updatedMessagesWithUser, assistantMessage]
      setMessages(finalMessages)
      setThreadId(newThreadId)

      // セッションにメッセージを保存
      if (activeSession && onMessagesUpdate) {
        onMessagesUpdate(activeSession.id, finalMessages, newThreadId)
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'エラーが発生しました'
      setError(errorMessage)

      // セッションにはユーザーメッセージまで保存
      if (activeSession && onMessagesUpdate) {
        onMessagesUpdate(activeSession.id, updatedMessagesWithUser, threadId)
      }
    } finally {
      setIsLoading(false)
    }
  }, [threadId, isLoading, messages, activeSession, onMessagesUpdate])

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    threadId,
  }
}
