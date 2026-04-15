import Link from 'next/link'
import { AlertCircle, RefreshCw, Upload } from 'lucide-react'

interface GraphCanvasStateProps {
  isLoading: boolean
  error: string | null
  emptyStateAction: string
  onRetry: () => void
}

export default function GraphCanvasState({
  isLoading,
  error,
  emptyStateAction,
  onRetry,
}: GraphCanvasStateProps) {
  if (isLoading) {
    return (
      <div className="absolute inset-0 flex items-center justify-center bg-slate-950/35 backdrop-blur-sm">
        <div className="surface-panel-dark rounded-3xl px-8 py-7 text-center">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-white/25 border-t-white" />
          <div className="mt-4 text-base font-semibold text-white">正在加载关系图数据</div>
          <div className="mt-2 text-sm text-white/70">同步节点与关系信息，请稍候。</div>
        </div>
      </div>
    )
  }

  return (
    <div className="absolute inset-0 flex items-center justify-center px-4">
      <div className="surface-panel-dark max-w-md rounded-[2rem] px-8 py-8 text-center text-white">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-white/10">
          <AlertCircle className="h-6 w-6" />
        </div>
        <h2 className="mt-5 text-2xl font-semibold">
          {error ? '图谱加载失败' : '暂无关系图数据'}
        </h2>
        <p className="mt-3 text-sm leading-7 text-white/75">
          {error || '上传文档后即可在此浏览抽取结果，并查看节点间的因果关系。'}
        </p>
        <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-center">
          <button type="button" className="btn-primary" onClick={onRetry}>
            <RefreshCw className="h-4 w-4" />
            {emptyStateAction}
          </button>
          <Link href="/upload" className="btn-secondary">
            <Upload className="h-4 w-4" />
            前往上传页
          </Link>
        </div>
      </div>
    </div>
  )
}
