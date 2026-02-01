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

/** sendChatMessage の戻り値型 */
export interface ChatResponse {
  response: string
  threadId: string
}

/**
 * チャットメッセージを送信
 *
 * @param message ユーザーのメッセージ
 * @param threadId スレッドID（省略可）
 * @returns レスポンスオブジェクト { response: string, threadId: string }
 */
export async function sendChatMessage(
  message: string,
  threadId: string | null
): Promise<ChatResponse> {
  const headers = await createAuthHeaders()

  const res = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      message,
      thread_id: threadId,
    }),
  })

  if (!res.ok) {
    const error = await res.json()
    throw new Error(error.error || 'エラーが発生しました')
  }

  const data = await res.json()

  // レスポンス構造の検証（APIの不正な応答を検出）
  if (!data?.data?.response || !data?.data?.thread_id) {
    throw new Error('サーバーから無効なレスポンスを受信しました')
  }

  return {
    response: data.data.response,
    threadId: data.data.thread_id,
  }
}
