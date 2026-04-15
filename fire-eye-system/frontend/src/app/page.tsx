import Link from 'next/link'
import { ArrowRight, Flame, Network, ShieldCheck, Upload, Sparkles } from 'lucide-react'
import Layout from '@/components/Layout'

const highlights = [
  {
    title: '智能事件链抽取',
    description: '上传火灾调查报告后，自动识别关键事件、关系和因果脉络。',
    icon: Sparkles,
  },
  {
    title: '图谱结构校验',
    description: '对抽取结果执行术语归一、逻辑验证与图数据库入库准备。',
    icon: ShieldCheck,
  },
  {
    title: '交互式关系图谱',
    description: '通过可视化方式浏览节点关系，定位关键风险与传播路径。',
    icon: Network,
  },
]

const quickActions = [
  {
    title: '上传调查文档',
    description: '开始一次新的抽取任务，查看处理统计与事件链摘要。',
    href: '/upload',
    label: '进入上传页',
    icon: Upload,
  },
  {
    title: '查看关系图谱',
    description: '直接进入图谱视图，检索图节点并查看关联详情。',
    href: '/graph',
    label: '进入图谱页',
    icon: Network,
  },
]

const workflow = [
  '上传 PDF、DOCX、TXT 调查文档',
  '解析章节并抽取事件链',
  '执行校验、归一化与图数据库存储',
  '在关系图中查看节点、关系和详情',
]

export default function HomePage() {
  return (
    <Layout>
      <section className="app-shell py-8 sm:py-12 lg:py-16">
        <div className="grid gap-8 lg:grid-cols-[1.2fr_0.8fr] lg:items-stretch">
          <div className="surface-panel-strong relative overflow-hidden rounded-[2rem] px-6 py-8 sm:px-8 sm:py-10 lg:px-10">
            <div className="absolute right-0 top-0 h-40 w-40 rounded-full bg-orange-300/20 blur-3xl" />
            <span className="eyebrow">Fire Intelligence Workflow</span>
            <div className="mt-6 max-w-2xl">
              <h1 className="text-balance text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl lg:text-6xl">
                火瞳系统将调查文档转化为可检索、可验证的火灾事理图谱。
              </h1>
              <p className="mt-5 max-w-2xl text-base leading-8 text-slate-600 sm:text-lg">
                聚焦核心流程说明与关键入口，减少首次进入即面对复杂图谱的理解门槛。
              </p>
            </div>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link href="/upload" className="btn-primary">
                <Upload className="h-4 w-4" />
                开始上传文档
              </Link>
              <Link href="/graph" className="btn-secondary">
                <Network className="h-4 w-4" />
                直接查看图谱
              </Link>
            </div>

            <div className="mt-10 grid gap-4 sm:grid-cols-3">
              <div className="stat-card">
                <div className="text-sm text-slate-500">核心能力</div>
                <div className="mt-2 text-2xl font-semibold text-slate-950">3 段流程</div>
                <div className="mt-2 text-sm text-slate-600">抽取、校验、图谱展示一体完成</div>
              </div>
              <div className="stat-card">
                <div className="text-sm text-slate-500">适用场景</div>
                <div className="mt-2 text-2xl font-semibold text-slate-950">文档分析</div>
                <div className="mt-2 text-sm text-slate-600">支持火灾调查报告结构化处理</div>
              </div>
              <div className="stat-card">
                <div className="text-sm text-slate-500">交互结果</div>
                <div className="mt-2 text-2xl font-semibold text-slate-950">图谱洞察</div>
                <div className="mt-2 text-sm text-slate-600">聚焦风险因果链与节点关联关系</div>
              </div>
            </div>
          </div>

          <div className="surface-panel rounded-[2rem] p-6 sm:p-8">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-900 text-white">
                <Flame className="h-5 w-5" />
              </div>
              <div>
                <div className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">快速流程</div>
                <div className="mt-1 text-xl font-semibold text-slate-950">从文档到图谱</div>
              </div>
            </div>

            <div className="mt-6 space-y-4">
              {workflow.map((item, index) => (
                <div key={item} className="flex gap-4 rounded-2xl border border-slate-900/8 bg-white/60 p-4">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary-700 text-sm font-semibold text-white">
                    {index + 1}
                  </div>
                  <div className="text-sm leading-7 text-slate-700">{item}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="app-shell pb-10 sm:pb-14 lg:pb-16">
        <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
          <div className="surface-panel rounded-[2rem] p-6 sm:p-8">
            <span className="eyebrow">能力亮点</span>
            <div className="mt-5 grid gap-4">
              {highlights.map(({ title, description, icon: Icon }) => (
                <div key={title} className="rounded-3xl border border-slate-900/8 bg-white/65 p-5">
                  <div className="flex items-center gap-3">
                    <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-amber-100 text-primary-700">
                      <Icon className="h-5 w-5" />
                    </div>
                    <h2 className="text-lg font-semibold text-slate-950">{title}</h2>
                  </div>
                  <p className="mt-3 text-sm leading-7 text-slate-600">{description}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="grid gap-6 sm:grid-cols-2">
            {quickActions.map(({ title, description, href, label, icon: Icon }) => (
              <Link
                key={title}
                href={href}
                className="surface-panel group rounded-[2rem] p-6 transition duration-200 hover:-translate-y-1 hover:bg-white/85"
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-900 text-white">
                  <Icon className="h-5 w-5" />
                </div>
                <h2 className="mt-5 text-xl font-semibold text-slate-950">{title}</h2>
                <p className="mt-3 text-sm leading-7 text-slate-600">{description}</p>
                <div className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-primary-700">
                  {label}
                  <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>
    </Layout>
  )
}
