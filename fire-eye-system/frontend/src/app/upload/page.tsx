'use client'

import { useMemo, useState } from 'react'
import Link from 'next/link'
import { ArrowRight, FileText, Flame, LineChart, Network } from 'lucide-react'
import Layout from '@/components/Layout'
import FileUpload from '@/components/FileUpload'
import type { EventChain, UploadResult } from '@/types/upload'

const processSteps = [
  {
    title: '文档解析',
    description: '提取章节与段落结构，为后续事件链抽取建立上下文。',
    icon: FileText,
  },
  {
    title: '事件抽取与校验',
    description: '通过 LLM 提炼事件关系，执行逻辑验证和术语归一化。',
    icon: Flame,
  },
  {
    title: '图谱构建',
    description: '将有效链路写入图数据库，用于图谱浏览与关系检索。',
    icon: Network,
  },
]

function confidenceTone(confidence: number) {
  if (confidence >= 0.8) return 'bg-emerald-100 text-emerald-700'
  if (confidence >= 0.6) return 'bg-amber-100 text-amber-700'
  return 'bg-rose-100 text-rose-700'
}

export default function UploadPage() {
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null)

  const topChains = useMemo<EventChain[]>(() => {
    return uploadResult?.event_chains?.chains?.slice(0, 10) ?? []
  }, [uploadResult])

  return (
    <Layout>
      <section className="app-shell py-8 sm:py-10 lg:py-12">
        <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_340px]">
          <div className="space-y-8">
            <div className="surface-panel-strong overflow-hidden rounded-[2rem] px-6 py-8 sm:px-8 sm:py-10">
              <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
                <div className="max-w-2xl">
                  <span className="eyebrow">Upload Workflow</span>
                  <h1 className="mt-4 text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
                    上传火灾调查报告并生成事理图谱
                  </h1>
                  <p className="mt-3 text-sm leading-8 text-slate-600 sm:text-base">
                    页面聚焦清晰的输入流程、处理结果反馈与后续跳转，减少原先过于依赖玻璃态和内联样式造成的信息噪音。
                  </p>
                </div>

                <Link href="/graph" className="btn-secondary">
                  <Network className="h-4 w-4" />
                  直接查看图谱
                </Link>
              </div>

              <div className="mt-8 grid gap-4 md:grid-cols-3">
                {processSteps.map(({ title, description, icon: Icon }) => (
                  <div key={title} className="rounded-[1.75rem] border border-slate-900/8 bg-white/70 p-5">
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-900 text-white">
                      <Icon className="h-5 w-5" />
                    </div>
                    <h2 className="mt-4 text-lg font-semibold text-slate-950">{title}</h2>
                    <p className="mt-2 text-sm leading-7 text-slate-600">{description}</p>
                  </div>
                ))}
              </div>
            </div>

            <FileUpload onUploadSuccess={setUploadResult} onUploadError={() => undefined} />

            <div className="surface-panel rounded-[2rem] p-6 sm:p-7">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-100 text-primary-700">
                  <LineChart className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-slate-950">处理说明</h2>
                  <p className="mt-1 text-sm text-slate-600">上传前后建议关注的关键点。</p>
                </div>
              </div>

              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <div className="rounded-[1.5rem] border border-slate-900/8 bg-white/70 p-5">
                  <div className="text-sm font-semibold text-slate-900">推荐输入</div>
                  <ul className="mt-4 space-y-3 text-sm leading-7 text-slate-600">
                    <li>优先使用 DOCX、TXT，或包含可复制文本层的 PDF。</li>
                    <li>若文档特别长，建议先选择结构完整、案例集中的报告进行展示。</li>
                    <li>上传前确认章节标题和段落信息较完整，便于上下文抽取。</li>
                  </ul>
                </div>

                <div className="rounded-[1.5rem] border border-slate-900/8 bg-white/70 p-5">
                  <div className="text-sm font-semibold text-slate-900">处理后建议</div>
                  <ul className="mt-4 space-y-3 text-sm leading-7 text-slate-600">
                    <li>优先关注有效事件链数、验证通过率和平均置信度。</li>
                    <li>若事件链过少，可检查文档是否为扫描版图片 PDF。</li>
                    <li>处理完成后进入图谱页，结合搜索和节点详情进行演示。</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <aside className="space-y-6">
            <div className="surface-panel rounded-[2rem] p-6">
              <span className="eyebrow">Result Snapshot</span>
              <h2 className="mt-4 text-xl font-semibold text-slate-950">结果摘要</h2>
              <p className="mt-2 text-sm leading-7 text-slate-600">
                成功上传后，此区域展示最新处理结果的关键摘要，便于演示时快速讲解。
              </p>

              <div className="mt-5 space-y-3">
                <div className="rounded-2xl bg-white/70 px-4 py-4">
                  <div className="text-sm text-slate-500">当前文档</div>
                  <div className="mt-2 text-sm font-semibold text-slate-900 break-all">
                    {uploadResult?.filename ?? '尚未上传文档'}
                  </div>
                </div>
                <div className="rounded-2xl bg-white/70 px-4 py-4">
                  <div className="text-sm text-slate-500">事件链数量</div>
                  <div className="mt-2 text-2xl font-semibold text-slate-950">{uploadResult?.event_chains?.count ?? 0}</div>
                </div>
                <div className="rounded-2xl bg-white/70 px-4 py-4">
                  <div className="text-sm text-slate-500">验证通过率</div>
                  <div className="mt-2 text-2xl font-semibold text-slate-950">
                    {uploadResult?.processing_statistics
                      ? `${(uploadResult.processing_statistics.validation_rate * 100).toFixed(1)}%`
                      : '--'}
                  </div>
                </div>
              </div>

              <div className="mt-6">
                <Link href="/graph" className="btn-primary w-full justify-center">
                  查看图谱结果
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </div>

            <div className="surface-panel rounded-[2rem] p-6">
              <h2 className="text-xl font-semibold text-slate-950">事件链预览</h2>
              <p className="mt-2 text-sm leading-7 text-slate-600">默认展示前 10 条链路，突出高置信度结果。</p>

              <div className="mt-5 space-y-3">
                {topChains.length > 0 ? (
                  topChains.map((chain, index) => (
                    <div key={`${chain.source}-${chain.target}-${index}`} className="rounded-[1.5rem] border border-slate-900/8 bg-white/70 p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div className="text-sm leading-7 text-slate-700">
                          <span className="font-semibold text-primary-700">{chain.source}</span>
                          <span className="mx-2 text-slate-400">→ {chain.relation} →</span>
                          <span className="font-semibold text-sky-700">{chain.target}</span>
                        </div>
                        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${confidenceTone(chain.confidence)}`}>
                          {(chain.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      {chain.context && (
                        <p className="mt-3 text-sm leading-7 text-slate-500">{chain.context}</p>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="rounded-[1.5rem] border border-dashed border-slate-300 bg-white/55 px-5 py-8 text-center text-sm leading-7 text-slate-500">
                    上传成功后，这里会展示提取到的事件链摘要。
                  </div>
                )}
              </div>
            </div>
          </aside>
        </div>
      </section>
    </Layout>
  )
}
