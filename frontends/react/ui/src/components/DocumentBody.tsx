import { useEffect, useRef } from 'react'

export type Span = { start: number; end: number }

type Props = { text: string; spans: Span[]; scrollToFirst?: boolean }

/** The document, with every cited passage marked where its offsets fall. */
export default function DocumentBody({ text, spans, scrollToFirst }: Props) {
  const first = useRef<HTMLElement>(null)

  const where = spans.map((span) => `${span.start}-${span.end}`).join()

  useEffect(() => {
    if (scrollToFirst) first.current?.scrollIntoView({ block: 'center' })
  }, [scrollToFirst, text, where])

  const marked = merged(spans, text.length)

  const pieces: React.ReactNode[] = []
  let read = 0
  marked.forEach((span, n) => {
    if (span.start > read) pieces.push(<span key={`t${n}`}>{text.slice(read, span.start)}</span>)
    pieces.push(
      <mark className="doc-passage" key={`m${n}`} ref={n === 0 ? first : undefined}>
        {text.slice(span.start, span.end)}
      </mark>,
    )
    read = Math.max(read, span.end)
  })
  pieces.push(<span key="tail">{text.slice(read)}</span>)

  return <div className="doc-panel doc-para">{pieces}</div>
}

/**
 * The passages as disjoint spans, in order. Chunks overlap by design, so two adjacent
 * cited chunks share their edges — slicing each independently would emit the shared
 * characters twice, and a nested one out of order, showing the reader a document that
 * is not theirs. Overlapping citations are one mark over what they jointly cover.
 */
function merged(spans: Span[], length: number): Span[] {
  const ordered = spans
    .map((span) => clamped(span, length))
    .sort((a, b) => a.start - b.start)
  const disjoint: Span[] = []
  for (const span of ordered) {
    const running = disjoint[disjoint.length - 1]
    if (running && span.start <= running.end) {
      running.end = Math.max(running.end, span.end)
      continue
    }
    disjoint.push({ ...span })
  }
  return disjoint
}

/** A span running past the end marks to the end rather than throwing. */
function clamped(span: Span, length: number): Span {
  const start = Math.max(0, Math.min(span.start, length))
  return { start, end: Math.max(start, Math.min(span.end, length)) }
}
