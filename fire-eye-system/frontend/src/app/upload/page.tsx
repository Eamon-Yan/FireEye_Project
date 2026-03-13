'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, FileText, TrendingUp, Home, Eye } from 'lucide-react'
import FileUpload from '@/components/FileUpload'

export default function UploadPage() {
  const router = useRouter()
  const [uploadResult, setUploadResult] = useState<any>(null)

  const handleUploadSuccess = (result: any) => {
    setUploadResult(result)
  }

  const handleUploadError = (error: string) => {
    console.error('Upload error:', error)
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      position: 'relative',
    }}>
      {/* 顶部导航栏 */}
      <div style={{
        position: 'sticky',
        top: 0,
        zIndex: 10,
        backgroundColor: 'rgba(255, 255, 255, 0.15)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.2)',
      }}>
        <div style={{
          maxWidth: '80rem',
          margin: '0 auto',
          padding: '0 1.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          height: '4rem',
        }}>
          <button
            onClick={() => router.push('/')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              color: 'white',
              backgroundColor: 'rgba(255, 255, 255, 0.2)',
              border: '1px solid rgba(255, 255, 255, 0.3)',
              borderRadius: '0.5rem',
              padding: '0.5rem 1rem',
              cursor: 'pointer',
              transition: 'all 0.2s',
              fontWeight: '500',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.3)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.2)'
            }}
          >
            <Home style={{ width: '1.25rem', height: '1.25rem' }} />
            返回主页
          </button>
          
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
          }}>
            <span style={{ fontSize: '1.5rem' }}>🔥</span>
            <h1 style={{
              fontSize: '1.5rem',
              fontWeight: 'bold',
              color: 'white',
              margin: 0,
            }}>
              文档上传
            </h1>
          </div>

          <button
            onClick={() => router.push('/graph')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              color: 'white',
              backgroundColor: 'rgba(251, 146, 60, 0.9)',
              border: '1px solid rgba(255, 255, 255, 0.3)',
              borderRadius: '0.5rem',
              padding: '0.5rem 1rem',
              cursor: 'pointer',
              transition: 'all 0.2s',
              fontWeight: '500',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(251, 146, 60, 1)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(251, 146, 60, 0.9)'
            }}
          >
            <Eye style={{ width: '1.25rem', height: '1.25rem' }} />
            查看图谱
          </button>
        </div>
      </div>

      {/* 主内容区域 */}
      <div style={{
        maxWidth: '64rem',
        margin: '0 auto',
        padding: '3rem 1.5rem',
      }}>
        {/* 页面标题 */}
        <div style={{
          textAlign: 'center',
          marginBottom: '3rem',
        }}>
          <h1 style={{
            fontSize: '2.25rem',
            fontWeight: 'bold',
            color: 'white',
            marginBottom: '1rem',
          }}>
            上传火灾调查报告
          </h1>
          <p style={{
            fontSize: '1.125rem',
            color: 'rgba(255, 255, 255, 0.9)',
          }}>
            上传您的火灾调查报告，系统将自动提取事件链并构建事理图谱
          </p>
        </div>

        {/* 上传组件 */}
        <div style={{ marginBottom: '2rem' }}>
          <FileUpload
            onUploadSuccess={handleUploadSuccess}
            onUploadError={handleUploadError}
          />
        </div>

        {/* 处理结果 */}
        {uploadResult && (
          <div style={{
            backgroundColor: 'rgba(255, 255, 255, 0.15)',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            borderRadius: '1rem',
            padding: '2rem',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
          }}>
            <h2 style={{
              fontSize: '1.5rem',
              fontWeight: '600',
              color: 'white',
              marginBottom: '1.5rem',
            }}>
              处理结果
            </h2>
            
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(20rem, 1fr))',
              gap: '1.5rem',
              marginBottom: '1.5rem',
            }}>
              {/* 文档信息 */}
              <div style={{
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                borderRadius: '0.75rem',
                padding: '1.5rem',
                border: '1px solid rgba(255, 255, 255, 0.2)',
              }}>
                <h3 style={{
                  fontWeight: '600',
                  color: 'white',
                  marginBottom: '1rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                }}>
                  <FileText style={{ width: '1.25rem', height: '1.25rem' }} />
                  文档信息
                </h3>
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem',
                  fontSize: '0.875rem',
                  color: 'rgba(255, 255, 255, 0.9)',
                }}>
                  <div>
                    <span style={{ fontWeight: '500' }}>文件名: </span>
                    {uploadResult.filename}
                  </div>
                  <div>
                    <span style={{ fontWeight: '500' }}>文档ID: </span>
                    {uploadResult.document_id}
                  </div>
                  <div>
                    <span style={{ fontWeight: '500' }}>文件类型: </span>
                    {uploadResult.file_type}
                  </div>
                  <div>
                    <span style={{ fontWeight: '500' }}>章节数量: </span>
                    {uploadResult.document_sections?.section_count || 0}
                  </div>
                </div>
              </div>

              {/* 处理统计 */}
              {uploadResult.processing_statistics && (
                <div style={{
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  borderRadius: '0.75rem',
                  padding: '1.5rem',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                }}>
                  <h3 style={{
                    fontWeight: '600',
                    color: 'white',
                    marginBottom: '1rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                  }}>
                    <TrendingUp style={{ width: '1.25rem', height: '1.25rem' }} />
                    处理统计
                  </h3>
                  <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.75rem',
                    fontSize: '0.875rem',
                    color: 'rgba(255, 255, 255, 0.9)',
                  }}>
                    <div>
                      <span style={{ fontWeight: '500' }}>原始事件链: </span>
                      {uploadResult.processing_statistics.raw_chains}
                    </div>
                    <div>
                      <span style={{ fontWeight: '500' }}>有效事件链: </span>
                      {uploadResult.processing_statistics.valid_chains}
                    </div>
                    <div>
                      <span style={{ fontWeight: '500' }}>验证通过率: </span>
                      {(uploadResult.processing_statistics.validation_rate * 100).toFixed(1)}%
                    </div>
                    <div>
                      <span style={{ fontWeight: '500' }}>平均置信度: </span>
                      {uploadResult.processing_statistics.avg_confidence.toFixed(2)}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* 事件链列表 */}
            {uploadResult.event_chains && uploadResult.event_chains.chains && (
              <div style={{ marginBottom: '1.5rem' }}>
                <h3 style={{
                  fontWeight: '600',
                  color: 'white',
                  marginBottom: '1rem',
                }}>
                  提取的事件链 ({uploadResult.event_chains.count} 个)
                </h3>
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem',
                  maxHeight: '24rem',
                  overflowY: 'auto',
                }}>
                  {uploadResult.event_chains.chains.slice(0, 10).map((chain: any, index: number) => (
                    <div key={index} style={{
                      backgroundColor: 'rgba(255, 255, 255, 0.1)',
                      borderRadius: '0.75rem',
                      padding: '1rem',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                    }}>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        flexWrap: 'wrap',
                        gap: '0.5rem',
                      }}>
                        <div style={{ flex: 1, minWidth: '20rem' }}>
                          <div style={{ fontSize: '0.875rem', color: 'white' }}>
                            <span style={{ fontWeight: '600', color: '#f43f5e' }}>{chain.source}</span>
                            <span style={{ margin: '0 0.5rem', color: 'rgba(255, 255, 255, 0.7)' }}>
                              → {chain.relation} →
                            </span>
                            <span style={{ fontWeight: '600', color: '#a78bfa' }}>{chain.target}</span>
                          </div>
                          {chain.context && (
                            <p style={{
                              fontSize: '0.75rem',
                              color: 'rgba(255, 255, 255, 0.7)',
                              marginTop: '0.5rem',
                            }}>
                              {chain.context}
                            </p>
                          )}
                        </div>
                        <div>
                          <span style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            padding: '0.25rem 0.75rem',
                            borderRadius: '9999px',
                            fontSize: '0.75rem',
                            fontWeight: '600',
                            backgroundColor: 'rgba(251, 146, 60, 0.9)',
                            color: 'white',
                          }}>
                            {(chain.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                  {uploadResult.event_chains.chains.length > 10 && (
                    <p style={{
                      fontSize: '0.875rem',
                      color: 'rgba(255, 255, 255, 0.7)',
                      textAlign: 'center',
                    }}>
                      还有 {uploadResult.event_chains.chains.length - 10} 个事件链...
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* 操作按钮 */}
            <div style={{
              display: 'flex',
              justifyContent: 'center',
              gap: '1rem',
              flexWrap: 'wrap',
            }}>
              <button
                onClick={() => router.push('/graph')}
                style={{
                  backgroundColor: 'rgba(251, 146, 60, 0.9)',
                  color: 'white',
                  padding: '0.75rem 2rem',
                  borderRadius: '0.5rem',
                  border: '1px solid rgba(255, 255, 255, 0.3)',
                  cursor: 'pointer',
                  fontWeight: '600',
                  fontSize: '1rem',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'rgba(251, 146, 60, 1)'
                  e.currentTarget.style.transform = 'translateY(-2px)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'rgba(251, 146, 60, 0.9)'
                  e.currentTarget.style.transform = 'translateY(0)'
                }}
              >
                查看图谱
              </button>
              <button
                onClick={() => setUploadResult(null)}
                style={{
                  backgroundColor: 'rgba(255, 255, 255, 0.2)',
                  color: 'white',
                  padding: '0.75rem 2rem',
                  borderRadius: '0.5rem',
                  border: '1px solid rgba(255, 255, 255, 0.3)',
                  cursor: 'pointer',
                  fontWeight: '600',
                  fontSize: '1rem',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.3)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.2)'
                }}
              >
                继续上传
              </button>
            </div>
          </div>
        )}

        {/* 使用说明 */}
        <div style={{
          marginTop: '3rem',
          backgroundColor: 'rgba(255, 255, 255, 0.15)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          borderRadius: '1rem',
          padding: '2rem',
          border: '1px solid rgba(255, 255, 255, 0.2)',
        }}>
          <h2 style={{
            fontSize: '1.25rem',
            fontWeight: '600',
            color: 'white',
            marginBottom: '1.5rem',
          }}>
            使用说明
          </h2>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(20rem, 1fr))',
            gap: '2rem',
            fontSize: '0.875rem',
            color: 'rgba(255, 255, 255, 0.9)',
          }}>
            <div>
              <h3 style={{
                fontWeight: '600',
                marginBottom: '0.75rem',
                color: 'white',
              }}>
                支持的文件格式
              </h3>
              <ul style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '0.5rem',
                paddingLeft: '1.25rem',
              }}>
                <li>PDF 文档 (.pdf)</li>
                <li>Word 文档 (.docx, .doc)</li>
                <li>纯文本文件 (.txt)</li>
              </ul>
            </div>
            <div>
              <h3 style={{
                fontWeight: '600',
                marginBottom: '0.75rem',
                color: 'white',
              }}>
                处理流程
              </h3>
              <ul style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '0.5rem',
                paddingLeft: '1.25rem',
              }}>
                <li>文档解析和章节提取</li>
                <li>LLM 智能事件链抽取</li>
                <li>术语归一化和逻辑校验</li>
                <li>存储到 Neo4j 图数据库</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
