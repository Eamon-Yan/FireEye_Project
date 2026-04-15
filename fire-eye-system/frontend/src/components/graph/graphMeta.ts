import type { GraphNode } from '@/types/graph'

export const NODE_META: Record<string, { label: string; color: string }> = {
  FireEvent: { label: '火灾事件', color: '#bc4123' },
  Hazard: { label: '安全隐患', color: '#d67b2c' },
  Consequence: { label: '后果影响', color: '#2f6b91' },
}

export const NODE_TYPES = Object.keys(NODE_META)

export const RELATION_LABELS: Record<string, string> = {
  CAUSES: '导致',
  LEADS_TO: '引发',
  RESULTS_IN: '造成',
  TRIGGERS: '触发',
  CONTRIBUTES_TO: '促成',
  ASSOCIATED_WITH: '关联',
  RELATED_TO: '相关',
}

export const RELATION_TYPES = Object.keys(RELATION_LABELS)

export const FIELD_LABELS: Record<string, string> = {
  event_type: '事件类型',
  standard_term: '标准术语',
  description: '描述',
  severity_level: '严重程度',
  category: '类别',
  frequency: '频率',
  location: '位置',
  time: '时间',
  cause: '原因',
  impact: '影响',
  impact_level: '影响等级',
  affected_area: '影响区域',
  risk_level: '风险等级',
  probability: '发生概率',
  consequence: '后果',
  mitigation: '缓解措施',
}

export function getNodeMeta(nodeType: string) {
  return NODE_META[nodeType] ?? { label: nodeType, color: '#64748b' }
}

export function getNodeId(nodeOrId: GraphNode | string): string {
  return typeof nodeOrId === 'string' ? nodeOrId : nodeOrId.id
}
