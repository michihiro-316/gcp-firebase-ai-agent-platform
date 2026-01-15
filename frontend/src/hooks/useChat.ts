/**
 * チャットフック
 *
 * AIエージェントとの会話を管理します。
 */
import { useState, useCallback } from 'react'
import { sendChatMessage } from '../services/api'

/**
 * ユニークなIDを生成
 * crypto.randomUUID()を使用して衝突のないIDを生成
 * Date.now()はミリ秒単位のため、高速な連続呼び出しで衝突する可能性がある
 */
function generateUniqueId(): string {
  return crypto.randomUUID()
}

// メッセージの型
export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [threadId, setThreadId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

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
    setMessages(prev => [...prev, userMessage])

    // AIの応答用プレースホルダー
    const assistantMessageId = generateUniqueId()
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
    }
    setMessages(prev => [...prev, assistantMessage])

    try {
      // ストリーミングでメッセージを受信
      const newThreadId = await sendChatMessage(
        content,
        threadId,
        (chunk) => {
          // チャンクを受信するたびにメッセージを更新
          setMessages(prev =>
            prev.map(msg =>
              msg.id === assistantMessageId
                ? { ...msg, content: msg.content + chunk }
                : msg
            )
          )
        }
      )

      setThreadId(newThreadId)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'エラーが発生しました'
      setError(errorMessage)

      // エラー時は失敗したメッセージを削除
      setMessages(prev => prev.filter(msg => msg.id !== assistantMessageId))
    } finally {
      setIsLoading(false)
    }
  }, [threadId, isLoading])

  // 会話をリセット
  const resetChat = useCallback(() => {
    setMessages([])
    setThreadId(null)
    setError(null)
  }, [])

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    resetChat,
    threadId,
  }
}
