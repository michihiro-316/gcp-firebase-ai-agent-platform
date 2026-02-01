/**
 * Firebase初期化
 *
 * 【設定方法】
 * .envファイルに以下の環境変数を設定してください:
 * - VITE_FIREBASE_API_KEY
 * - VITE_FIREBASE_AUTH_DOMAIN
 * - VITE_FIREBASE_PROJECT_ID
 */
import { initializeApp } from 'firebase/app'
import { getAuth, GoogleAuthProvider } from 'firebase/auth'

// Firebase設定（環境変数から取得）
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
}

// Firebase初期化
const app = initializeApp(firebaseConfig)

// 認証インスタンス
export const auth = getAuth(app)

// Googleログインプロバイダ
export const googleProvider = new GoogleAuthProvider()
