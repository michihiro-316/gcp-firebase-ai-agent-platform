# ログインの流れ - 完全解説

**このドキュメントの目的**：
「ログインボタンを押したら何が起きるか」を、**実際のコード**と**繋がり**を見ながら理解する。

**想定読者**: GASを少し触ったことがある新卒エンジニア

**読了時間**: 約30分

---

## まず知っておくべきこと

### なぜGoogleログインを使うの？

```
【方法1: 自分でパスワード管理】

  ユーザー → パスワード → 自分のサーバー
                           ↓
                    パスワードを保存
                           ↓
                    もしハッキングされたら...
                    全ユーザーのパスワードが漏洩！

【方法2: Googleに任せる（OAuth）】← 今回はこっち

  ユーザー → Googleアカウント → Google
                                  ↓
                           「この人は本物です」
                                  ↓
                           自分のサーバー

  ✅ パスワードを保存しなくてよい
  ✅ Googleのセキュリティに守られる
  ✅ 2段階認証も自動で使える
```

### Custom Claims（カスタムクレーム）とは？

```
【銀行の例えで説明】

身分証明書（IDトークン）:
┌─────────────────────────────────────┐
│  名前: 山田太郎                       │
│  生年月日: 1990/1/1                   │
│  住所: 東京都...                      │
│                                     │
│  【追加情報（Custom Claims）】         │
│  所属会社: 株式会社ACME                │  ← サーバーだけが書ける
│  社員番号: A001                       │  ← ユーザーは改ざんできない
└─────────────────────────────────────┘

この身分証があれば、
「株式会社ACMEの山田太郎さん」だと証明できる
```

---

## 全体フロー図

```
【ブラウザ】                          【外部サービス】

1. 「Googleでログイン」
   ボタンをクリック
        ↓
   ┌─────────────────┐
   │  useAuth.ts     │  ← 「ログイン係」
   │  loginWithGoogle()
   └────────┬────────┘
            ↓
   ┌─────────────────┐
   │  firebase.ts    │  ← 「Firebase接続係」
   │  signInWithPopup()
   └────────┬────────┘
            ↓
   ポップアップが開く ───────────────→ Google
            ↓                         ↓
   ユーザーがGoogleアカウントを選択   「この人は本物です」
            ↓                         ↓
   ┌─────────────────┐              ← 認証結果を受け取り
   │ Firebase Auth   │
   │ ユーザー作成/更新│
   └────────┬────────┘
            ↓
   ┌─────────────────┐
   │ onAuthStateChanged()  ← 「ログイン完了したよ！」
   │ 自動で呼ばれる    │      と通知してくれる
   └────────┬────────┘
            ↓
2. ログイン完了！
   チャット画面に切り替わる
```

---

## ステップ1: ログインボタンをクリック

### なぜこのファイルがあるのか？

**問題**: ログイン画面のボタンに直接ログイン処理を書くと...
- コードが長くなる
- 他の画面（設定画面など）で再利用できない
- テストしにくい

**解決**: ログイン処理を「フック（Hook）」として分離する

### 場所: `frontend/src/hooks/useAuth.ts`

```typescript
// useAuth.ts（簡略版）

export function useAuth() {
  // ====================================
  // 【このフックの役割】
  // 1. 「今ログインしてる？」を管理
  // 2. 「ログインする」機能を提供
  // 3. 「ログアウトする」機能を提供
  // ====================================

  // ★ 状態の定義
  const [user, setUser] = useState(null)      // ログイン中のユーザー
  const [loading, setLoading] = useState(true) // 読み込み中？

  // ★ ログイン状態の監視（ページを開いた時に1回だけ実行）
  useEffect(() => {
    // 「ログイン状態が変わったら教えて」と登録
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setUser(user)       // ユーザー情報を更新
      setLoading(false)   // 読み込み完了
    })

    return unsubscribe  // ページを離れる時に解除
  }, [])

  // ★ Googleでログイン
  const loginWithGoogle = async () => {
    try {
      await signInWithPopup(auth, googleProvider)
      // 成功すると onAuthStateChanged が自動で呼ばれる
      // → setUser(user) が実行される
      // → 画面が自動でチャット画面に切り替わる
    } catch (err) {
      console.error('ログイン失敗:', err)
    }
  }

  // ★ ログアウト
  const logout = async () => {
    await signOut(auth)
    // 成功すると onAuthStateChanged が自動で呼ばれる
    // → setUser(null) が実行される
    // → 画面が自動でログイン画面に切り替わる
  }

  return { user, loading, loginWithGoogle, logout }
}
```

### GAS経験者向け: useEffect とは？

