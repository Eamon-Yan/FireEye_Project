'use client'

import React, { useState, useCallback } from 'react'
import { Upload, X, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import axios from 'axios'

interface FileUploadProps {
  onUploadSuccess?: (result: any) => void
  onUploadError?: (error: string) => void
  className?: string
}

interface UploadResult {
  document_id: string
  filename: string
  file_type: string
  event_chains?: {
    count: number
    chains: Array<{
      source: string
      relation: string
      target: string
      confidence: number
    }>
  }
  processing_statistics?: {
    raw_chains: number
    valid_chains: number
    validation_rate: number
    avg_confidence: number
  }
  document_sections?: {
    section_count: number
  }
}

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, '')
const DOCUMENT_PROCESS_ENDPOINT = API_BASE_URL
  ? `${API_BASE_URL}/api/v1/documents/process`
  : '/api/v1/documents/process'

export default function FileUpload({ onUploadSuccess, onUploadError, className }: FileUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)

    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0 && files[0]) {
      handleFileUpload(files[0])
    }
  }, [])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0 && files[0]) {
      handleFileUpload(files[0])
    }
  }, [])

  const handleFileUpload = async (file: File) => {
    const allowedTypes = ['.pdf', '.docx', '.doc', '.txt']
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()

    if (!allowedTypes.includes(fileExtension)) {
      const errorMsg = `不支持的文件类型: ${fileExtension}。支持的格式: ${allowedTypes.join(', ')}`
      setError(errorMsg)
      onUploadError?.(errorMsg)
      return
    }

    const maxSize = 50 * 1024 * 1024
    if (file.size > maxSize) {
      const errorMsg = `文件大小超过限制 (${Math.round(maxSize / 1024 / 1024)}MB)`
      setError(errorMsg)
      onUploadError?.(errorMsg)
      return
    }

    setIsUploading(true)
    setError(null)
    setUploadResult(null)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('apply_validation', 'true')
      formData.append('save_to_graph', 'true')

      const response = await axios.post(DOCUMENT_PROCESS_ENDPOINT, formData, {
        timeout: 120000,
      })

      if (response.data.status === 'success') {
        const result = response.data.data
        setUploadResult(result)
        onUploadSuccess?.(result)
      } else {
        throw new Error(response.data.message || '上传处理失败')
      }
      } catch (err: any) {
        let errorMessage = '上传失败'

        if (err.code === 'ECONNABORTED') {
          errorMessage = '上传超时，请稍后重试'
        } else if (err.response?.data?.detail) {
          errorMessage = Array.isArray(err.response.data.detail)
            ? err.response.data.detail.map((item: any) => item.msg || JSON.stringify(item)).join('；')
            : err.response.data.detail
        } else if (err.request && !err.response) {
          errorMessage = '无法连接到后端服务，请检查后端是否已启动'
        } else if (err.message) {
          errorMessage = err.message
        }
setError(errorMessage)
      onUploadError?.(errorMessage)
    } finally {
      setIsUploading(false)
    }
  }

  const resetUpload = () => {
    setUploadResult(null)
    setError(null)
  }

  return (
    <div style={{ width: '100%', maxWidth: '48rem', margin: '0 auto' }} className={className}>
      <div
        style={{
          position: 'relative',
          border: isDragOver ? '2px dashed rgba(251, 146, 60, 0.8)' : '2px dashed rgba(255, 255, 255, 0.4)',
          borderRadius: '1rem',
          padding: '3rem 2rem',
          textAlign: 'center',
          transition: 'all 0.3s',
          backgroundColor: isDragOver
            ? 'rgba(251, 146, 60, 0.1)'
            : isUploading
              ? 'rgba(255, 255, 255, 0.1)'
              : 'rgba(255, 255, 255, 0.15)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          cursor: isUploading ? 'not-allowed' : 'pointer',
        }}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          type="file"
          accept=".pdf,.docx,.doc,.txt"
          onChange={handleFileSelect}
          style={{
            position: 'absolute',
            inset: 0,
            width: '100%',
            height: '100%',
            opacity: 0,
            cursor: isUploading ? 'not-allowed' : 'pointer',
          }}
          disabled={isUploading}
        />

        {isUploading ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <Loader2
              style={{
                width: '3rem',
                height: '3rem',
                color: 'rgba(251, 146, 60, 1)',
                animation: 'spin 1s linear infinite',
                marginBottom: '1rem',
              }}
            />
            <p
              style={{
                fontSize: '1.125rem',
                fontWeight: '600',
                color: 'white',
                marginBottom: '0.5rem',
              }}
            >
              正在处理文档...
            </p>
            <p
              style={{
                fontSize: '0.875rem',
                color: 'rgba(255, 255, 255, 0.8)',
              }}
            >
              正在解析文档并提取事件链，请稍候
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <div
              style={{
                width: '4rem',
                height: '4rem',
                borderRadius: '50%',
                backgroundColor: 'rgba(251, 146, 60, 0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '1.5rem',
              }}
            >
              <Upload
                style={{
                  width: '2rem',
                  height: '2rem',
                  color: 'rgba(251, 146, 60, 1)',
                }}
              />
            </div>
            <p
              style={{
                fontSize: '1.25rem',
                fontWeight: '600',
                color: 'white',
                marginBottom: '0.5rem',
              }}
            >
              拖拽文件到此处或点击上传
            </p>
            <p
              style={{
                fontSize: '0.875rem',
                color: 'rgba(255, 255, 255, 0.8)',
                marginBottom: '1rem',
              }}
            >
              支持 PDF、DOCX、DOC、TXT 格式，最大 50MB
            </p>
          </div>
        )}
      </div>

      {error && (
        <div
          style={{
            marginTop: '1.5rem',
            padding: '1rem 1.25rem',
            borderRadius: '0.75rem',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.2)',
            backdropFilter: 'blur(10px)',
            WebkitBackdropFilter: 'blur(10px)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
          }}
        >
          <AlertCircle
            style={{
              width: '1.25rem',
              height: '1.25rem',
              color: 'rgba(248, 113, 113, 1)',
              flexShrink: 0,
            }}
          />
          <p
            style={{
              color: 'rgba(254, 202, 202, 1)',
              fontSize: '0.875rem',
              margin: 0,
            }}
          >
            {error}
          </p>
        </div>
      )}

      {uploadResult && (
        <div
          style={{
            marginTop: '1.5rem',
            padding: '1.5rem',
            borderRadius: '1rem',
            backgroundColor: 'rgba(34, 197, 94, 0.1)',
            border: '1px solid rgba(34, 197, 94, 0.2)',
            backdropFilter: 'blur(10px)',
            WebkitBackdropFilter: 'blur(10px)',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '1rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <CheckCircle
                style={{
                  width: '1.5rem',
                  height: '1.5rem',
                  color: 'rgba(34, 197, 94, 1)',
                }}
              />
              <h3
                style={{
                  color: 'white',
                  fontSize: '1.125rem',
                  fontWeight: '600',
                  margin: 0,
                }}
              >
                文档处理成功
              </h3>
            </div>
            <button
              onClick={resetUpload}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'rgba(255, 255, 255, 0.6)',
                cursor: 'pointer',
                padding: '0.25rem',
                borderRadius: '0.375rem',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)'
                e.currentTarget.style.color = 'white'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent'
                e.currentTarget.style.color = 'rgba(255, 255, 255, 0.6)'
              }}
            >
              <X style={{ width: '1.25rem', height: '1.25rem' }} />
            </button>
          </div>

          <div
            style={{
              display: 'grid',
              gap: '0.75rem',
              fontSize: '0.875rem',
              color: 'rgba(255, 255, 255, 0.9)',
            }}
          >
            <div>
              <span style={{ fontWeight: '600' }}>文档ID:</span> {uploadResult.document_id}
            </div>
            <div>
              <span style={{ fontWeight: '600' }}>文件名:</span> {uploadResult.filename}
            </div>
            <div>
              <span style={{ fontWeight: '600' }}>文件类型:</span> {uploadResult.file_type.toUpperCase()}
            </div>
            {uploadResult.event_chains && (
              <div>
                <span style={{ fontWeight: '600' }}>提取事件链:</span> {uploadResult.event_chains.count} 个
              </div>
            )}
            {uploadResult.document_sections && (
              <div>
                <span style={{ fontWeight: '600' }}>文档章节:</span> {uploadResult.document_sections.section_count} 个
              </div>
            )}
            {uploadResult.processing_statistics && (
              <>
                <div>
                  <span style={{ fontWeight: '600' }}>原始事件链:</span> {uploadResult.processing_statistics.raw_chains} 个
                </div>
                <div>
                  <span style={{ fontWeight: '600' }}>有效事件链:</span> {uploadResult.processing_statistics.valid_chains} 个
                </div>
                <div>
                  <span style={{ fontWeight: '600' }}>验证通过率:</span> {(uploadResult.processing_statistics.validation_rate * 100).toFixed(1)}%
                </div>
                <div>
                  <span style={{ fontWeight: '600' }}>平均置信度:</span> {uploadResult.processing_statistics.avg_confidence.toFixed(2)}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
