import { useEffect, useRef, useState } from 'react'
import * as cora from '../api'
import type { Citation } from '../api'

/** The kept text of the document a citation was measured in, or why it cannot be read. */
export function usePassage(citation: Citation | null) {
  const [text, setText] = useState<string | null>(null)
  const [trouble, setTrouble] = useState<string | null>(null)

  useEffect(() => {
    setText(null)
    setTrouble(null)
    if (!citation) return
    let current = true
    cora
      .passage(citation.upload)
      .then((kept) => current && setText(kept))
      .catch((failed) => current && setTrouble(String(failed.message ?? failed)))
    return () => {
      current = false
    }
  }, [citation?.upload])

  return { text, trouble }
}

type Props = { citation: Citation; text: string; scrollToPassage?: boolean }

export default function DocumentBody({ citation, text, scrollToPassage }: Props) {
  const marked = useRef<HTMLElement>(null)

  useEffect(() => {
    if (scrollToPassage) marked.current?.scrollIntoView({ block: 'center' })
  }, [scrollToPassage, citation.upload, citation.start])

  const start = Math.max(0, Math.min(citation.start, text.length))
  const end = Math.max(start, Math.min(citation.end, text.length))

  return (
    <div className="doc-panel">
      <span className="doc-para">{text.slice(0, start)}</span>
      <mark className="doc-passage" ref={marked}>
        {text.slice(start, end)}
      </mark>
      <span className="doc-para">{text.slice(end)}</span>
    </div>
  )
}
