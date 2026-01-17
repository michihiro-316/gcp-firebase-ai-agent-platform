/**
 * マークダウン対応レンダラー（サンプル）
 *
 * ⚠️ 警告: このファイルはサンプルコードです。
 * 本番環境では使用しないでください。
 * XSSなどのセキュリティリスクがあります。
 *
 * このファイルは顧客別カスタムレンダラーの参考実装です。
 * 使用する場合は、以下の手順を実行してください：
 *
 * 1. このファイルを src/renderers/{customer_id}/MessageRenderer.tsx にコピー
 * 2. 必要に応じてカスタマイズ
 * 3. src/renderers/index.ts に登録
 *
 * 【依存パッケージ（本番用）】
 * npm install react-markdown
 * npm install react-syntax-highlighter @types/react-syntax-highlighter
 *
 * 【本番環境での推奨実装】
 * dangerouslySetInnerHTML の代わりに react-markdown を使用してください。
 * react-markdown はデフォルトでHTMLをサニタイズします。
 */
import type { MessageRendererProps } from '../types'

// 注意: これはサンプルコードです。
// 本番環境では以下のパッケージを使用してください。
// import ReactMarkdown from 'react-markdown'
// import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
// import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'

/**
 * マークダウン対応レンダラー
 *
 * - マークダウン記法をHTMLに変換
 * - コードブロックにシンタックスハイライト適用
 * - 表形式のデータをテーブルとして表示
 */
export function MessageRenderer({ message, config }: MessageRendererProps) {
  const { role, content } = message

  const messageStyle: React.CSSProperties = {
    backgroundColor:
      role === 'user'
        ? config.styling?.userMessageBg
        : config.styling?.assistantMessageBg,
    maxWidth: config.output?.maxWidth,
    fontFamily: config.styling?.fontFamily,
  }

  // マークダウンを使用しない場合のフォールバック
  // 実際の実装では ReactMarkdown を使用
  const renderContent = () => {
    if (!content) {
      return role === 'assistant' ? '...' : null
    }

    // ⚠️ セキュリティ警告:
    // dangerouslySetInnerHTML はXSS脆弱性のリスクがあります。
    // 本番環境では react-markdown を使用してください。
    return (
      <div
        className="markdown-content"
        dangerouslySetInnerHTML={{
          __html: simpleMarkdownParse(content),
        }}
      />
    )
  }

  return (
    <div className={`message ${role}`} style={messageStyle}>
      <div className="message-content">{renderContent()}</div>
    </div>
  )
}

/**
 * シンプルなマークダウンパーサー（デモ用）
 *
 * 注意: これは簡易実装です。
 * 本番環境では react-markdown を使用してください。
 */
function simpleMarkdownParse(text: string): string {
  return (
    text
      // コードブロック
      .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
      // インラインコード
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      // 太字
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      // 斜体
      .replace(/\*([^*]+)\*/g, '<em>$1</em>')
      // 改行
      .replace(/\n/g, '<br />')
  )
}

export default MessageRenderer
