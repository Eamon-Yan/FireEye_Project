import { ArrowUpRight, Info, Network, X, List } from 'lucide-react'
import type { ConnectedNode, GraphNode } from '@/types/graph'
import { FIELD_LABELS, RELATION_LABELS, getNodeMeta } from './graphMeta'
import { useState } from 'react'

interface NodeDetailPanelProps {
  selectedNode: GraphNode | null
  connectedNodes: ConnectedNode[]
  selectedProperties: Array<[string, unknown]>
  onClose: () => void
  mobile?: boolean
}

export function GraphNodeDetailPanel({
  selectedNode,
  connectedNodes,
  selectedProperties,
  onClose,
  mobile = false,
}: NodeDetailPanelProps) {
  const [showAllConnections, setShowAllConnections] = useState(false)

  const displayConnections = showAllConnections ? connectedNodes : connectedNodes.slice(0, 6)

  return (
    <div className="surface-panel rounded-[2rem] p-5 sm:p-6 h-full flex flex-col">
      <div className="flex items-start justify-between gap-4">
        <div>
          <span className="eyebrow">Node Detail</span>
          <h2 className="mt-3 text-xl font-semibold text-slate-950">节点详情</h2>
          <p className="mt-2 text-sm leading-7 text-slate-600">
            {selectedNode ? '查看节点属性、类型和关联关系。' : '点击图谱中的任意节点后，这里会显示详细信息。'}
          </p>
        </div>
        {(mobile || selectedNode) && (
          <button
            type="button"
            className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-slate-900/10 bg-white/70 text-slate-600"
            onClick={onClose}
            aria-label="关闭节点详情面板"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {!selectedNode ? (
        <div className="mt-6 rounded-[1.5rem] border border-dashed border-slate-300 bg-white/50 px-5 py-8 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-900 text-white">
            <Network className="h-5 w-5" />
          </div>
          <div className="mt-4 text-base font-semibold text-slate-900">尚未选中节点</div>
          <p className="mt-2 text-sm leading-7 text-slate-600">
            可通过点击节点、使用搜索过滤，或在图谱中聚焦关键事件链来查看详情。
          </p>
        </div>
      ) : (
        <div className="mt-6 space-y-5 overflow-y-auto pr-1 flex-1">
          <div className="rounded-[1.5rem] border border-slate-900/8 bg-white/70 p-5">
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">节点类型</div>
            <div className="mt-3 inline-flex rounded-full px-4 py-2 text-sm font-semibold text-white" style={{ backgroundColor: getNodeMeta(selectedNode.type).color }}>
              {getNodeMeta(selectedNode.type).label}
            </div>
            <div className="mt-4 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">描述</div>
            <p className="mt-3 text-sm leading-7 text-slate-700">{selectedNode.description}</p>
          </div>

          <div className="rounded-[1.5rem] border border-slate-900/8 bg-white/70 p-5">
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">属性</div>
            <div className="mt-4 space-y-3">
              {selectedProperties.length > 0 ? (
                selectedProperties.map(([key, value]) => (
                  <div key={key} className="flex items-start justify-between gap-4 rounded-2xl bg-slate-50 px-4 py-3">
                    <span className="shrink-0 text-sm font-medium text-slate-500">{FIELD_LABELS[key] ?? key}</span>
                    <span className="text-right text-sm font-semibold text-slate-800">{String(value)}</span>
                  </div>
                ))
              ) : (
                <div className="rounded-2xl bg-slate-50 px-4 py-4 text-sm text-slate-500">暂无额外属性</div>
              )}
            </div>
          </div>

          <div className="rounded-[1.5rem] border border-slate-900/8 bg-white/70 p-5">
            <div className="flex items-center justify-between gap-3">
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">关联关系</div>
              <div className="text-sm font-semibold text-slate-700">{connectedNodes.length} 条</div>
            </div>
            <div className="mt-4 space-y-3">
              {connectedNodes.length > 0 ? (
                displayConnections.map((item) => (
                  <div key={`${item.node.id}-${item.relation}-${item.direction}`} className="rounded-2xl bg-slate-50 px-4 py-3 group hover:bg-slate-100 transition">
                    <div className="text-sm font-semibold text-slate-900 line-clamp-2">{item.node.description}</div>
                    <div className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">
                      {item.direction === 'outgoing' ? '向外连接' : '来自关系'} / {RELATION_LABELS[item.relation] ?? item.relation}
                    </div>
                  </div>
                ))
              ) : (
                <div className="rounded-2xl bg-slate-50 px-4 py-4 text-sm text-slate-500">暂无关联关系</div>
              )}
              
              {!showAllConnections && connectedNodes.length > 6 && (
                <button
                  onClick={() => setShowAllConnections(true)}
                  className="w-full flex items-center justify-center gap-2 py-3 rounded-2xl border border-dashed border-slate-300 text-xs font-semibold text-slate-500 hover:text-primary-700 hover:border-primary-700/30 hover:bg-orange-50/30 transition"
                >
                  <List className="h-3 w-3" />
                  查看全部 {connectedNodes.length} 条关系
                </button>
              )}
              
              {showAllConnections && connectedNodes.length > 6 && (
                <button
                  onClick={() => setShowAllConnections(false)}
                  className="w-full flex items-center justify-center gap-2 py-3 rounded-2xl text-xs font-semibold text-slate-400 hover:text-slate-600 transition"
                >
                  收起列表
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

interface MobileNodeDetailToggleProps {
  selectedNode: GraphNode | null
  showMobilePanel: boolean
  onToggle: () => void
}

export function MobileNodeDetailToggle({
  selectedNode,
  showMobilePanel,
  onToggle,
}: MobileNodeDetailToggleProps) {
  return (
    <div className="mt-6 xl:hidden">
      <button
        type="button"
        className="btn-secondary w-full justify-between"
        onClick={onToggle}
        aria-expanded={showMobilePanel}
      >
        <span className="inline-flex items-center gap-2">
          <Info className="h-4 w-4" />
          {selectedNode ? `查看节点详情：${selectedNode.description}` : '查看图谱说明与节点详情'}
        </span>
        <ArrowUpRight className="h-4 w-4" />
      </button>
    </div>
  )
}
