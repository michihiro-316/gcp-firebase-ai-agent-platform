/**
 * API通信モジュール
 *
 * バックエンドAPIとの通信を行います。
 */
import { auth } from './firebase'

// APIベースURL（環境変数から取得）
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080'

/**
 * 認証トークンを取得
 */
async function getAuthToken(): Promise<string> {
  const user = auth.currentUser
  if (!user) {
    throw new Error('ログインが必要です')
  }
  return user.getIdToken()
}

/**
 * 認証ヘッダーを生成
 */
async function createAuthHeaders(): Promise<HeadersInit> {
  const token = await getAuthToken()
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  }
}

/**
 * チャットメッセージを送信（ストリーミング）
 *
 * @param message ユーザーのメッセージ
 * @param threadId スレッドID（省略可）
 * @param onChunk チャンク受信時のコールバック
 * @returns スレッドID
 */
export async function sendChatMessage(
  message: string,
  threadId: string | null,
  onChunk: (chunk: string) => void
): Promise<string> {
  const headers = await createAuthHeaders()

  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      message,
      thread_id: threadId,
    }),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.error || 'エラーが発生しました')
  }

  // レスポンスヘッダーからスレッドIDを取得
  const newThreadId = response.headers.get('X-Thread-Id') || threadId || ''

  // Server-Sent Eventsを処理
  const reader = response.body?.getReader()
  // stream: true を指定することで、マルチバイト文字（日本語など）が
  // チャンクの境界で分断された場合でも正しくデコードされる
  const decoder = new TextDecoder()

  if (!reader) {
    throw new Error('レスポンスの読み取りに失敗しました')
  }

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    // stream: true で不完全なマルチバイトシーケンスをバッファリング
    const text = decoder.decode(value, { stream: true })
    const lines = text.split('\n')

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6)
        if (data === '[DONE]') {
          break
        }
        if (data.startsWith('[ERROR]')) {
          throw new Error(data.slice(8))
        }
        onChunk(data)
      }
    }
  }

  return newThreadId
}
