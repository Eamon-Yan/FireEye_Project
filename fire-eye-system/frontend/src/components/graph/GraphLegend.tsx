import { NODE_META } from './graphMeta'

export default function GraphLegend() {
  return (
    <div className="mt-4 grid gap-3 sm:grid-cols-3">
      {Object.entries(NODE_META).map(([key, meta]) => (
        <div key={key} className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/6 px-4 py-3 text-white/88">
          <span className="h-3 w-3 rounded-full" style={{ backgroundColor: meta.color }} />
          <span className="text-sm font-medium">{meta.label}</span>
        </div>
      ))}
    </div>
  )
}
