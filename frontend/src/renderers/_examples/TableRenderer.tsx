/**
 * 表形式データ対応レンダラー（サンプル）
 *
 * AIからの応答に含まれるJSON形式のデータを
 * 自動的にテーブルとして表示するレンダラー。
 *
 * 【対応形式】
 * ```json
 * {"type": "table", "data": [...], "headers": [...]}
 * ```
 *
 * 【使用方法】
 * 1. このファイルを src/renderers/{customer_id}/MessageRenderer.tsx にコピー
 * 2. src/renderers/index.ts に登録
 */
import type { MessageRendererProps } from '../types'

interface TableData {
  type: 'table'
  headers: string[]
  data: Record<string, unknown>[]
}

/**
 * 表形式データ対応レンダラー
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

  const renderContent = () => {
    if (!content) {
      return role === 'assistant' ? '...' : null
    }

    // テーブルとして有効かどうかを判定
    if (config.output?.enableTables) {
      const tableData = tryParseTableData(content)
      if (tableData) {
        return renderTable(tableData)
      }
    }

    // 通常のテキスト表示
    return content
  }

  return (
    <div className={`message ${role}`} style={messageStyle}>
      <div className="message-content">{renderContent()}</div>
    </div>
  )
}

/**
 * コンテンツからテーブルデータを抽出
 */
function tryParseTableData(content: string): TableData | null {
  try {
    // JSON部分を抽出
    const jsonMatch = content.match(/```json\n?([\s\S]*?)```/)
    if (jsonMatch) {
      const data = JSON.parse(jsonMatch[1])
      if (isValidTableData(data)) {
        return data as TableData
      }
    }

    // 直接JSONの場合
    const data = JSON.parse(content)
    if (isValidTableData(data)) {
      return data as TableData
    }
  } catch {
    // JSONではない場合は無視
  }
  return null
}

/**
 * テーブルデータとして有効かどうかをチェック
 */
function isValidTableData(data: unknown): boolean {
  if (typeof data !== 'object' || data === null) return false
  const obj = data as Record<string, unknown>
  return (
    obj.type === 'table' &&
    Array.isArray(obj.data) &&
    Array.isArray(obj.headers)
  )
}

/**
 * テーブルをレンダリング
 */
function renderTable(tableData: TableData) {
  const { headers, data } = tableData

  return (
    <div className="table-container">
      <table className="data-table">
        <thead>
          <tr>
            {headers.map((header, i) => (
              <th key={i}>{header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={i}>
              {headers.map((header, j) => (
                <td key={j}>{String(row[header] ?? '')}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default MessageRenderer
