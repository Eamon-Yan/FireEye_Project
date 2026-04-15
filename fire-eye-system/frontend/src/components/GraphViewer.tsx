'use client'

import { useCallback, useRef, useState } from 'react'
import type { GraphNode } from '@/types/graph'
import GraphCanvas from '@/components/graph/GraphCanvas'
import GraphViewerToolbar from '@/components/graph/GraphViewerToolbar'
import { GraphNodeDetailPanel, MobileNodeDetailToggle } from '@/components/graph/GraphNodeDetailPanel'
import useGraphQuery from '@/components/graph/useGraphQuery'
import useGraphViewerData from '@/components/graph/useGraphViewerData'
import useViewportDimensions from '@/components/graph/useViewportDimensions'

export default function GraphViewer() {
  const fgRef = useRef<any>(null)
  const [searchInput, setSearchInput] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [showMobilePanel, setShowMobilePanel] = useState(false)

  // 增强功能：过滤状态
  const [selectedNodeTypes, setSelectedNodeTypes] = useState<string[]>([])
  const [selectedRelationTypes, setSelectedRelationTypes] = useState<string[]>([])

  const dimensions = useViewportDimensions()

  const handleGraphLoaded = useCallback((nextGraphData: { nodes: Array<{ id: string }> }) => {
    setSelectedNodeId((currentId) => {
      if (!currentId) return currentId
      return nextGraphData.nodes.some((node) => node.id === currentId) ? currentId : null
    })
  }, [])

  const handleGraphLoadFailed = useCallback(() => {
    setSelectedNodeId(null)
  }, [])

  const { graphData, isLoading, error, refetch } = useGraphQuery(
    searchTerm,
    handleGraphLoaded,
    handleGraphLoadFailed
  )

  const { degreeMap, selectedNode, connectedNodes, selectedProperties, displayData } = useGraphViewerData(
    graphData,
    selectedNodeId,
    selectedNodeTypes,
    selectedRelationTypes
  )

  const handleSearchSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSearchTerm(searchInput.trim())
  }

  const handleExport = () => {
    const dataBlob = new Blob([JSON.stringify(graphData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `fire-eye-graph-${Date.now()}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  const handleNodeSelect = (node: GraphNode) => {
    setSelectedNodeId(node.id)
    setShowMobilePanel(true)
  }

  const handleZoomToFit = () => {
    fgRef.current?.zoomToFit(500, 80)
  }

  const emptyStateAction = error ? '重新尝试获取图谱接口' : '先上传文档生成图谱数据'

  return (
    <section className="app-shell py-6 sm:py-8">
      <GraphViewerToolbar
        graphData={graphData}
        displayData={displayData}
        searchInput={searchInput}
        searchTerm={searchTerm}
        onSearchInputChange={setSearchInput}
        onSearchSubmit={handleSearchSubmit}
        onRefresh={() => void refetch(searchTerm)}
        onZoomToFit={handleZoomToFit}
        onExport={handleExport}
        selectedNodeTypes={selectedNodeTypes}
        setSelectedNodeTypes={setSelectedNodeTypes}
        selectedRelationTypes={selectedRelationTypes}
        setSelectedRelationTypes={setSelectedRelationTypes}
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
        <div className="space-y-4">
          <GraphCanvas
            fgRef={fgRef}
            graphData={displayData}
            dimensions={dimensions}
            degreeMap={degreeMap}
            selectedNodeId={selectedNodeId}
            isLoading={isLoading}
            error={error}
            emptyStateAction={emptyStateAction}
            onRetry={() => void refetch(searchTerm)}
            onNodeSelect={handleNodeSelect}
          />
        </div>

        <aside className="hidden xl:block">
          <GraphNodeDetailPanel
            selectedNode={selectedNode}
            connectedNodes={connectedNodes}
            selectedProperties={selectedProperties}
            onClose={() => setSelectedNodeId(null)}
          />
        </aside>
      </div>

      <MobileNodeDetailToggle
        selectedNode={selectedNode}
        showMobilePanel={showMobilePanel}
        onToggle={() => setShowMobilePanel((current) => !current)}
      />

      {showMobilePanel && (
        <div className="fixed inset-x-0 bottom-0 z-50 rounded-t-[2rem] border border-slate-900/10 bg-[rgba(251,248,243,0.96)] p-4 shadow-2xl backdrop-blur-xl xl:hidden">
          <GraphNodeDetailPanel
            selectedNode={selectedNode}
            connectedNodes={connectedNodes}
            selectedProperties={selectedProperties}
            onClose={() => setShowMobilePanel(false)}
            mobile
          />
        </div>
      )}
    </section>
  )
}
