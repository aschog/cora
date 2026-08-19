/**
 * Rendered HTML applied to a block that is already drawn, node by node: what has not
 * changed is left alone, and only what differs is written.
 *
 * An answer is written a token at a time, so the alternative — assigning `innerHTML` —
 * throws away the whole answer and rebuilds it on every piece. The reader loses any
 * selection they had made in it, which makes copying an answer while it is being written
 * impossible.
 */
export function patch(into: Element, html: string): void {
  const wanted = into.ownerDocument.createElement('template')
  wanted.innerHTML = html
  reconcile(into, wanted.content)
}

function reconcile(kept: Node, wanted: Node): void {
  const here = Array.from(kept.childNodes)
  const next = Array.from(wanted.childNodes)
  next.forEach((node, at) => {
    const drawn = here[at]
    if (!drawn) kept.appendChild(node)
    else if (drawn.nodeType !== node.nodeType || drawn.nodeName !== node.nodeName)
      kept.replaceChild(node, drawn)
    else if (drawn.nodeType === Node.TEXT_NODE) {
      if (drawn.nodeValue !== node.nodeValue) drawn.nodeValue = node.nodeValue
    } else {
      attributes(drawn as Element, node as Element)
      reconcile(drawn, node)
    }
  })
  here.slice(next.length).forEach((gone) => kept.removeChild(gone))
}

function attributes(kept: Element, wanted: Element): void {
  for (const { name, value } of Array.from(wanted.attributes))
    if (kept.getAttribute(name) !== value) kept.setAttribute(name, value)
  for (const { name } of Array.from(kept.attributes))
    if (!wanted.hasAttribute(name)) kept.removeAttribute(name)
}
