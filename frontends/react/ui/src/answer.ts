import MarkdownIt from 'markdown-it'
import type { Citation } from './api'
/* The button is written as markup rather than drawn as a component, so the class has to
   be read out of the module by hand — the same one the answer's own styles come from. */
import styles from './components/Answer.module.css'

/**
 * What counts as a citation, and it is the rule the answer was written under: a run of
 * brackets continuing neither a word nor another bracket. Shared with nothing — the
 * server resolves by the same rule, so the two never disagree about which numbers in an
 * answer are citations at all. Which of them the reader can *click* is narrower: a
 * number written inside code is one the answer rests on and is drawn here as the text it
 * was written as, because a button in a code block would misquote the code.
 */
const CITATION_RUN = /(?<![\w\]])(?:\[\d+\])+/g
const TAGS = /(<[^>]*>)/
const UNCLICKABLE = new Set(['code', 'pre'])

const markdown = new MarkdownIt({ html: false, linkify: false, breaks: false })
/* An answer that could fetch an image could make the reader's browser call out on a
   document's say-so. It renders as its own text instead. */
markdown.disable('image')

/* A link in an answer was written over documents cora read, so it leaves this page
   rather than replacing it, and carries nothing back to the opener. */
markdown.renderer.rules.link_open = (tokens, idx, options, _env, self) => {
  tokens[idx].attrSet('target', '_blank')
  tokens[idx].attrSet('rel', 'noopener noreferrer')
  return self.renderToken(tokens, idx, options)
}

/**
 * An answer as the HTML the page draws: markdown rendered, and every `[n]` that names a
 * citation replaced by a button carrying it. A number citing nothing stays the text it
 * was written as, and nothing inside a tag or inside code is touched.
 */
export function answerHtml(answer: string, citations: Citation[]): string {
  const known = new Set(citations.map((citation) => citation.number))
  let inCode = 0
  return markdown
    .render(answer)
    .split(TAGS)
    .map((piece) => {
      const tag = piece.match(/^<\/?([a-z0-9]+)/i)
      if (tag) {
        if (UNCLICKABLE.has(tag[1].toLowerCase())) inCode += piece[1] === '/' ? -1 : 1
        return piece
      }
      return inCode > 0 ? piece : clickable(piece, known)
    })
    .join('')
}

function clickable(text: string, known: Set<number>): string {
  return text.replace(CITATION_RUN, (run) =>
    (run.match(/\d+/g) ?? [])
      .map((digits) => {
        const number = Number(digits)
        if (!known.has(number)) return `[${digits}]`
        return (
          `<button class="${styles.cite}" data-cite="${number}" ` +
          `aria-label="Open cited source ${number}">${number}</button>`
        )
      })
      .join(''),
  )
}
