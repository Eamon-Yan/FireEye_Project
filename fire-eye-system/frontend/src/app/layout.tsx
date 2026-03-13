import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: '火瞳系统 - 火灾事理图谱分析平台',
  description: '基于Neo4j和LLM的火灾事理图谱Web系统，提供智能抽取、校验对齐和场景预测功能',
  keywords: ['火灾分析', '事理图谱', 'Neo4j', 'LLM', '场景预测'],
  authors: [{ name: 'Fire Eye Team' }],
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>
        <div id="root">
          {children}
        </div>
      </body>
    </html>
  )
}