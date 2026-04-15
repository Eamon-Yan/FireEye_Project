'use client'

import { useCallback, useEffect, useId, useMemo, useState, useRef } from 'react'
import { AlertCircle, CheckCircle, Loader2, Upload, X } from 'lucide-react'
import axios from 'axios'
import type { UploadResult } from '@/types/upload'

interface FileUploadProps {
  onUploadSuccess?: (result: UploadResult) => void
  onUploadError?: (error: string) => void
  className?: string
}

interface TaskStatus {
  document_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  stage: string
  message: string
  progress: number
  result?: UploadResult
  error?: string
}

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, '')
const DOCUMENT_PROCESS_ENDPOINT = `${API_BASE_URL}/api/v1/documents/process`
const GET_STATUS_ENDPOINT = (id: string) => `${API_BASE_URL}/api/v1/documents/status/${id}`

export default function FileUpload({ onUploadSuccess, onUploadError, className }: FileUploadProps) {
  const inputId = useId()
  const [isDragOver, setIsDragOver] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadStage, setUploadStage] = useState('')
  const [progress, setProgress] = useState(0)
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  
  const pollTimerRef = useRef<NodeJS.Timeout | null>(null)

  const stopPolling = useCallback(() => {
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current)
      pollTimerRef.current = null
    }
  }, [])

  useEffect(() => {
    return () => stopPolling()
  }, [stopPolling])

  const pollTaskStatus = useCallback((documentId: string) => {
    stopPolling()
    
    pollTimerRef.current = setInterval(async () => {
      try {
        const response = await axios.get(GET_STATUS_ENDPOINT(documentId))
        if (response.data.status === 'success') {
          const task = response.data.data as TaskStatus
          
          setUploadStage(task.message)
          setProgress(task.progress)

          if (task.status === 'completed') {
            stopPolling()
            setIsUploading(false)
            if (task.result) {
              setUploadResult(task.result)
              onUploadSuccess?.(task.result)
            }
          } else if (task.status === 'failed') {
            stopPolling()
            setIsUploading(false)
            setError(task.message || '任务执行失败')
            onUploadError?.(task.message || '任务执行失败')
          }
        }
      } catch (err) {
        console.error('Polling error:', err)
      }
    }, 2000)
  }, [onUploadError, onUploadSuccess, stopPolling])

  const uploadMetrics = useMemo(() => {
    if (!uploadResult?.processing_statistics) {
      return []
    }

    return [
      {
        label: '原始事件链',
        value: `${uploadResult.processing_statistics.raw_chains}`,
      },
      {
        label: '有效事件链',
        value: `${uploadResult.processing_statistics.valid_chains}`,
      },
      {
        label: '验证通过率',
        value: `${(uploadResult.processing_statistics.validation_rate * 100).toFixed(1)}%`,
      },
      {
        label: '平均置信度',
        value: uploadResult.processing_statistics.avg_confidence.toFixed(2),
      },
    ]
  }, [uploadResult])

  const handleDragOver = useCallback((event: React.DragEvent<HTMLLabelElement>) => {
    event.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((event: React.DragEvent<HTMLLabelElement>) => {
    event.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((event: React.DragEvent<HTMLLabelElement>) => {
    event.preventDefault()
    setIsDragOver(false)

    const file = event.dataTransfer.files?.[0]
    if (file) {
      void handleFileUpload(file)
    }
  }, [])

  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      void handleFileUpload(file)
      event.target.value = ''
    }
  }, [])

  const handleFileUpload = async (file: File) => {
    const allowedTypes = ['.pdf', '.docx', '.txt']
    const fileExtension = `.${file.name.split('.').pop()?.toLowerCase()}`

    if (!allowedTypes.includes(fileExtension)) {
      const errorMessage = `不支持的文件类型: ${fileExtension}。支持格式: ${allowedTypes.join(', ')}`
      setError(errorMessage)
      onUploadError?.(errorMessage)
      return
    }

    const maxSize = 50 * 1024 * 1024
    if (file.size > maxSize) {
      const errorMessage = `文件大小超过限制 (${Math.round(maxSize / 1024 / 1024)}MB)`
      setError(errorMessage)
      onUploadError?.(errorMessage)
      return
    }

    setIsUploading(true)
    setError(null)
    setUploadResult(null)
    setProgress(5)
    setUploadStage('正在上传文档...')

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('apply_validation', 'true')
      formData.append('save_to_graph', 'true')

      const response = await axios.post(DOCUMENT_PROCESS_ENDPOINT, formData)

      if (response.data.status !== 'success') {
        throw new Error(response.data.message || '上传处理失败')
      }

      const { document_id } = response.data.data
      pollTaskStatus(document_id)
      
    } catch (requestError) {
      setIsUploading(false)
      let errorMessage = '上传失败'
      if (axios.isAxiosError(requestError)) {
        if (requestError.code === 'ECONNABORTED') {
          errorMessage = '上传超时，请稍后重试'
        } else if (requestError.response?.data?.detail) {
          const detail = requestError.response.data.detail
          errorMessage = Array.isArray(detail)
            ? detail.map((item: { msg?: string }) => item.msg || JSON.stringify(item)).join('；')
            : String(detail)
        } else if (requestError.request && !requestError.response) {
          errorMessage = '无法连接到后端服务，请确认后端接口已启动'
        } else if (requestError.message) {
          errorMessage = requestError.message
        }
      } else if (requestError instanceof Error) {
        errorMessage = requestError.message
      }

      setError(errorMessage)
      onUploadError?.(errorMessage)
    }
  }

  const resetUpload = () => {
    setUploadResult(null)
    setError(null)
    stopPolling()
  }

  return (
    <div className={className}>
      <div className="surface-panel-strong rounded-[2rem] p-5 sm:p-6">
        <div className="mb-5 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <span className="eyebrow">Document Intake</span>
            <h2 className="mt-3 text-2xl font-semibold text-slate-950">上传调查文档</h2>
            <p className="mt-2 text-sm leading-7 text-slate-600">
              支持 PDF、DOCX、TXT。后台异步执行抽取任务，支持真实进度追踪。
            </p>
          </div>
          <div className="rounded-full border border-slate-900/10 bg-white/70 px-4 py-2 text-xs font-medium uppercase tracking-[0.18em] text-slate-500">
            最大 50MB
          </div>
        </div>

        <label
          htmlFor={inputId}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`block rounded-[1.75rem] border-2 border-dashed px-6 py-10 text-center transition duration-200 ${
            isDragOver
              ? 'border-primary-700 bg-orange-50/70'
              : isUploading
                ? 'border-slate-300 bg-white/55'
                : 'border-slate-300 bg-white/70 hover:border-primary-700 hover:bg-white/85'
          } ${isUploading ? 'cursor-progress' : 'cursor-pointer'}`}
        >
          <input
            id={inputId}
            type="file"
            accept=".pdf,.docx,.txt"
            className="sr-only"
            onChange={handleFileSelect}
            disabled={isUploading}
          />

          <div className="mx-auto flex max-w-xl flex-col items-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-orange-100 text-primary-700 shadow-inner shadow-orange-200/80">
              {isUploading ? <Loader2 className="h-7 w-7 animate-spin" /> : <Upload className="h-7 w-7" />}
            </div>
            <div className="mt-5 text-xl font-semibold text-slate-950">
              {isUploading ? uploadStage || '正在处理任务...' : '拖拽文件到这里，或点击选择文件'}
            </div>
            
            {isUploading && (
              <div className="mt-6 w-full max-w-sm">
                <div className="flex justify-between mb-2">
                  <span className="text-xs font-medium text-slate-500">任务进度</span>
                  <span className="text-xs font-bold text-primary-700">{progress}%</span>
                </div>
                <div className="h-2 w-full bg-slate-200 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-primary-600 to-accent-500 transition-all duration-500" 
                    style={{ width: `${progress}%` }} 
                  />
                </div>
              </div>
            )}

            <p className="mt-3 max-w-lg text-sm leading-7 text-slate-600">
              {isUploading
                ? '处理时间取决于文档规模。您可以等待任务完成，或稍后刷新状态。'
                : '上传后将依次执行文档解析、事件链抽取、术语校验与图谱入库。'}
            </p>
          </div>
        </label>

        {error && (
          <div className="mt-5 flex items-start gap-3 rounded-[1.5rem] border border-red-200 bg-red-50 px-5 py-4 text-red-700">
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
            <div>
              <div className="text-sm font-semibold">任务异常</div>
              <p className="mt-1 text-sm leading-7">{error}</p>
            </div>
          </div>
        )}

        {uploadResult && (
          <div className="mt-5 rounded-[1.75rem] border border-emerald-200 bg-emerald-50/90 p-5 sm:p-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div className="flex items-start gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-600 text-white">
                  <CheckCircle className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-slate-950">文档处理成功</h3>
                  <p className="mt-1 text-sm leading-7 text-slate-600">
                    后台任务已执行完毕，提取结果已同步至图数据库。
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={resetUpload}
                className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-slate-900/10 bg-white/70 text-slate-500 transition hover:bg-white hover:text-slate-900"
                aria-label="清除当前上传结果"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <div className="stat-card">
                <div className="text-sm text-slate-500">文档 ID</div>
                <div className="mt-2 break-all text-sm font-semibold text-slate-900">{uploadResult.document_id}</div>
              </div>
              <div className="stat-card">
                <div className="text-sm text-slate-500">文件类型</div>
                <div className="mt-2 text-xl font-semibold text-slate-950">{uploadResult.file_type.toUpperCase()}</div>
              </div>
              <div className="stat-card">
                <div className="text-sm text-slate-500">提取事件链</div>
                <div className="mt-2 text-3xl font-semibold text-slate-950">{uploadResult.event_chains?.count ?? 0}</div>
              </div>
              <div className="stat-card">
                <div className="text-sm text-slate-500">文档章节</div>
                <div className="mt-2 text-3xl font-semibold text-slate-950">{uploadResult.document_sections?.section_count ?? 0}</div>
              </div>
            </div>

            {uploadMetrics.length > 0 && (
              <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                {uploadMetrics.map((item) => (
                  <div key={item.label} className="rounded-3xl border border-slate-900/8 bg-white/75 p-4">
                    <div className="text-sm text-slate-500">{item.label}</div>
                    <div className="mt-2 text-2xl font-semibold text-slate-950">{item.value}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
