import { useEffect, useMemo, useRef } from 'react'
import styles from './DocumentBody.module.css'
import { joined } from '../joined'

type Span = { start: number; end: number }

type Props = {
  text: string
  spans: Span[]
  scrollToFirst?: boolean
  /** Drawn without its own panel, where whatever holds it already is one. A prop rather
   *  than a rule reaching in from the holder: each component's styles are its own now, so
   *  what the outside gets to change about this one is what this one offers. */
  flat?: boolean
}

/** The document, with every cited passage marked where its offsets fall. */
export default function DocumentBody({ text, spans, scrollToFirst, flat }: Props) {
  const first = useRef<HTMLElement>(null)

  const where = spans.map((span) => `${span.start}-${span.end}`).join()

  useEffect(() => {
    if (scrollToFirst) first.current?.scrollIntoView({ block: 'center' })
  }, [scrollToFirst, text, where])

  /* A whole document cut into spans on every render is the one expensive thing the page
     does, and most renders change neither the text nor where it is marked — a turn
     landing, a rail folding, a banner appearing. Held against the two values the cutting
     actually reads: the text, and where the marks fall in it. */
  const pieces = useMemo(() => {
    const marked = merged(spans, text.length)
    const cut: React.ReactNode[] = []
    let read = 0
    marked.forEach((span, n) => {
      if (span.start > read) {
        cut.push(<span key={`t${n}`}>{text.slice(read, span.start)}</span>)
      }
      cut.push(
        <mark
          className={styles.docPassage}
          key={`m${n}`}
          ref={n === 0 ? first : undefined}
        >
          {text.slice(span.start, span.end)}
        </mark>,
      )
      read = Math.max(read, span.end)
    })
    cut.push(<span key="tail">{text.slice(read)}</span>)
    return cut
    /* `where` rather than `spans`: the array is built fresh by the panel on every render
       and would never compare equal, which is the same as not holding it at all. */
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text, where])

  return (
    <div className={joined(styles.docPanel, styles.docPara, flat && styles.flat)}>
      {pieces}
    </div>
  )
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
