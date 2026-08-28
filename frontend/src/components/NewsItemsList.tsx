import { useMemo, useState } from 'react'
import type { NewsItem } from '../api/types'

export function NewsItemsList({ items }: { items: NewsItem[] }) {
  const [selectedEntity, setSelectedEntity] = useState<string>('all')

  const entities = useMemo(
    () => Array.from(new Set(items.map((item) => item.related_entity))),
    [items],
  )

  const filtered = useMemo(
    () =>
      selectedEntity === 'all'
        ? items
        : items.filter((item) => item.related_entity === selectedEntity),
    [items, selectedEntity],
  )

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold text-slate-900">News items ({items.length})</h2>
        {entities.length > 1 && (
          <select
            value={selectedEntity}
            onChange={(event) => setSelectedEntity(event.target.value)}
            className="rounded border border-slate-300 px-2 py-1 text-sm"
          >
            <option value="all">All entities</option>
            {entities.map((entity) => (
              <option key={entity} value={entity}>
                {entity}
              </option>
            ))}
          </select>
        )}
      </div>

      {filtered.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500">No news items found.</p>
      ) : (
        <ul className="mt-3 space-y-3">
          {filtered.map((item, index) => (
            <li key={`${item.url}-${index}`} className="border-t border-slate-100 pt-3 first:border-0 first:pt-0">
              <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
                <a
                  href={item.url}
                  target="_blank"
                  rel="noreferrer"
                  className="font-medium text-indigo-600 hover:underline"
                >
                  {item.title}
                </a>
                <span className="text-xs text-slate-400">
                  {item.source}
                  {item.published_at ? ` · ${new Date(item.published_at).toLocaleDateString()}` : ''}
                </span>
              </div>
              <p className="text-sm text-slate-600">{item.snippet}</p>
              <span className="mt-1 inline-block rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
                {item.related_entity}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
