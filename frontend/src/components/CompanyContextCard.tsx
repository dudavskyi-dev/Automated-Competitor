import type { CompanyContext } from '../api/types'

export function CompanyContextCard({ company }: { company: CompanyContext }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <h2 className="text-lg font-semibold text-slate-900">{company.domain}</h2>
      <a
        href={company.source_url}
        target="_blank"
        rel="noreferrer"
        className="text-sm text-indigo-600 hover:underline"
      >
        {company.source_url}
      </a>
      <dl className="mt-4 space-y-3 text-sm">
        <div>
          <dt className="font-medium text-slate-700">Target audience</dt>
          <dd className="text-slate-600">{company.target_audience}</dd>
        </div>
        <div>
          <dt className="font-medium text-slate-700">Value proposition</dt>
          <dd className="text-slate-600">{company.value_proposition}</dd>
        </div>
        <div>
          <dt className="font-medium text-slate-700">Keywords</dt>
          <dd className="mt-1 flex flex-wrap gap-1.5">
            {company.keywords.map((keyword) => (
              <span
                key={keyword}
                className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600"
              >
                {keyword}
              </span>
            ))}
          </dd>
        </div>
      </dl>
    </section>
  )
}
