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
    // 验证文件类型
    const allowedTypes = ['.pdf', '.docx', '.doc', '.txt']
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
    
    if (!allowedTypes.includes(fileExtension)) {
      const errorMsg = `不支持的文件类型: ${fileExtension}。支持的格式: ${allowedTypes.join(', ')}`
      setError(errorMsg)
      onUploadError?.(errorMsg)
      return
    }

    // 验证文件大小 (50MB)
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

      const response = await axios.post('http://localhost:8000/api/v1/documents/process', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 120000, // 2分钟超时
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
      
      if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail
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
    <div style={{ width: '100%', maxWidth: '48rem', margin: '0 auto' }}>
      {/* 上传区域 */}
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
            <Loader2 style={{
              width: '3rem',
              height: '3rem',
              color: 'rgba(251, 146, 60, 1)',
              animation: 'spin 1s linear infinite',
              marginBottom: '1rem',
            }} />
            <p style={{
              fontSize: '1.125rem',
              fontWeight: '600',
              color: 'white',
              marginBottom: '0.5rem',
            }}>
              正在处理文档...
            </p>
            <p style={{
              fontSize: '0.875rem',
              color: 'rgba(255, 255, 255, 0.8)',
            }}>
              正在解析文档并提取事件链，请稍候
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <div style={{
              width: '4rem',
              height: '4rem',
              borderRadius: '50%',
              backgroundColor: 'rgba(251, 146, 60, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1.5rem',
            }}>
              <Upload style={{
                width: '2rem',
                height: '2rem',
                color: 'rgba(251, 146, 60, 1)',
              }} />
            </div>
            <p style={{
              fontSize: '1.25rem',
              fontWeight: '600',
              color: 'white',
              marginBottom: '0.75rem',
            }}>
              拖拽文件到此处或点击上传
            </p>
            <p style={{
              fontSize: '0.875rem',
              color: 'rgba(255, 255, 255, 0.8)',
              marginBottom: '1.5rem',
            }}>
              支持 PDF、Word 文档和文本文件，最大 50MB
            </p>
            <div style={{
              display: 'inline-block',
              backgroundColor: 'rgba(251, 146, 60, 0.9)',
              color: 'white',
              padding: '0.75rem 2rem',
              borderRadius: '0.5rem',
              border: '1px solid rgba(255, 255, 255, 0.3)',
              fontWeight: '600',
              fontSize: '1rem',
              pointerEvents: 'none',
            }}>
              选择文件
            </div>
          </div>
        )}
      </div>

      {/* 错误信息 */}
      {error && (
        <div style={{
          marginTop: '1rem',
          padding: '1rem',
          backgroundColor: 'rgba(239, 68, 68, 0.15)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: '0.75rem',
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
          }}>
            <AlertCircle style={{
              width: '1.25rem',
              height: '1.25rem',
              color: '#fca5a5',
              marginRight: '0.75rem',
            }} />
            <p style={{
              fontSize: '0.875rem',
              color: '#fca5a5',
              flex: 1,
            }}>
              {error}
            </p>
            <button
              onClick={resetUpload}
              style={{
                color: '#fca5a5',
                cursor: 'pointer',
                backgroundColor: 'transparent',
                border: 'none',
                padding: '0.25rem',
              }}
            >
              <X style={{ width: '1rem', height: '1rem' }} />
            </button>
          </div>
        </div>
      )}

      {/* 成功结果 */}
      {uploadResult && (
        <div style={{
          marginTop: '1rem',
          padding: '1rem',
          backgroundColor: 'rgba(34, 197, 94, 0.15)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          border: '1px solid rgba(34, 197, 94, 0.3)',
          borderRadius: '0.75rem',
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'flex-start',
          }}>
            <CheckCircle style={{
              width: '1.25rem',
              height: '1.25rem',
              color: '#86efac',
              marginRight: '0.75rem',
              marginTop: '0.125rem',
            }} />
            <div style={{ flex: 1 }}>
              <p style={{
                fontSize: '0.875rem',
                fontWeight: '600',
                color: '#86efac',
                marginBottom: '0.75rem',
              }}>
                文档处理成功！
              </p>
              <div style={{
                fontSize: '0.875rem',
                color: 'rgba(255, 255, 255, 0.9)',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.5rem',
              }}>
                <p>📄 文件: {uploadResult.filename}</p>
                <p>🆔 文档ID: {uploadResult.document_id}</p>
                {uploadResult.event_chains && (
                  <p>🔗 提取事件链: {uploadResult.event_chains.count} 个</p>
                )}
                {uploadResult.processing_statistics && (
                  <div style={{
                    marginTop: '0.5rem',
                    fontSize: '0.75rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.25rem',
                  }}>
                    <p>📊 验证通过率: {(uploadResult.processing_statistics.validation_rate * 100).toFixed(1)}%</p>
                    <p>🎯 平均置信度: {uploadResult.processing_statistics.avg_confidence.toFixed(2)}</p>
                  </div>
                )}
              </div>
            </div>
            <button
              onClick={resetUpload}
              style={{
                color: '#86efac',
                cursor: 'pointer',
                backgroundColor: 'transparent',
                border: 'none',
                padding: '0.25rem',
              }}
            >
              <X style={{ width: '1rem', height: '1rem' }} />
            </button>
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}
