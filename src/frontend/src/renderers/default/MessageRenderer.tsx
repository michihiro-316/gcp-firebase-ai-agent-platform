/**
 * デフォルトのメッセージレンダラー
 *
 * チャットメッセージの表示を担当するコンポーネント。
 * 顧客ごとにカスタマイズしたい場合は、このファイルをコピーして
 * renderers/{customer_id}/MessageRenderer.tsx を作成してください。
 *
 * 【カスタマイズ例】
 * - 表形式のデータを<table>タグでレンダリング
 * - グラフライブラリ（Chart.js等）でデータを可視化
 * - 特定のキーワードでリンクや画像を埋め込み
 * - マークダウンのパース処理を追加
 */
import type { MessageRendererProps } from '../types'

/**
 * デフォルトのメッセージレンダラー
 *
 * シンプルなテキスト表示のみ。
 * 顧客要件に応じてカスタマイズしてください。
 */
export function MessageRenderer({ message, config }: MessageRendererProps) {
  const { role, content } = message

  // スタイルを設定から適用
  const messageStyle: React.CSSProperties = {
    backgroundColor:
      role === 'user'
        ? config.styling?.userMessageBg
        : config.styling?.assistantMessageBg,
    maxWidth: config.output?.maxWidth,
    fontFamily: config.styling?.fontFamily,
  }

  return (
    <div className={`message ${role}`} style={messageStyle}>
      <div className="message-content">
        {content || (role === 'assistant' && '...')}
      </div>
    </div>
  )
}

export default MessageRenderer
