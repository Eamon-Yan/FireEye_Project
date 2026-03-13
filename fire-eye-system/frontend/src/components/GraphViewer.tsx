'use client'

import React, { useEffect, useState, useCallback } from 'react'
import dynamic from 'next/dynamic'
import { useRouter } from 'next/navigation'
import { Search, Download, RefreshCw, X, Info, Home, Upload } from 'lucide-react'

const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), {
  ssr: false,
})

interface GraphNode {
  id: string
  type: string
  description: string
  properties: Record<string, any>
}

interface GraphLink {
  source: string
  target: string
  relation: string
  confidence?: number
}

interface GraphData {
  nodes: GraphNode[]
  links: GraphLink[]
}

export default function GraphViewer() {
  const router = useRouter()
  const fgRef = React.useRef<any>()
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] })
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [dimensions, setDimensions] = useState({ width: 1920, height: 1080 })
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)

  useEffect(() => {
    console.log('🔥🔥🔥 GLASSMORPHISM GraphViewer v7.0 - NEW LAYOUT + NODE DETAILS! 🔥🔥🔥')
  }, [])

  useEffect(() => {
    const updateDimensions = () => {
      setDimensions({
        width: window.innerWidth,
        height: window.innerHeight,
      })
    }

    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  const fetchGraphData = useCallback(async () => {
    setIsLoading(true)
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'
      const response = await fetch(
        `${apiUrl}/api/v1/graph/query?limit=100&include_relationships=true${
          searchQuery ? `&search_text=${encodeURIComponent(searchQuery)}` : ''
        }`
      )
      const result = await response.json()

      if (result.status === 'success' && result.data) {
        setGraphData(result.data)
      }
    } catch (error) {
      console.error('Failed to fetch graph data:', error)
    } finally {
      setIsLoading(false)
    }
  }, [searchQuery])

  useEffect(() => {
    fetchGraphData()
  }, [fetchGraphData])

  // 配置力导向图参数
  useEffect(() => {
    if (fgRef.current && graphData.nodes.length > 0) {
      const fg = fgRef.current
      
      // 适中的排斥力
      fg.d3Force('charge').strength(-500)
      
      // 缩短链接距离，让连接更紧密
      fg.d3Force('link').distance(80)
      
      // 添加碰撞检测力，防止节点和标签重叠
      fg.d3Force('collide', fg.d3ForceCollide((node: any) => {
        const nodeRadius = node.val || 5
        // 碰撞半径：节点半径 + 标签空间
        return nodeRadius + 35
      }).strength(1).iterations(3))
      
      // 增强向心力，让整体布局更紧凑集中
      fg.d3Force('center', fg.d3ForceCenter(dimensions.width / 2, dimensions.height / 2).strength(0.15))
      
      // 重新加热模拟
      fg.d3ReheatSimulation()
    }
  }, [graphData, dimensions])

  // 新配色方案：深色主题
  const getNodeColor = (node: any): string => {
    const colorMap: Record<string, string> = {
      FireEvent: '#f43f5e',    // 玫瑰红
      Hazard: '#fb923c',       // 琥珀橙
      Consequence: '#a78bfa',  // 紫罗兰
    }
    return colorMap[node.type] || '#64748b'
  }

  const getNodeSize = (node: any): number => {
    const connections = graphData.links.filter(
      (link: any) => link.source === node.id || link.target === node.id
    ).length
    return 5 + Math.min(connections * 2, 15)
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    fetchGraphData()
  }

  const handleExport = () => {
    const dataStr = JSON.stringify(graphData, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `fire-eye-graph-${Date.now()}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  const handleNodeClick = (node: any) => {
    setSelectedNode(node)
  }

  const getConnectedNodes = (nodeId: string) => {
    const connections = graphData.links
      .filter(link => {
        const sourceId = typeof link.source === 'object' ? (link.source as any).id : link.source
        const targetId = typeof link.target === 'object' ? (link.target as any).id : link.target
        return sourceId === nodeId || targetId === nodeId
      })
      .map(link => {
        const sourceId = typeof link.source === 'object' ? (link.source as any).id : link.source
        const targetId = typeof link.target === 'object' ? (link.target as any).id : link.target
        const connectedId = sourceId === nodeId ? targetId : sourceId
        return {
          node: graphData.nodes.find(n => n.id === connectedId),
          relation: link.relation,
          direction: sourceId === nodeId ? 'outgoing' : 'incoming'
        }
      })
      .filter(item => item.node)
    
    // 去重：基于节点ID和关系类型的组合
    const uniqueConnections = connections.reduce((acc, current) => {
      const key = `${current.node?.id}-${current.relation}-${current.direction}`
      if (!acc.some(item => `${item.node?.id}-${item.relation}-${item.direction}` === key)) {
        acc.push(current)
      }
      return acc
    }, [] as typeof connections)
    
    return uniqueConnections
  }

  return (
    <div style={{ 
      width: '100vw', 
      height: '100vh', 
      position: 'relative', 
      overflow: 'hidden',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      {/* 图表背景层 */}
      <div style={{ position: 'absolute', inset: 0, zIndex: 0 }}>
        {!isLoading && (
          <ForceGraph2D
            ref={fgRef}
            width={dimensions.width}
            height={dimensions.height}
            graphData={graphData}
            nodeId="id"
            nodeLabel="description"
            nodeColor={getNodeColor}
            nodeVal={getNodeSize}
            linkSource="source"
            linkTarget="target"
            linkLabel="relation"
            linkColor={() => 'rgba(255, 255, 255, 0.3)'}
            linkWidth={(link: any) => Math.sqrt(link.confidence || 1) * 2}
            linkDirectionalArrowLength={4}
            linkDirectionalArrowRelPos={1}
            enableNodeDrag={true}
            enableZoomInteraction={true}
            enablePanInteraction={true}
            cooldownTicks={200}
            d3AlphaDecay={0.01}
            d3VelocityDecay={0.2}
            warmupTicks={100}
            onNodeClick={handleNodeClick}
            nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
              const label = node.description
              const fontSize = 12 / globalScale
              const nodeRadius = node.val || 5
              const isSelected = selectedNode?.id === node.id

              // 绘制选中高亮
              if (isSelected) {
                ctx.beginPath()
                ctx.arc(node.x, node.y, nodeRadius + 4, 0, 2 * Math.PI, false)
                ctx.fillStyle = 'rgba(255, 255, 255, 0.3)'
                ctx.fill()
              }

              // 绘制节点
              ctx.beginPath()
              ctx.arc(node.x, node.y, nodeRadius, 0, 2 * Math.PI, false)
              ctx.fillStyle = getNodeColor(node)
              ctx.fill()
              ctx.strokeStyle = '#ffffff'
              ctx.lineWidth = isSelected ? 3 / globalScale : 2 / globalScale
              ctx.stroke()

              // 绘制标签
              if (globalScale > 0.5) {
                ctx.font = `${fontSize}px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`
                ctx.textAlign = 'center'
                ctx.textBaseline = 'middle'

                const textWidth = ctx.measureText(label).width
                const labelY = node.y + nodeRadius + fontSize + 4
                const padding = 6
                const borderRadius = 4

                // 绘制标签阴影
                ctx.shadowColor = 'rgba(0, 0, 0, 0.3)'
                ctx.shadowBlur = 4
                ctx.shadowOffsetX = 0
                ctx.shadowOffsetY = 2

                // 绘制圆角矩形背景
                const rectX = node.x - textWidth / 2 - padding
                const rectY = labelY - fontSize / 2 - padding / 2
                const rectWidth = textWidth + padding * 2
                const rectHeight = fontSize + padding

                ctx.beginPath()
                ctx.moveTo(rectX + borderRadius, rectY)
                ctx.lineTo(rectX + rectWidth - borderRadius, rectY)
                ctx.quadraticCurveTo(rectX + rectWidth, rectY, rectX + rectWidth, rectY + borderRadius)
                ctx.lineTo(rectX + rectWidth, rectY + rectHeight - borderRadius)
                ctx.quadraticCurveTo(rectX + rectWidth, rectY + rectHeight, rectX + rectWidth - borderRadius, rectY + rectHeight)
                ctx.lineTo(rectX + borderRadius, rectY + rectHeight)
                ctx.quadraticCurveTo(rectX, rectY + rectHeight, rectX, rectY + rectHeight - borderRadius)
                ctx.lineTo(rectX, rectY + borderRadius)
                ctx.quadraticCurveTo(rectX, rectY, rectX + borderRadius, rectY)
                ctx.closePath()

                // 半透明白色背景
                ctx.fillStyle = 'rgba(255, 255, 255, 0.95)'
                ctx.fill()

                // 重置阴影
                ctx.shadowColor = 'transparent'
                ctx.shadowBlur = 0
                ctx.shadowOffsetX = 0
                ctx.shadowOffsetY = 0

                // 绘制文字
                ctx.fillStyle = '#1e293b'
                ctx.fillText(label, node.x, labelY)
              }
            }}
          />
        )}
      </div>

      {/* 顶部工具栏 */}
      <div style={{
        position: 'absolute',
        top: '1.5rem',
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 10,
        display: 'flex',
        alignItems: 'center',
        gap: '1rem',
        backgroundColor: 'rgba(255, 255, 255, 0.15)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderRadius: '1rem',
        padding: '0.75rem 1.5rem',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
      }}>
        <button
          onClick={() => router.push('/')}
          style={{
            padding: '0.5rem',
            backgroundColor: 'rgba(255, 255, 255, 0.2)',
            border: '1px solid rgba(255, 255, 255, 0.3)',
            borderRadius: '0.5rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s',
          }}
          title="Back to Home"
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.3)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.2)'
          }}
        >
          <Home style={{ width: '1.25rem', height: '1.25rem', color: 'white' }} />
        </button>

        <div style={{ 
          width: '1px', 
          height: '1.5rem', 
          backgroundColor: 'rgba(255, 255, 255, 0.3)',
        }} />

        <span style={{ fontSize: '1.5rem' }}>🔥</span>
        <h1 style={{ 
          fontSize: '1.25rem', 
          fontWeight: 'bold', 
          color: 'white',
          margin: 0,
        }}>
          FireEye Graph
        </h1>
        
        <div style={{ 
          width: '1px', 
          height: '1.5rem', 
          backgroundColor: 'rgba(255, 255, 255, 0.3)',
          margin: '0 0.5rem',
        }} />

        <form onSubmit={handleSearch} style={{ display: 'flex', alignItems: 'center' }}>
          <div style={{ position: 'relative' }}>
            <Search style={{ 
              position: 'absolute', 
              left: '0.75rem', 
              top: '50%', 
              transform: 'translateY(-50%)',
              width: '1rem',
              height: '1rem',
              color: 'rgba(255, 255, 255, 0.7)',
            }} />
            <input
              type="text"
              placeholder="Search nodes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                paddingLeft: '2.5rem',
                paddingRight: '1rem',
                paddingTop: '0.5rem',
                paddingBottom: '0.5rem',
                backgroundColor: 'rgba(255, 255, 255, 0.2)',
                border: '1px solid rgba(255, 255, 255, 0.3)',
                borderRadius: '0.5rem',
                color: 'white',
                outline: 'none',
                width: '16rem',
              }}
            />
          </div>
        </form>

        <div style={{ 
          display: 'flex', 
          gap: '1rem',
          alignItems: 'center',
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ 
              fontSize: '0.75rem', 
              color: 'rgba(255, 255, 255, 0.7)',
              marginBottom: '0.25rem',
            }}>
              Nodes
            </div>
            <div style={{ 
              fontSize: '1.5rem', 
              fontWeight: 'bold', 
              color: 'white',
            }}>
              {graphData.nodes.length}
            </div>
          </div>
          
          <div style={{ textAlign: 'center' }}>
            <div style={{ 
              fontSize: '0.75rem', 
              color: 'rgba(255, 255, 255, 0.7)',
              marginBottom: '0.25rem',
            }}>
              Links
            </div>
            <div style={{ 
              fontSize: '1.5rem', 
              fontWeight: 'bold', 
              color: 'white',
            }}>
              {graphData.links.length}
            </div>
          </div>
        </div>

        <div style={{ 
          width: '1px', 
          height: '1.5rem', 
          backgroundColor: 'rgba(255, 255, 255, 0.3)',
          margin: '0 0.5rem',
        }} />

        <button
          onClick={() => router.push('/upload')}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: 'rgba(251, 146, 60, 0.9)',
            border: '1px solid rgba(255, 255, 255, 0.3)',
            borderRadius: '0.5rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            transition: 'all 0.2s',
            fontWeight: '500',
            color: 'white',
          }}
          title="Upload Document"
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(251, 146, 60, 1)'
            e.currentTarget.style.transform = 'translateY(-1px)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(251, 146, 60, 0.9)'
            e.currentTarget.style.transform = 'translateY(0)'
          }}
        >
          <Upload style={{ width: '1.125rem', height: '1.125rem' }} />
          <span>上传文档</span>
        </button>

        <button
          onClick={fetchGraphData}
          style={{
            padding: '0.5rem',
            backgroundColor: 'rgba(255, 255, 255, 0.2)',
            border: '1px solid rgba(255, 255, 255, 0.3)',
            borderRadius: '0.5rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s',
          }}
          title="Refresh"
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.3)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.2)'
          }}
        >
          <RefreshCw style={{ width: '1.25rem', height: '1.25rem', color: 'white' }} />
        </button>
        
        <button
          onClick={handleExport}
          style={{
            padding: '0.5rem',
            backgroundColor: 'rgba(255, 255, 255, 0.2)',
            border: '1px solid rgba(255, 255, 255, 0.3)',
            borderRadius: '0.5rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s',
          }}
          title="Export"
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.3)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.2)'
          }}
        >
          <Download style={{ width: '1.25rem', height: '1.25rem', color: 'white' }} />
        </button>
      </div>

      {/* 左下角图例 */}
      <div style={{
        position: 'absolute',
        bottom: '1.5rem',
        left: '1.5rem',
        zIndex: 10,
        backgroundColor: 'rgba(255, 255, 255, 0.15)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderRadius: '1rem',
        padding: '1rem',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
      }}>
        <div style={{ 
          fontSize: '0.75rem', 
          fontWeight: '600',
          color: 'rgba(255, 255, 255, 0.9)',
          marginBottom: '0.75rem',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
        }}>
          节点类型
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{ 
              width: '0.75rem', 
              height: '0.75rem', 
              borderRadius: '50%', 
              backgroundColor: '#f43f5e',
            }} />
            <span style={{ fontSize: '0.875rem', color: 'white' }}>火灾事件</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{ 
              width: '0.75rem', 
              height: '0.75rem', 
              borderRadius: '50%', 
              backgroundColor: '#fb923c',
            }} />
            <span style={{ fontSize: '0.875rem', color: 'white' }}>安全隐患</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{ 
              width: '0.75rem', 
              height: '0.75rem', 
              borderRadius: '50%', 
              backgroundColor: '#a78bfa',
            }} />
            <span style={{ fontSize: '0.875rem', color: 'white' }}>后果影响</span>
          </div>
        </div>
      </div>

      {/* 节点详情面板 */}
      {selectedNode && (
        <div style={{
          position: 'absolute',
          top: '50%',
          right: '1.5rem',
          transform: 'translateY(-50%)',
          zIndex: 15,
          width: '24rem',
          maxHeight: '80vh',
          overflow: 'auto',
          backgroundColor: 'rgba(255, 255, 255, 0.15)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          borderRadius: '1rem',
          padding: '1.5rem',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
        }}>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'flex-start',
            marginBottom: '1rem',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Info style={{ width: '1.5rem', height: '1.5rem', color: 'white' }} />
              <h2 style={{ 
                fontSize: '1.25rem', 
                fontWeight: 'bold', 
                color: 'white',
                margin: 0,
              }}>
                节点详情
              </h2>
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              style={{
                padding: '0.25rem',
                backgroundColor: 'rgba(255, 255, 255, 0.2)',
                border: 'none',
                borderRadius: '0.375rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <X style={{ width: '1.25rem', height: '1.25rem', color: 'white' }} />
            </button>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <div style={{ 
              fontSize: '0.75rem', 
              color: 'rgba(255, 255, 255, 0.7)',
              marginBottom: '0.25rem',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}>
              类型
            </div>
            <div style={{ 
              display: 'inline-block',
              padding: '0.25rem 0.75rem',
              backgroundColor: getNodeColor(selectedNode),
              borderRadius: '0.5rem',
              fontSize: '0.875rem',
              fontWeight: '600',
              color: 'white',
            }}>
              {selectedNode.type === 'FireEvent' ? '火灾事件' : 
               selectedNode.type === 'Hazard' ? '安全隐患' : 
               selectedNode.type === 'Consequence' ? '后果影响' : selectedNode.type}
            </div>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <div style={{ 
              fontSize: '0.75rem', 
              color: 'rgba(255, 255, 255, 0.7)',
              marginBottom: '0.5rem',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}>
              描述
            </div>
            <div style={{ 
              fontSize: '0.875rem', 
              color: 'white',
              lineHeight: '1.5',
            }}>
              {selectedNode.description}
            </div>
          </div>

          {selectedNode.properties && Object.keys(selectedNode.properties).length > 0 && (
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ 
                fontSize: '0.75rem', 
                color: 'rgba(255, 255, 255, 0.7)',
                marginBottom: '0.5rem',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}>
                属性
              </div>
              <div style={{ 
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                borderRadius: '0.5rem',
                padding: '0.75rem',
              }}>
                {Object.entries(selectedNode.properties)
                  .filter(([key, value]) => {
                    // 过滤掉无用字段
                    if (['id', 'created_at', 'updated_at'].includes(key)) return false
                    // 过滤掉与描述相同的字段
                    if ((key === 'standard_term' || key === 'description') && 
                        String(value) === selectedNode.description) return false
                    // 过滤掉默认值字段（如严重程度=5）
                    if (key === 'severity_level' && String(value) === '5') return false
                    return true
                  })
                  .map(([key, value]) => {
                    // 翻译字段名
                    const fieldNameMap: Record<string, string> = {
                      'event_type': '事件类型',
                      'standard_term': '标准术语',
                      'description': '描述',
                      'severity_level': '严重程度',
                      'category': '类别',
                      'frequency': '频率',
                      'location': '位置',
                      'time': '时间',
                      'cause': '原因',
                      'impact': '影响',
                      'impact_level': '影响等级',
                      'affected_area': '影响区域',
                      'risk_level': '风险等级',
                      'probability': '发生概率',
                      'consequence': '后果',
                      'mitigation': '缓解措施'
                    }
                    const displayName = fieldNameMap[key] || key
                    
                    return (
                      <div key={key} style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between',
                        marginBottom: '0.5rem',
                        gap: '1rem',
                      }}>
                        <span style={{ 
                          fontSize: '0.875rem', 
                          color: 'rgba(255, 255, 255, 0.7)',
                          flexShrink: 0,
                        }}>
                          {displayName}:
                        </span>
                        <span style={{ 
                          fontSize: '0.875rem', 
                          color: 'white',
                          fontWeight: '500',
                          textAlign: 'right',
                        }}>
                          {String(value)}
                        </span>
                      </div>
                    )
                  })}
                {Object.entries(selectedNode.properties)
                  .filter(([key, value]) => {
                    if (['id', 'created_at', 'updated_at'].includes(key)) return false
                    if ((key === 'standard_term' || key === 'description') && 
                        String(value) === selectedNode.description) return false
                    if (key === 'severity_level' && String(value) === '5') return false
                    return true
                  }).length === 0 && (
                  <div style={{ 
                    fontSize: '0.875rem', 
                    color: 'rgba(255, 255, 255, 0.5)',
                    textAlign: 'center',
                  }}>
                    暂无额外属性
                  </div>
                )}
              </div>
            </div>
          )}

          <div>
            <div style={{ 
              fontSize: '0.75rem', 
              color: 'rgba(255, 255, 255, 0.7)',
              marginBottom: '0.5rem',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}>
              关联关系 ({getConnectedNodes(selectedNode.id).length})
            </div>
            <div style={{ 
              display: 'flex',
              flexDirection: 'column',
              gap: '0.5rem',
            }}>
              {getConnectedNodes(selectedNode.id).slice(0, 5).map((item, idx) => {
                // 翻译关系类型
                const relationMap: Record<string, string> = {
                  'CAUSES': '导致',
                  'LEADS_TO': '引发',
                  'RESULTS_IN': '造成',
                  'TRIGGERS': '触发',
                  'CONTRIBUTES_TO': '促成',
                  'ASSOCIATED_WITH': '关联',
                  'RELATED_TO': '相关'
                }
                const displayRelation = relationMap[item.relation] || item.relation
                
                return (
                  <div key={idx} style={{
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    borderRadius: '0.5rem',
                    padding: '0.75rem',
                  }}>
                    <div style={{ 
                      fontSize: '0.875rem', 
                      color: 'white',
                      fontWeight: '500',
                      marginBottom: '0.25rem',
                    }}>
                      {item.node?.description}
                    </div>
                    <div style={{ 
                      fontSize: '0.75rem', 
                      color: 'rgba(255, 255, 255, 0.7)',
                    }}>
                      {item.direction === 'outgoing' ? '→' : '←'} {displayRelation}
                    </div>
                  </div>
                )
              })}
              {getConnectedNodes(selectedNode.id).length > 5 && (
                <div style={{ 
                  fontSize: '0.75rem', 
                  color: 'rgba(255, 255, 255, 0.7)',
                  textAlign: 'center',
                }}>
                  +{getConnectedNodes(selectedNode.id).length - 5} 个更多关系
                </div>
              )}
              {getConnectedNodes(selectedNode.id).length === 0 && (
                <div style={{ 
                  fontSize: '0.875rem', 
                  color: 'rgba(255, 255, 255, 0.5)',
                  textAlign: 'center',
                  padding: '1rem',
                }}>
                  暂无关联关系
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 加载状态 */}
      {isLoading && (
        <div style={{
          position: 'absolute',
          inset: 0,
          zIndex: 20,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'rgba(0, 0, 0, 0.3)',
          backdropFilter: 'blur(4px)',
          WebkitBackdropFilter: 'blur(4px)',
        }}>
          <div style={{
            backgroundColor: 'rgba(255, 255, 255, 0.15)',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            borderRadius: '1rem',
            padding: '2rem',
            textAlign: 'center',
            border: '1px solid rgba(255, 255, 255, 0.2)',
          }}>
            <div style={{
              width: '3rem',
              height: '3rem',
              border: '4px solid rgba(255, 255, 255, 0.3)',
              borderTopColor: 'white',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
              margin: '0 auto 1rem',
            }} />
            <p style={{ color: 'white', fontWeight: '500', margin: 0 }}>Loading graph data...</p>
          </div>
        </div>
      )}

      {/* 空数据状态 */}
      {!isLoading && graphData.nodes.length === 0 && (
        <div style={{
          position: 'absolute',
          inset: 0,
          zIndex: 20,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          pointerEvents: 'none',
        }}>
          <div style={{
            backgroundColor: 'rgba(255, 255, 255, 0.15)',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            borderRadius: '1rem',
            padding: '3rem',
            textAlign: 'center',
            maxWidth: '28rem',
            border: '1px solid rgba(255, 255, 255, 0.2)',
          }}>
            <span style={{ fontSize: '4rem', display: 'block', marginBottom: '1rem' }}>📊</span>
            <h2 style={{ 
              fontSize: '1.5rem', 
              fontWeight: 'bold', 
              color: 'white',
              marginBottom: '0.5rem',
            }}>
              No Graph Data
            </h2>
            <p style={{ color: 'rgba(255, 255, 255, 0.8)', margin: 0 }}>
              Upload documents to generate the knowledge graph
            </p>
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
