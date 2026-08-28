import { Link } from 'react-router-dom'

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-5">
      <h2 className="text-lg font-semibold text-red-800">Something went wrong</h2>
      <p className="mt-2 text-sm text-red-700">{message}</p>
      <Link
        to="/"
        className="mt-4 inline-block rounded bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
      >
        Back to search
      </Link>
    </div>
  )
}
