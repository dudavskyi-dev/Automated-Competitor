import { useEffect, useState } from 'react'
import { ApiError, getJobStatus } from '../api/client'
import type { JobStatusValue } from '../api/types'

const POLL_INTERVAL_MS = 1500

interface JobPollingResult {
  status: JobStatusValue | null
  currentStep: string | null
  pollError: ApiError | null
}

export function useJobPolling(jobId: string): JobPollingResult {
  const [status, setStatus] = useState<JobStatusValue | null>(null)
  const [currentStep, setCurrentStep] = useState<string | null>(null)
  const [pollError, setPollError] = useState<ApiError | null>(null)

  useEffect(() => {
    let cancelled = false
    let timer: ReturnType<typeof setTimeout> | undefined

    async function tick() {
      try {
        const body = await getJobStatus(jobId)
        if (cancelled) return
        setStatus(body.status)
        setCurrentStep(body.current_step)
        if (body.status === 'pending' || body.status === 'running') {
          timer = setTimeout(tick, POLL_INTERVAL_MS)
        }
      } catch (err) {
        if (cancelled) return
        if (err instanceof ApiError && err.status === 404) {
          setPollError(err)
          return
        }
        timer = setTimeout(tick, POLL_INTERVAL_MS)
      }
    }

    tick()
    return () => {
      cancelled = true
      if (timer) clearTimeout(timer)
    }
  }, [jobId])

  return { status, currentStep, pollError }
}
