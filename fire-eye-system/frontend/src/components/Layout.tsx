'use client'

import type { ReactNode } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Flame, Home, Upload, Network, Menu, X } from 'lucide-react'
import { clsx } from 'clsx'
import { useEffect, useState } from 'react'

interface LayoutProps {
  children: ReactNode
}

const navigation = [
  { name: '总览', href: '/', icon: Home },
  { name: '文档上传', href: '/upload', icon: Upload },
  { name: '关系图谱', href: '/graph', icon: Network },
]

export default function Layout({ children }: LayoutProps) {
  const pathname = usePathname()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    setMobileMenuOpen(false)
  }, [pathname])

  return (
    <div className="relative min-h-screen overflow-hidden">
      <div className="pointer-events-none absolute inset-0 bg-grid-soft opacity-50" />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-64 bg-gradient-to-b from-orange-200/40 via-transparent to-transparent" />

      <header className="sticky top-0 z-40 border-b border-slate-900/10 bg-[rgba(251,248,243,0.82)] backdrop-blur-xl">
        <div className="app-shell">
          <div className="flex h-18 items-center justify-between gap-4 py-4">
            <Link href="/" className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-primary-700 via-primary-600 to-accent-500 text-white shadow-lg shadow-primary-900/15">
                <Flame className="h-5 w-5" />
              </div>
              <div>
                <div className="text-base font-semibold tracking-wide text-slate-900">火瞳系统</div>
                <div className="text-xs uppercase tracking-[0.24em] text-slate-500">Fire Causality Graph</div>
              </div>
            </Link>

            <nav className="hidden items-center gap-2 md:flex">
              {navigation.map((item) => {
                const Icon = item.icon
                const isActive = pathname === item.href

                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={clsx(
                      'inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition',
                      isActive
                        ? 'bg-slate-900 text-white shadow-md shadow-slate-900/15'
                        : 'text-slate-600 hover:bg-white/70 hover:text-slate-900'
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {item.name}
                  </Link>
                )
              })}
            </nav>

            <div className="hidden items-center gap-3 md:flex">
              <div className="rounded-full border border-slate-900/10 bg-white/60 px-4 py-2 text-xs font-medium uppercase tracking-[0.18em] text-slate-600">
                Web Front
              </div>
            </div>

            <button
              type="button"
              aria-label={mobileMenuOpen ? '关闭导航菜单' : '打开导航菜单'}
              className="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-slate-900/10 bg-white/70 text-slate-700 md:hidden"
              onClick={() => setMobileMenuOpen((open) => !open)}
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>

          {mobileMenuOpen && (
            <nav className="grid gap-2 border-t border-slate-900/10 py-4 md:hidden">
              {navigation.map((item) => {
                const Icon = item.icon
                const isActive = pathname === item.href

                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={clsx(
                      'inline-flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition',
                      isActive
                        ? 'bg-slate-900 text-white'
                        : 'bg-white/70 text-slate-700 hover:bg-white'
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {item.name}
                  </Link>
                )
              })}
            </nav>
          )}
        </div>
      </header>

      <main className="app-shell relative z-10">{children}</main>

      <footer className="relative z-10 border-t border-slate-900/10 bg-[rgba(251,248,243,0.72)] backdrop-blur-xl">
        <div className="app-shell flex flex-col gap-3 py-6 text-sm text-slate-600 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <Flame className="h-4 w-4 text-primary-700" />
            <span>火灾事理图谱分析平台，面向文档抽取、校验对齐与图谱展示。</span>
          </div>
          <span>Demo Workspace / Next.js 14</span>
        </div>
      </footer>
    </div>
  )
}
