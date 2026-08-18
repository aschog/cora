import { useEffect, useRef } from 'react'
import type { Doc } from '../data'

type Props = { doc: Doc; scrollToCited?: boolean }

function scrollableAncestor(el: HTMLElement): HTMLElement | null {
  for (let node = el.parentElement; node; node = node.parentElement) {
    const overflow = getComputedStyle(node).overflowY
    if ((overflow === 'auto' || overflow === 'scroll') && node.scrollHeight > node.clientHeight) return node
  }
  return null
}

export default function DocumentBody({ doc, scrollToCited = false }: Props) {
  const firstCited = useRef<HTMLParagraphElement>(null)

  useEffect(() => {
    if (!scrollToCited) return
    const target = firstCited.current
    if (!target) return
    const container = scrollableAncestor(target)
    if (!container) return
    const offset = target.getBoundingClientRect().top - container.getBoundingClientRect().top
    container.scrollTop += offset - container.clientHeight / 2 + target.offsetHeight / 2
  }, [scrollToCited, doc.key])

  let seenCited = false
  return (
    <div className="doc-panel">
      {doc.body.map((para, i) => {
        const isFirstCited = Boolean(para.cited) && !seenCited
        if (para.cited) seenCited = true
        return (
          <p
            key={i}
            className={para.cited ? 'doc-para cited' : 'doc-para'}
            ref={isFirstCited ? firstCited : undefined}
          >
            {para.text}
          </p>
        )
      })}
    </div>
  )
}
