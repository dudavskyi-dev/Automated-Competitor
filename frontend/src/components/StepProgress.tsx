import { STEP_LABELS, STEP_ORDER } from '../constants/steps'
import type { JobStatusValue } from '../api/types'

interface StepProgressProps {
  status: JobStatusValue
  currentStep: string | null
}

function getActiveIndex(status: JobStatusValue, currentStep: string | null): number {
  if (status === 'pending') return -1
  if (currentStep === null) return 0
  const finishedIndex = STEP_ORDER.indexOf(currentStep as (typeof STEP_ORDER)[number])
  return finishedIndex === -1 ? 0 : finishedIndex + 1
}

export function StepProgress({ status, currentStep }: StepProgressProps) {
  const activeIndex = getActiveIndex(status, currentStep)

  return (
    <div className="space-y-3">
      {status === 'pending' && <p className="text-sm text-slate-500">Queued…</p>}
      <ol className="space-y-2">
        {STEP_ORDER.map((step, index) => {
          const isDone = index < activeIndex
          const isActive = index === activeIndex && activeIndex < STEP_ORDER.length
          return (
            <li key={step} className="flex items-center gap-3">
              <span
                className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-medium ${
                  isDone
                    ? 'bg-emerald-500 text-white'
                    : isActive
                      ? 'bg-indigo-500 text-white animate-pulse'
                      : 'bg-slate-200 text-slate-500'
                }`}
              >
                {isDone ? '✓' : index + 1}
              </span>
              <span className={isDone || isActive ? 'text-slate-900' : 'text-slate-400'}>
                {STEP_LABELS[step]}
              </span>
            </li>
          )
        })}
      </ol>
    </div>
  )
}
