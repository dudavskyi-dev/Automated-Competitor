import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export function BriefMarkdown({ markdown }: { markdown: string }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <h2 className="text-lg font-semibold text-slate-900">Full brief</h2>
      <div className="prose prose-slate prose-sm mt-3 max-w-none">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdown}</ReactMarkdown>
      </div>
    </section>
  )
}
