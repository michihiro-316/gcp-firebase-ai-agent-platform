/**
 * 認証フック
 *
 * Firebase Authenticationの状態を管理します。
 */
import { useState, useEffect } from 'react'
import { User, signInWithPopup, signOut, onAuthStateChanged } from 'firebase/auth'
import { auth, googleProvider } from '../services/firebase'

export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // 認証状態の監視
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setUser(user)
      setLoading(false)
    })
    return unsubscribe
  }, [])

  // Googleでログイン
  const loginWithGoogle = async () => {
    setError(null)
    try {
      await signInWithPopup(auth, googleProvider)
    } catch (err) {
      setError('ログインに失敗しました')
      console.error(err)
    }
  }

  // ログアウト
  const logout = async () => {
    try {
      await signOut(auth)
    } catch (err) {
      setError('ログアウトに失敗しました')
      console.error(err)
    }
  }

  return {
    user,
    loading,
    error,
    loginWithGoogle,
    logout,
    isLoggedIn: !!user,
  }
}
