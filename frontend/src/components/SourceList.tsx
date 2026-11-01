import type { Source } from '../types'

interface SourceListProps {
  sources: Source[]
}

export function SourceList({ sources }: SourceListProps) {
  return (
    // "Retrieved", not "cited": these are all the passages the model was given
    <details className="sources">
      <summary>Retrieved passages ({sources.length})</summary>
      <ul>
        {sources.map((source, index) => (
          <li key={index}>
            <strong>
              {source.filename} p.{source.page}
            </strong>
            <p>{source.snippet}…</p>
          </li>
        ))}
      </ul>
    </details>
  )
}