```javascript
// GASの場合
function onOpen() {
  // スプレッドシートを開いた時に1回だけ実行
}

// Reactの場合
useEffect(() => {
  // コンポーネントが表示された時に1回だけ実行
}, [])  // ← この [] が「1回だけ」を意味する
```

---

## ステップ2: Firebase初期化

### なぜこのファイルがあるのか？

**問題**: Firebaseの設定を複数の場所で書くと...
- 同じコードが重複する
- 設定を変えたい時に全部直す必要がある

**解決**: Firebase初期化を1つのファイルにまとめる

### 場所: `frontend/src/services/firebase.ts`

```typescript
// firebase.ts

// ★ Firebase設定（環境変数から取得）
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
}

// ★ Firebase初期化（アプリ全体で1回だけ）
const app = initializeApp(firebaseConfig)

// ★ 認証機能を取得（他のファイルから使える）
export const auth = getAuth(app)

// ★ Googleログイン用の設定
export const googleProvider = new GoogleAuthProvider()
```

### 環境変数とは？

```
【問題】APIキーをコードに直接書くと...

const apiKey = "AIzaSyXXXXXXXXXX"  // ← GitHubに公開される！

【解決】.env ファイルに書く

# .env ファイル（GitHubにはアップしない）
VITE_FIREBASE_API_KEY=AIzaSyXXXXXXXXXX

# コードでは環境変数から読む
const apiKey = import.meta.env.VITE_FIREBASE_API_KEY
```

---

## ステップ3: ログイン処理の詳細

### signInWithPopup の動作

```
┌──────────────────────────────────────────────────────────────┐
│                    ログインの10ステップ                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. signInWithPopup() を呼ぶ                                 │
│         ↓                                                    │
│  2. 新しいウィンドウ（ポップアップ）が開く                      │
│         ↓                                                    │
│  3. Googleの「アカウントを選択」画面が表示                      │
│         ↓                                                    │
│  4. ユーザーがアカウントを選択                                 │
│         ↓                                                    │
│  5. Google: 「この人は本物です」                              │
│         ↓                                                    │
│  6. Firebase Auth にユーザー情報が保存                        │
│         ↓                                                    │
│  7. ポップアップが自動で閉じる                                 │
│         ↓                                                    │
│  8. onAuthStateChanged が自動で呼ばれる                       │
│         ↓                                                    │
│  9. setUser(user) で状態が更新                               │
│         ↓                                                    │
│  10. 画面がチャット画面に切り替わる                            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 認証状態の変化パターン

| シナリオ | 何が起きるか | 結果 |
|---------|------------|------|
| 初めてアクセス | onAuthStateChanged → user: null | ログイン画面 |
| ログインボタンクリック | signInWithPopup → onAuthStateChanged → user: {...} | チャット画面 |
| ページリロード | onAuthStateChanged → user: {...}（保存されていた） | チャット画面 |
| ログアウト | signOut → onAuthStateChanged → user: null | ログイン画面 |

---

## ステップ4: バックエンドでの認証検証

### なぜサーバー側でも検証が必要？

```
【問題】フロントエンドだけで認証すると...

悪意のあるユーザーが、
ブラウザの開発者ツールで
「ログイン済み」に偽装できてしまう！

【解決】サーバー側でも必ずトークンを検証する

フロントエンド: 「私は山田太郎です」
        ↓ IDトークンを送信
サーバー: 「本当に？Googleに確認するね」
        ↓ Firebase Admin SDK で検証
Google: 「本物の山田太郎さんです」
        ↓
サーバー: 「OK、処理を続けます」
```

### 場所: `backend/src/common/auth.py`

```python
# auth.py（簡略版）

def authenticate_request(request):
    """
    リクエストを認証する

    【4つの関門】
    1. トークンがあるか？
    2. トークンは本物か？
    3. このユーザーは許可されているか？
    4. どの会社に所属しているか？
    """

    # 関門1: トークンがあるか？
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise ValueError("認証トークンがありません")

    id_token = auth_header.split("Bearer ")[1]

    # 関門2: トークンは本物か？（Googleに確認）
    user_info = auth.verify_id_token(id_token)

    # 関門3: このユーザーは許可されているか？
    if not is_user_allowed(user_info["email"]):
        raise ValueError("アクセスが許可されていません")

    # 関門4: どの会社に所属しているか？
    user_info["customer_id"] = get_user_customer_id(user_info["uid"])

    return user_info  # 全部通過！


def get_user_customer_id(uid):
    """
    ユーザーの所属会社（顧客ID）を取得

    【Custom Claims から取得】
    - サーバー側でしか設定できない
    - ユーザーが改ざんできない
    - 「この人は株式会社ACMEの社員です」という情報
    """
    user = auth.get_user(uid)
    claims = user.custom_claims or {}
    customer_id = claims.get("customer_id")

    if not customer_id:
        # 会社に登録されていないユーザーは拒否！
        raise ValueError("顧客に紐付けされていません。管理者に連絡してください。")

    return customer_id
