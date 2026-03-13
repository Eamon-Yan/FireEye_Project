'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Flame, Home, Upload, Network, Search, Settings } from 'lucide-react'
import { clsx } from 'clsx'

interface LayoutProps {
  children: React.ReactNode
}

const navigation = [
  { name: '首页', href: '/', icon: Home },
  { name: '文档上传', href: '/upload', icon: Upload },
  { name: '图谱查看', href: '/graph', icon: Network },
  { name: '场景预测', href: '/prediction', icon: Search },
]

export default function Layout({ children }: LayoutProps) {
  const pathname = usePathname()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航栏 */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            {/* Logo 和主导航 */}
            <div className="flex">
              <Link href="/" className="flex items-center">
                <Flame className="h-8 w-8 text-red-600" />
                <span className="ml-2 text-xl font-bold text-gray-900">火瞳系统</span>
              </Link>
              
              <div className="hidden sm:ml-8 sm:flex sm:space-x-8">
                {navigation.map((item) => {
                  const Icon = item.icon
                  const isActive = pathname === item.href
                  
                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      className={clsx(
                        'inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium',
                        {
                          'border-red-500 text-gray-900': isActive,
                          'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300': !isActive,
                        }
                      )}
                    >
                      <Icon className="h-4 w-4 mr-2" />
                      {item.name}
                    </Link>
                  )
                })}
              </div>
            </div>

            {/* 右侧操作 */}
            <div className="flex items-center space-x-4">
              <button className="text-gray-500 hover:text-gray-700">
                <Settings className="h-5 w-5" />
              </button>
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium text-gray-700">U</span>
                </div>
                <span className="text-sm text-gray-700">用户</span>
              </div>
            </div>
          </div>
        </div>

        {/* 移动端导航 */}
        <div className="sm:hidden">
          <div className="pt-2 pb-3 space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href
              
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={clsx(
                    'block pl-3 pr-4 py-2 border-l-4 text-base font-medium',
                    {
                      'bg-red-50 border-red-500 text-red-700': isActive,
                      'border-transparent text-gray-600 hover:text-gray-800 hover:bg-gray-50 hover:border-gray-300': !isActive,
                    }
                  )}
                >
                  <div className="flex items-center">
                    <Icon className="h-4 w-4 mr-3" />
                    {item.name}
                  </div>
                </Link>
              )
            })}
          </div>
        </div>
      </nav>

      {/* 主要内容区域 */}
      <main className="flex-1">
        {children}
      </main>

      {/* 页脚 */}
      <footer className="bg-white border-t mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <Flame className="h-5 w-5 text-red-600" />
              <span className="text-sm text-gray-600">
                火瞳系统 - 火灾事理图谱分析平台
              </span>
            </div>
            <div className="text-sm text-gray-500">
              © 2024 火瞳系统. 保留所有权利.
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}