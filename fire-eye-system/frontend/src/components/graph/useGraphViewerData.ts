import { useMemo } from 'react'
import type { ConnectedNode, GraphData, GraphNode } from '@/types/graph'
import { getNodeId } from './graphMeta'

interface GraphViewerDataResult {
  degreeMap: Map<string, number>
  selectedNode: GraphNode | null
  connectedNodes: ConnectedNode[]
  selectedProperties: Array<[string, unknown]>
  displayData: GraphData
}

export default function useGraphViewerData(
  graphData: GraphData,
  selectedNodeId: string | null,
  selectedNodeTypes: string[] = [],
  selectedRelationTypes: string[] = []
): GraphViewerDataResult {
  // 1. 计算显示数据（过滤）
  const displayData = useMemo(() => {
    const hasNodeFilter = selectedNodeTypes.length > 0
    const hasRelationFilter = selectedRelationTypes.length > 0

    if (!hasNodeFilter && !hasRelationFilter) {
      return graphData
    }

    // 过滤节点
    const filteredNodes = hasNodeFilter
      ? graphData.nodes.filter((node) => selectedNodeTypes.includes(node.type))
      : graphData.nodes

    const nodeIds = new Set(filteredNodes.map((n) => n.id))

    // 过滤关系
    const filteredLinks = graphData.links.filter((link) => {
      const sourceId = getNodeId(link.source)
      const targetId = getNodeId(link.target)
      
      // 关系的两端节点必须都在过滤后的节点列表中
      const nodesMatch = nodeIds.has(sourceId) && nodeIds.has(targetId)
      if (!nodesMatch) return false

      // 如果有关系类型过滤，则检查关系类型
      if (hasRelationFilter) {
        return selectedRelationTypes.includes(link.relation)
      }
      return true
    })

    return {
      nodes: filteredNodes,
      links: filteredLinks,
    }
  }, [graphData, selectedNodeTypes, selectedRelationTypes])

  // 2. 基于显示数据计算度数（这样孤立节点在过滤后会缩小）
  const degreeMap = useMemo(() => {
    const map = new Map<string, number>()
    displayData.nodes.forEach((node) => map.set(node.id, 0))
    displayData.links.forEach((link) => {
      const sourceId = getNodeId(link.source)
      const targetId = getNodeId(link.target)
      map.set(sourceId, (map.get(sourceId) ?? 0) + 1)
      map.set(targetId, (map.get(targetId) ?? 0) + 1)
    })
    return map
  }, [displayData])

  const nodesById = useMemo(() => {
    // 这里使用全量 graphData，确保即使节点被过滤掉了，详情逻辑（如关联关系）依然能找到节点对象
    return new Map(graphData.nodes.map((node) => [node.id, node]))
  }, [graphData.nodes])

  const selectedNode = useMemo(() => {
    return selectedNodeId ? nodesById.get(selectedNodeId) ?? null : null
  }, [nodesById, selectedNodeId])

  const connectedNodes = useMemo<ConnectedNode[]>(() => {
    if (!selectedNodeId) {
      return []
    }

    const result: ConnectedNode[] = []
    const seen = new Set<string>()

    // 关联关系逻辑依然基于全量数据，方便用户穿透查看
    graphData.links.forEach((link) => {
      const sourceId = getNodeId(link.source)
      const targetId = getNodeId(link.target)

      if (sourceId !== selectedNodeId && targetId !== selectedNodeId) {
        return
      }

      const connectedId = sourceId === selectedNodeId ? targetId : sourceId
      const connectedNode = nodesById.get(connectedId)
      if (!connectedNode) {
        return
      }

      const direction = sourceId === selectedNodeId ? 'outgoing' : 'incoming'
      const key = `${connectedId}-${link.relation}-${direction}`
      if (seen.has(key)) {
        return
      }

      seen.add(key)
      result.push({ node: connectedNode, relation: link.relation, direction })
    })

    return result
  }, [graphData.links, nodesById, selectedNodeId])

  const selectedProperties = useMemo(() => {
    if (!selectedNode) {
      return [] as Array<[string, unknown]>
    }

    return Object.entries(selectedNode.properties).filter(([key, value]) => {
      if (['id', 'created_at', 'updated_at'].includes(key)) return false
      if ((key === 'standard_term' || key === 'description') && String(value) === selectedNode.description) {
        return false
      }
      if (key === 'severity_level' && String(value) === '5') return false
      return value !== null && value !== ''
    })
  }, [selectedNode])

  return {
    degreeMap,
    selectedNode,
    connectedNodes,
    selectedProperties,
    displayData,
  }
}
