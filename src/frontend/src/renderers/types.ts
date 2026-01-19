/**
 * チャットレンダラーの型定義
 *
 * 顧客ごとのチャット表示設定を定義します。
 * 新しいオプションは必要になった時点で追加してください。
 */
import type { Message } from '../hooks/useChat'

/**
 * チャットレンダラー設定
 */
export interface ChatRendererConfig {
  /** 出力形式の設定 */
  output?: {
    /** 表形式の出力を有効化（_examples/TableRenderer.tsx で使用） */
    enableTables?: boolean
    /** メッセージの最大幅 */
    maxWidth?: string
  }

  /** スタイリング設定 */
  styling?: {
    /** ユーザーメッセージの背景色 */
    userMessageBg?: string
    /** アシスタントメッセージの背景色 */
    assistantMessageBg?: string
    /** フォントファミリー */
    fontFamily?: string
  }

  /** カスタム設定（顧客固有の拡張用） */
  custom?: Record<string, unknown>
}

/**
 * メッセージレンダラーのProps型
 *
 * 全てのカスタムレンダラーはこの型を使用してください。
 */
export interface MessageRendererProps {
  message: Message
  config: ChatRendererConfig
}

/**
 * デフォルトのレンダラー設定
 */
export const defaultRendererConfig: ChatRendererConfig = {
  output: {
    enableTables: false,
    maxWidth: '800px',
  },
  styling: {
    userMessageBg: undefined,
    assistantMessageBg: undefined,
    fontFamily: 'inherit',
  },
  custom: {},
}
