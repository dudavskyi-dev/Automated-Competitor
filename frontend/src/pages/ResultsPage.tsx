import { useEffect, useState } from 'react'
import { useParams, useSearchParams, Link } from 'react-router-dom'
import { ApiError, getJobReport } from '../api/client'
import { useJobPolling } from '../hooks/useJobPolling'
import { StepProgress } from '../components/StepProgress'
import { CompanyContextCard } from '../components/CompanyContextCard'
import { CompetitorsList } from '../components/CompetitorsList'
import { NewsItemsList } from '../components/NewsItemsList'
import { BriefMarkdown } from '../components/BriefMarkdown'
import { ErrorState } from '../components/ErrorState'
import type { MonitoringBrief } from '../api/types'

type ReportState =
  | { kind: 'idle' }
  | { kind: 'success'; brief: MonitoringBrief }
  | { kind: 'error'; message: string }

export function ResultsPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const [params] = useSearchParams()
  const searchedUrl = params.get('url')
  const companyName = params.get('name')

  const { status, currentStep, pollError } = useJobPolling(jobId ?? '')
  const [reportState, setReportState] = useState<ReportState>({ kind: 'idle' })

  useEffect(() => {
    if (!jobId || (status !== 'done' && status !== 'error')) return

    let cancelled = false
    getJobReport(jobId)
      .then((report) => {
        if (!cancelled) setReportState({ kind: 'success', brief: report })
      })
      .catch((err) => {
        if (cancelled) return
        setReportState({
          kind: 'error',
          message: err instanceof ApiError ? err.detail : 'Failed to load the report.',
        })
      })

    return () => {
      cancelled = true
    }
  }, [jobId, status])

  if (!jobId) {
    return <ErrorState message="No job id was provided." />
  }

  const pollErrorMessage = pollError
    ? pollError.status === 404
      ? 'This job could not be found. It may have been lost if the server restarted.'
      : pollError.detail
    : null

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-10">
      <div className="mx-auto max-w-3xl space-y-6">
        <header className="rounded-lg border border-slate-200 bg-white p-5">
          <Link to="/" className="text-sm text-indigo-600 hover:underline">
            ← Back to search
          </Link>
          <h1 className="mt-2 text-xl font-semibold text-slate-900">
            {companyName || 'Monitoring brief'}
          </h1>
          {searchedUrl && <p className="text-sm text-slate-500">{searchedUrl}</p>}
        </header>

        {pollErrorMessage && <ErrorState message={pollErrorMessage} />}

        {!pollErrorMessage && (status === null || status === 'pending' || status === 'running') && (
          <div className="rounded-lg border border-slate-200 bg-white p-5">
            <StepProgress status={status ?? 'pending'} currentStep={currentStep} />
          </div>
        )}

        {!pollErrorMessage &&
          (status === 'done' || status === 'error') &&
          reportState.kind === 'idle' && (
            <div className="rounded-lg border border-slate-200 bg-white p-5">
              <p className="text-sm text-slate-500">Loading report…</p>
            </div>
          )}

        {!pollErrorMessage && reportState.kind === 'error' && (
          <ErrorState message={reportState.message} />
        )}

        {!pollErrorMessage && reportState.kind === 'success' && (
          <div className="space-y-6">
            <CompanyContextCard company={reportState.brief.company} />
            <CompetitorsList competitors={reportState.brief.competitors} />
            <NewsItemsList items={reportState.brief.items} />
            <BriefMarkdown markdown={reportState.brief.summary_markdown} />
          </div>
        )}
      </div>
    </div>
  )
}