```

---

## ステップ5: 顧客（会社）への紐付け

### なぜ顧客紐付けが必要？

```
【このシステムの構造】

顧客（会社）
  └── ユーザー（社員）
       └── データ（会話履歴など）

例:
株式会社ACME
  ├── 山田太郎 → ACMEの会話履歴
  └── 鈴木花子 → ACMEの会話履歴

株式会社ベータ
  └── 田中一郎 → ベータの会話履歴

※ ACMEの人はベータのデータを見れない（情報漏洩防止）
```

### 管理者の作業手順

```bash
# ターミナルで実行（管理者が行う）

# 1. 会社を追加
python manage_customer.py add acme-corp "株式会社ACME"
# → 結果: ✅ 顧客 '株式会社ACME' を追加しました！

# 2. ユーザーを会社に紐付け
python manage_customer.py add-user acme-corp yamada@acme.co.jp
# → 結果: ✅ ユーザー 'yamada@acme.co.jp' を 'acme-corp' に紐付けました！
# → ⚠️ 注意: ユーザーは再ログインが必要です

# 3. 確認
python manage_customer.py show acme-corp
# → 結果:
#   顧客名: 株式会社ACME
#   所属ユーザー:
#     yamada@acme.co.jp
```

### なぜ再ログインが必要？

```
【IDトークンの仕組み】

ログイン時:
  Custom Claims が入った IDトークンが発行される
  ┌─────────────────────────────┐
  │ name: 山田太郎               │
  │ email: yamada@acme.co.jp    │
  │ customer_id: acme-corp      │ ← ここに入る
  └─────────────────────────────┘

管理者が紐付けを変更しても:
  既に発行されたトークンは変わらない！

だから:
  再ログインして新しいトークンを取得する必要がある
```

---

## まとめ：ファイルの繋がり

```
【ブラウザ側（フロントエンド）】

┌──────────────┐
│ firebase.ts  │  ← Firebase の設定・初期化
│              │
│ auth         │──→ useAuth.ts, api.ts で使う
│ googleProvider│
└──────────────┘
       ↓
┌──────────────┐
│ useAuth.ts   │  ← ログイン・ログアウト処理
│              │
│ loginWithGoogle()
│ logout()     │
│ user         │──→ 画面の表示切り替えに使う
└──────────────┘


【サーバー側（バックエンド）】

┌──────────────┐
│  auth.py     │  ← トークン検証・顧客ID取得
│              │
│ authenticate_request()
│ verify_token()
│ get_user_customer_id()
└──────────────┘


【管理ツール】

┌──────────────┐
│manage_customer.py│  ← 顧客・ユーザー管理
│              │
│ add          │ → 顧客を追加
│ add-user     │ → ユーザーを顧客に紐付け
│ show         │ → 顧客情報を表示
└──────────────┘
```

---

## よくあるエラーと対処法

| エラー | 原因 | 対処法 |
|--------|------|--------|
| `顧客に紐付けされていません` | ユーザーが会社に登録されていない | 管理者に連絡 → add-user 実行 → 再ログイン |
| `ポップアップがブロックされました` | ブラウザの設定 | ポップアップを許可する |
| `トークンの検証に失敗しました` | トークン期限切れ（1時間） | ページをリロード or 再ログイン |
| `アクセスが許可されていません` | メールアドレスが許可リストにない | 管理者に連絡 |

---

## 確認問題

### 理解度チェック

1. **ログイン成功後、なぜ明示的に画面を切り替えるコードを書かなくてよい？**

   <details>
   <summary>答え</summary>
   onAuthStateChanged が自動で呼ばれて、user の状態が更新されるから。
   Reactは状態が変わると自動で画面を再描画する。
   </details>

2. **Custom Claims は誰が設定できる？**

   <details>
   <summary>答え</summary>
   サーバー側（管理者）だけ。ユーザー自身は設定・変更できない。
   だから「所属会社」のような重要な情報を安全に保存できる。
   </details>

3. **ユーザーを顧客に紐付けた後、なぜ再ログインが必要？**

   <details>
   <summary>答え</summary>
   IDトークンは発行時の情報が入っている。
   紐付け後に新しいトークンを取得しないと、customer_id が含まれない。
   </details>

### 実践チャレンジ

Firebase Console を開いて、以下を確認してみよう：

1. Authentication → Users でユーザー一覧を確認
2. ユーザーをクリックして、Custom Claims に customer_id があるか確認

---

## 次に読むべきドキュメント

- `FLOW_03_セットアップの流れ.md` - 環境構築の手順
- `FLOW_01_チャット送信の流れ.md` - チャット処理の詳細
