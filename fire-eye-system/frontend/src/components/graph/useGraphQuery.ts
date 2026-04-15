import { useCallback, useEffect, useState } from 'react'
import type { GraphData } from '@/types/graph'

const DEFAULT_GRAPH_DATA: GraphData = { nodes: [], links: [] }

interface UseGraphQueryResult {
  graphData: GraphData
  isLoading: boolean
  error: string | null
  refetch: (term: string) => Promise<void>
}

export default function useGraphQuery(
  searchTerm: string,
  onGraphLoaded?: (graphData: GraphData) => void,
  onGraphLoadFailed?: () => void
): UseGraphQueryResult {
  const [graphData, setGraphData] = useState<GraphData>(DEFAULT_GRAPH_DATA)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refetch = useCallback(
    async (term: string) => {
      setIsLoading(true)
      setError(null)

      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'
        const response = await fetch(
          `${apiUrl}/api/v1/graph/query?limit=100&include_relationships=true${
            term ? `&search_text=${encodeURIComponent(term)}` : ''
          }`,
          {
            headers: { Accept: 'application/json' },
            cache: 'no-store',
          }
        )

        if (!response.ok) {
          throw new Error(`接口请求失败 (${response.status})`)
        }

        const result = (await response.json()) as { status?: string; data?: GraphData; message?: string }
        if (result.status !== 'success' || !result.data) {
          throw new Error(result.message || '图谱数据返回异常')
        }

        setGraphData(result.data)
        onGraphLoaded?.(result.data)
      } catch (fetchError) {
        setGraphData(DEFAULT_GRAPH_DATA)
        setError(fetchError instanceof Error ? fetchError.message : '关系图数据加载失败')
        onGraphLoadFailed?.()
      } finally {
        setIsLoading(false)
      }
    },
    [onGraphLoadFailed, onGraphLoaded]
  )

  useEffect(() => {
    void refetch(searchTerm)
  }, [refetch, searchTerm])

  return {
    graphData,
    isLoading,
    error,
    refetch,
  }
}
