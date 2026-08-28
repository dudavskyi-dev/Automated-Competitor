import type { MonitoringBrief, ResearchResponse, StatusResponse } from './types'

export class ApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init)
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      if (typeof body?.detail === 'string') detail = body.detail
    } catch {
      // response wasn't JSON; fall back to statusText
    }
    throw new ApiError(res.status, detail)
  }
  return (await res.json()) as T
}

export function startResearch(url: string): Promise<ResearchResponse> {
  return request<ResearchResponse>('/research', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  })
}

export function getJobStatus(jobId: string): Promise<StatusResponse> {
  return request<StatusResponse>(`/research/${jobId}/status`)
}

export function getJobReport(jobId: string): Promise<MonitoringBrief> {
  return request<MonitoringBrief>(`/research/${jobId}/report`)
}
