import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError, startResearch } from '../api/client'

function isValidUrl(value: string): boolean {
  try {
    new URL(value)
    return true
  } catch {
    return false
  }
}

export function SearchPage() {
  const navigate = useNavigate()
  const [url, setUrl] = useState('')
  const [companyName, setCompanyName] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitError(null)

    if (!isValidUrl(url)) {
      setSubmitError('Please enter a valid URL, e.g. https://example.com')
      return
    }

    setSubmitting(true)
    try {
      const { job_id: jobId } = await startResearch(url)
      const params = new URLSearchParams({ url, name: companyName })
      navigate(`/results/${jobId}?${params.toString()}`)
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.detail : 'Failed to start research.')
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-lg rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Competitive Intelligence Pipeline</h1>
        <p className="mt-2 text-sm text-slate-500">
          Enter a company's website and we'll find their competitors and the latest news about
          them.
        </p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label htmlFor="company-name" className="block text-sm font-medium text-slate-700">
              Company name
            </label>
            <input
              id="company-name"
              type="text"
              value={companyName}
              onChange={(event) => setCompanyName(event.target.value)}
              placeholder="Acme Inc."
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
            />
          </div>

          <div>
            <label htmlFor="url" className="block text-sm font-medium text-slate-700">
              Website URL
            </label>
            <input
              id="url"
              type="text"
              value={url}
              onChange={(event) => setUrl(event.target.value)}
              placeholder="https://acme.com"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
            />
          </div>

          {submitError && <p className="text-sm text-red-600">{submitError}</p>}

          <button
            type="submit"
            disabled={submitting || url.trim() === ''}
            className="w-full rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting ? 'Starting…' : 'Search'}
          </button>
        </form>
      </div>
    </div>
  )
}
