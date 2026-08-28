import type { Competitor } from '../api/types'

export function CompetitorsList({ competitors }: { competitors: Competitor[] }) {
  if (competitors.length === 0) {
    return (
      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="text-lg font-semibold text-slate-900">Competitors</h2>
        <p className="mt-2 text-sm text-slate-500">No competitors were found.</p>
      </section>
    )
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <h2 className="text-lg font-semibold text-slate-900">
        Competitors ({competitors.length})
      </h2>
      <ul className="mt-3 space-y-3">
        {competitors.map((competitor) => (
          <li key={competitor.name} className="border-t border-slate-100 pt-3 first:border-0 first:pt-0">
            <div className="flex items-baseline justify-between gap-2">
              <span className="font-medium text-slate-800">{competitor.name}</span>
              {competitor.url && (
                <a
                  href={competitor.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-indigo-600 hover:underline"
                >
                  visit site
                </a>
              )}
            </div>
            <p className="text-sm text-slate-600">{competitor.reason}</p>
          </li>
        ))}
      </ul>
    </section>
  )
}
