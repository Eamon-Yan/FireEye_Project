export interface GraphNode {
  id: string
  type: string
  description: string
  properties: Record<string, unknown>
}

export interface GraphLink {
  source: string | GraphNode
  target: string | GraphNode
  relation: string
  confidence?: number
}

export interface GraphData {
  nodes: GraphNode[]
  links: GraphLink[]
}

export interface ConnectedNode {
  node: GraphNode
  relation: string
  direction: 'outgoing' | 'incoming'
}
