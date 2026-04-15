export interface EventChain {
  source: string
  relation: string
  target: string
  confidence: number
  context?: string
}

export interface UploadResult {
  document_id: string
  filename: string
  file_type: string
  event_chains?: {
    count: number
    chains: EventChain[]
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
