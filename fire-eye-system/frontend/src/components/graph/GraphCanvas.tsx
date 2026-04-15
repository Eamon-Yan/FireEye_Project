import { useEffect } from 'react'
import dynamic from 'next/dynamic'
import type { GraphData, GraphNode } from '@/types/graph'
import GraphCanvasState from './GraphCanvasState'
import GraphLegend from './GraphLegend'
import { getNodeMeta } from './graphMeta'

const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), {
  ssr: false,
})

interface GraphCanvasProps {
  fgRef: React.MutableRefObject<any>
  graphData: GraphData
  dimensions: { width: number; height: number }
  degreeMap: Map<string, number>
  selectedNodeId: string | null
  isLoading: boolean
  error: string | null
  emptyStateAction: string
  onRetry: () => void
  onNodeSelect: (node: GraphNode) => void
}

export default function GraphCanvas({
  fgRef,
  graphData,
  dimensions,
  degreeMap,
  selectedNodeId,
  isLoading,
  error,
  emptyStateAction,
  onRetry,
  onNodeSelect,
}: GraphCanvasProps) {
  useEffect(() => {
    if (!fgRef.current || graphData.nodes.length === 0) {
      return
    }

    const graph = fgRef.current
    graph.d3Force('charge')?.strength?.(-340)
    graph.d3Force('link')?.distance?.(90)
    graph.d3Force(
      'collide',
      graph.d3ForceCollide((node: { val?: number }) => (node.val ?? 6) + 26).strength(1).iterations(2)
    )
    graph.d3Force('center', graph.d3ForceCenter(dimensions.width / 2, dimensions.height / 2).strength(0.18))
    graph.d3ReheatSimulation()
  }, [dimensions, fgRef, graphData])

  return (
    <div className="surface-panel-dark relative overflow-hidden rounded-[2rem] p-3 sm:p-4">
      <div className="absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-white/8 to-transparent" />
      <div className="relative overflow-hidden rounded-[1.5rem] border border-white/10 bg-slate-950/25">
        <div style={{ height: `${dimensions.height}px` }} className="relative w-full min-w-0">
          {!isLoading && !error && graphData.nodes.length > 0 && (
            <ForceGraph2D
              ref={fgRef}
              width={dimensions.width}
              height={dimensions.height}
              graphData={graphData}
              nodeId="id"
              nodeLabel="description"
              linkSource="source"
              linkTarget="target"
              linkLabel="relation"
              enableNodeDrag
              enablePanInteraction
              enableZoomInteraction
              cooldownTicks={180}
              d3AlphaDecay={0.014}
              d3VelocityDecay={0.24}
              warmupTicks={80}
              linkColor={() => 'rgba(255,255,255,0.28)'}
              linkWidth={(link: any) => Math.max(1.2, Math.sqrt(link.confidence ?? 1) * 1.8)}
              linkDirectionalArrowLength={4}
              linkDirectionalArrowRelPos={1}
              nodeColor={(node: any) => getNodeMeta(node.type).color}
              nodeVal={(node: any) => 6 + Math.min((degreeMap.get(node.id) ?? 0) * 1.8, 12)}
              onNodeClick={(node: any) => onNodeSelect(node as GraphNode)}
              nodeCanvasObject={(node: any, ctx, globalScale) => {
                const label = node.description
                const radius = node.val ?? 7
                const isSelected = selectedNodeId === node.id
                const meta = getNodeMeta(node.type)
                const fontSize = 12 / globalScale

                if (isSelected) {
                  ctx.beginPath()
                  ctx.arc(node.x, node.y, radius + 5, 0, 2 * Math.PI, false)
                  ctx.fillStyle = 'rgba(255, 255, 255, 0.18)'
                  ctx.fill()
                }

                ctx.beginPath()
                ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false)
                ctx.fillStyle = meta.color
                ctx.fill()
                ctx.strokeStyle = 'rgba(255,255,255,0.95)'
                ctx.lineWidth = isSelected ? 2.8 / globalScale : 1.6 / globalScale
                ctx.stroke()

                if (globalScale > 0.48) {
                  ctx.font = `${fontSize}px 'Noto Sans SC', sans-serif`
                  ctx.textAlign = 'center'
                  ctx.textBaseline = 'middle'

                  const textWidth = ctx.measureText(label).width
                  const labelY = node.y + radius + fontSize + 5
                  const paddingX = 6
                  const paddingY = 4
                  const rectX = node.x - textWidth / 2 - paddingX
                  const rectY = labelY - fontSize / 2 - paddingY
                  const rectWidth = textWidth + paddingX * 2
                  const rectHeight = fontSize + paddingY * 2
                  const borderRadius = 5

                  ctx.beginPath()
                  ctx.moveTo(rectX + borderRadius, rectY)
                  ctx.lineTo(rectX + rectWidth - borderRadius, rectY)
                  ctx.quadraticCurveTo(rectX + rectWidth, rectY, rectX + rectWidth, rectY + borderRadius)
                  ctx.lineTo(rectX + rectWidth, rectY + rectHeight - borderRadius)
                  ctx.quadraticCurveTo(rectX + rectWidth, rectY + rectHeight, rectX + rectWidth - borderRadius, rectY + rectHeight)
                  ctx.lineTo(rectX + borderRadius, rectY + rectHeight)
                  ctx.quadraticCurveTo(rectX, rectY + rectHeight, rectX, rectY + rectHeight - borderRadius)
                  ctx.lineTo(rectX, rectY + borderRadius)
                  ctx.quadraticCurveTo(rectX, rectY, rectX + borderRadius, rectY)
                  ctx.closePath()
                  ctx.fillStyle = 'rgba(255, 249, 241, 0.92)'
                  ctx.fill()
                  ctx.fillStyle = '#16202f'
                  ctx.fillText(label, node.x, labelY)
                }
              }}
            />
          )}

          {(isLoading || error || graphData.nodes.length === 0) && (
            <GraphCanvasState
              isLoading={isLoading}
              error={error}
              emptyStateAction={emptyStateAction}
              onRetry={onRetry}
            />
          )}
        </div>
      </div>

      <GraphLegend />
    </div>
  )
}
