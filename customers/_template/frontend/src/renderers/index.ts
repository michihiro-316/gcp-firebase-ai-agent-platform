/**
 * レンダラーレジストリ
 *
 * 顧客ごとのカスタムレンダラーを登録・取得する仕組み。
 *
 * 【新しい顧客のレンダラーを追加する方法】
 * 1. src/renderers/{customer_id}/ ディレクトリを作成
 * 2. MessageRenderer.tsx を作成（default/MessageRenderer.tsx を参考に）
 * 3. このファイルの customerRenderers に登録
 *
 * 【例: customer-a 用のカスタムレンダラー】
 * ```
 * import { MessageRenderer as CustomerARenderer } from './customer-a/MessageRenderer'
 *
 * const customerRenderers: Record<string, typeof DefaultMessageRenderer> = {
 *   'customer-a': CustomerARenderer,
 * }
 * ```
 */
import { MessageRenderer as DefaultMessageRenderer } from './default/MessageRenderer'

// 型定義
export type { ChatRendererConfig } from './types'
export { defaultRendererConfig } from './types'

/**
 * 顧客別カスタムレンダラーの登録
 *
 * 新しい顧客のレンダラーを追加する場合は、ここに追記してください。
 * キーは customer_id、値はレンダラーコンポーネントです。
 */
const customerRenderers: Record<string, typeof DefaultMessageRenderer> = {
  // 例: 'customer-a': CustomerAMessageRenderer,
  // 例: 'acme-corp': AcmeCorpMessageRenderer,
}

/**
 * 顧客IDに対応するレンダラーを取得
 *
 * @param customerId - 顧客ID（undefinedの場合はデフォルト）
 * @returns レンダラーコンポーネント
 */
export function getMessageRenderer(customerId?: string) {
  if (customerId && customerRenderers[customerId]) {
    return customerRenderers[customerId]
  }
  return DefaultMessageRenderer
}

// デフォルトレンダラーのエクスポート
export { DefaultMessageRenderer as MessageRenderer }
