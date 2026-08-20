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
    else if (drawn.nodeType !== Node.ELEMENT_NODE) written(drawn, node)
    else {
      attributes(drawn as Element, node as Element)
      reconcile(drawn, node)
    }
  })
  here.slice(next.length).forEach((gone) => kept.removeChild(gone))
}

/** Text that only grew is *appended to* rather than assigned. Assigning `nodeValue` is
 *  DOM's replace-data across the whole node, which pulls every selection boundary inside
 *  it back to the start — so the reader would lose the sentence they selected in the
 *  paragraph still being written, which is the one the answer arrives in. Appending moves
 *  no boundary that is already in the text. */
function written(drawn: Node, wanted: Node): void {
  if (drawn.nodeValue === wanted.nodeValue) return
  if (drawn.nodeType === Node.TEXT_NODE) appended(drawn as Text, wanted as Text)
  else drawn.nodeValue = wanted.nodeValue
}

function appended(drawn: Text, wanted: Text): void {
  if (wanted.data.startsWith(drawn.data))
    drawn.appendData(wanted.data.slice(drawn.data.length))
  else drawn.data = wanted.data
}

function attributes(kept: Element, wanted: Element): void {
  for (const { name, value } of Array.from(wanted.attributes))
    if (kept.getAttribute(name) !== value) kept.setAttribute(name, value)
  for (const { name } of Array.from(kept.attributes))
    if (!wanted.hasAttribute(name)) kept.removeAttribute(name)
}
