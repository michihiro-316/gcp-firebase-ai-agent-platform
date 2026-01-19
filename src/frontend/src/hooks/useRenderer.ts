/**
 * レンダラー設定フック
 *
 * 顧客ごとのチャットレンダラー設定を config.json から読み込みます。
 */
import { useState, useEffect } from 'react'
import type { ChatRendererConfig } from '../renderers/types'
import { defaultRendererConfig } from '../renderers/types'

interface RendererState {
  config: ChatRendererConfig
  customerId: string | undefined
  isLoading: boolean
}

/**
 * レンダラー設定を読み込むフック
 */
export function useRenderer(): RendererState {
  const [config, setConfig] = useState<ChatRendererConfig>(defaultRendererConfig)
  const [customerId, setCustomerId] = useState<string | undefined>(undefined)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    async function loadConfig() {
      try {
        const response = await fetch('/config.json')
        if (response.ok) {
          const mainConfig = await response.json()
          if (mainConfig.customerId) {
            setCustomerId(mainConfig.customerId)
          }
          if (mainConfig.chatRenderer) {
            setConfig({ ...defaultRendererConfig, ...mainConfig.chatRenderer })
          }
        }
        // config.json がない場合はデフォルト設定を使用
      } catch {
        // エラー時もデフォルト設定を使用（console.error は省略）
      } finally {
        setIsLoading(false)
      }
    }
    loadConfig()
  }, [])

  return { config, customerId, isLoading }
}
