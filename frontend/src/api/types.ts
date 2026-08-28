export type JobStatusValue = 'pending' | 'running' | 'done' | 'error'

export interface ResearchResponse {
  job_id: string
}

export interface StatusResponse {
  status: JobStatusValue
  current_step: string | null
}

export interface CompanyContext {
  source_url: string
  domain: string
  target_audience: string
  value_proposition: string
  keywords: string[]
}

export interface Competitor {
  name: string
  url: string | null
  reason: string
}

export interface NewsItem {
  title: string
  url: string
  source: string
  published_at: string | null
  snippet: string
  related_entity: string
}

export interface MonitoringBrief {
  company: CompanyContext
  competitors: Competitor[]
  items: NewsItem[]
  generated_at: string
  summary_markdown: string
}
