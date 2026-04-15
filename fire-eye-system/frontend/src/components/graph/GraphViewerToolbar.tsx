import Link from 'next/link'
import { Download, Home, Network, RefreshCw, Search, Upload, Filter, Check } from 'lucide-react'
import { useState } from 'react'
import type { GraphData } from '@/types/graph'
import { NODE_META, RELATION_LABELS, NODE_TYPES, RELATION_TYPES } from './graphMeta'
import { clsx } from 'clsx'

interface GraphViewerToolbarProps {
  graphData: GraphData
  displayData: GraphData
  searchInput: string
  searchTerm: string
  onSearchInputChange: (value: string) => void
  onSearchSubmit: (event: React.FormEvent<HTMLFormElement>) => void
  onRefresh: () => void
  onZoomToFit: () => void
  onExport: () => void
  selectedNodeTypes: string[]
  setSelectedNodeTypes: (types: string[]) => void
  selectedRelationTypes: string[]
  setSelectedRelationTypes: (types: string[]) => void
}

export default function GraphViewerToolbar({
  graphData,
  displayData,
  searchInput,
  searchTerm,
  onSearchInputChange,
  onSearchSubmit,
  onRefresh,
  onZoomToFit,
  onExport,
  selectedNodeTypes,
  setSelectedNodeTypes,
  selectedRelationTypes,
  setSelectedRelationTypes,
}: GraphViewerToolbarProps) {
  const [showFilters, setShowFilters] = useState(false)

  const toggleNodeType = (type: string) => {
    setSelectedNodeTypes(
      selectedNodeTypes.includes(type)
        ? selectedNodeTypes.filter((t) => t !== type)
        : [...selectedNodeTypes, type]
    )
  }

  const toggleRelationType = (type: string) => {
    setSelectedRelationTypes(
      selectedRelationTypes.includes(type)
        ? selectedRelationTypes.filter((t) => t !== type)
        : [...selectedRelationTypes, type]
    )
  }

  const clearFilters = () => {
    setSelectedNodeTypes([])
    setSelectedRelationTypes([])
  }

  const hasFilters = selectedNodeTypes.length > 0 || selectedRelationTypes.length > 0

  return (
    <>
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <span className="eyebrow">Knowledge Graph</span>
          <h1 className="mt-4 text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
            图谱浏览器
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600 sm:text-base">
            以响应式画布浏览火灾事件、隐患与后果影响关系，支持搜索、导出和节点详情查看。
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3 sm:flex sm:flex-wrap sm:justify-end">
          <Link href="/" className="btn-secondary">
            <Home className="h-4 w-4" />
            返回总览
          </Link>
          <Link href="/upload" className="btn-primary">
            <Upload className="h-4 w-4" />
            上传文档
          </Link>
        </div>
      </div>

      <div className="surface-panel-strong rounded-[2rem] p-4 sm:p-5">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center flex-1">
            <form className="flex flex-col gap-3 sm:flex-row sm:items-center flex-1" onSubmit={onSearchSubmit}>
              <label className="relative block min-w-0 flex-1 sm:min-w-[18rem]">
                <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  className="input-field pl-11"
                  placeholder="按节点描述搜索图谱内容"
                  value={searchInput}
                  onChange={(event) => onSearchInputChange(event.target.value)}
                  aria-label="搜索图谱节点"
                />
              </label>
              <button type="submit" className="btn-primary">
                <Search className="h-4 w-4" />
                搜索
              </button>
            </form>
            
            <button 
              type="button" 
              className={clsx(
                "btn-secondary",
                hasFilters && "border-primary-700/30 bg-orange-50/50 text-primary-700"
              )}
              onClick={() => setShowFilters(!showFilters)}
            >
              <Filter className="h-4 w-4" />
              筛选 {hasFilters && `(${selectedNodeTypes.length + selectedRelationTypes.length})`}
            </button>
          </div>

          <div className="flex flex-wrap gap-2">
            <button type="button" className="btn-secondary" onClick={onRefresh} aria-label="刷新图谱数据">
              <RefreshCw className="h-4 w-4" />
              刷新
            </button>
            <button type="button" className="btn-secondary" onClick={onZoomToFit} aria-label="将图谱缩放到合适视图">
              <Network className="h-4 w-4" />
              适配视图
            </button>
            <button type="button" className="btn-secondary" onClick={onExport} aria-label="导出图谱数据">
              <Download className="h-4 w-4" />
              导出
            </button>
          </div>
        </div>

        {showFilters && (
          <div className="mt-5 grid gap-6 border-t border-slate-900/10 pt-5 md:grid-cols-2">
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">节点类型</span>
                {selectedNodeTypes.length > 0 && (
                  <button onClick={() => setSelectedNodeTypes([])} className="text-xs text-primary-700 hover:underline">重置</button>
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                {NODE_TYPES.map((type) => (
                  <button
                    key={type}
                    onClick={() => toggleNodeType(type)}
                    className={clsx(
                      "inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition",
                      selectedNodeTypes.includes(type)
                        ? "bg-slate-900 text-white shadow-md"
                        : "bg-white/70 text-slate-600 hover:bg-white"
                    )}
                  >
                    <span className="h-2 w-2 rounded-full" style={{ backgroundColor: NODE_META[type]?.color }} />
                    {NODE_META[type]?.label || type}
                    {selectedNodeTypes.includes(type) && <Check className="h-3 w-3 ml-1" />}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">关系类型</span>
                {selectedRelationTypes.length > 0 && (
                  <button onClick={() => setSelectedRelationTypes([])} className="text-xs text-primary-700 hover:underline">重置</button>
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                {RELATION_TYPES.map((type) => (
                  <button
                    key={type}
                    onClick={() => toggleRelationType(type)}
                    className={clsx(
                      "inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition",
                      selectedRelationTypes.includes(type)
                        ? "bg-slate-900 text-white shadow-md"
                        : "bg-white/70 text-slate-600 hover:bg-white"
                    )}
                  >
                    {RELATION_LABELS[type] || type}
                    {selectedRelationTypes.includes(type) && <Check className="h-3 w-3 ml-1" />}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <div className="stat-card">
            <div className="text-sm text-slate-500">显示节点 / 总计</div>
            <div className="mt-2 text-2xl font-semibold text-slate-950">
              {displayData.nodes.length} <span className="text-sm font-normal text-slate-400">/ {graphData.nodes.length}</span>
            </div>
          </div>
          <div className="stat-card">
            <div className="text-sm text-slate-500">显示关系 / 总计</div>
            <div className="mt-2 text-2xl font-semibold text-slate-950">
              {displayData.links.length} <span className="text-sm font-normal text-slate-400">/ {graphData.links.length}</span>
            </div>
          </div>
          <div className="stat-card">
            <div className="text-sm text-slate-500">当前搜索状态</div>
            <div className="mt-2 truncate text-lg font-semibold text-slate-950">
              {searchTerm || '全部图谱'}
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
