import { useEffect, useRef, useState } from 'react'
import * as cora from '../api'

/** The kept text of an upload, or why it cannot be read. */
export function usePassage(upload: string | null) {
  const [text, setText] = useState<string | null>(null)
  const [trouble, setTrouble] = useState<string | null>(null)

  useEffect(() => {
    setText(null)
    setTrouble(null)
    if (!upload) return
    let current = true
    cora
      .passage(upload)
      .then((kept) => current && setText(kept))
      .catch((failed) => current && setTrouble(String(failed.message ?? failed)))
    return () => {
      current = false
    }
  }, [upload])

  return { text, trouble }
}

export type Span = { start: number; end: number }

type Props = { text: string; spans: Span[]; scrollToFirst?: boolean }

/** The document, with every cited passage marked where its offsets fall. */
export default function DocumentBody({ text, spans, scrollToFirst }: Props) {
  const first = useRef<HTMLElement>(null)

  useEffect(() => {
    if (scrollToFirst) first.current?.scrollIntoView({ block: 'center' })
  }, [scrollToFirst, text, spans])

  const marked = [...spans]
    .map((span) => clamped(span, text.length))
    .sort((a, b) => a.start - b.start)

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

/** A span running past the end marks to the end rather than throwing. */
function clamped(span: Span, length: number): Span {
  const start = Math.max(0, Math.min(span.start, length))
  return { start, end: Math.max(start, Math.min(span.end, length)) }
}
