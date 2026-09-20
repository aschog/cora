import { useEffect, useState } from 'react'
import dialog from './dialog.module.css'
import styles from './ReadImage.module.css'

const HEAD = 'READ FROM THE IMAGE'
const NOTHING = 'Nothing was read in that image.'
const SAID =
  'Correct what was read before it is kept. The image stays on this machine either way.'

type Props = {
  /** What the photo was called. The document is named after it, so the reader can tell
   *  which photo a list in the field came from. */
  image: string
  /** The words as they were recognised. Empty is a photo with no text in it, which is
   *  news rather than a document to save. */
  read: string
  /** Keep what is on screen: the same upload every other file goes through. */
  onKeep: (file: File) => void
  onDiscard: () => void
}

/** What was read out of a photo, put up to correct before cora holds any of it.
 *
 *  Recognition is a draft — a screenshot read on a phone gets letters wrong — so this
 *  stands between the reading and the field, and nothing reaches the field until the
 *  reader says so.
 */
export default function ReadImage({ image, read, onKeep, onDiscard }: Props) {
  const [text, setText] = useState(read)
  /* A second photo read in the same session arrives as new props around the box the
     first one is still in. State seeded from a prop is seeded once, so the reading it
     came from is held beside it and the box follows a new one — otherwise Keep it
     would upload the first reading under the second's name. */
  const [reading, setReading] = useState(read)
  if (reading !== read) {
    setReading(read)
    setText(read)
  }

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onDiscard()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onDiscard])

  /* What the reader has changed. A stray click on the ground behind the dialog throws
     away a reading, and by now that may be minutes of correction — so it closes what
     nobody has touched and leaves the rest standing. Discard is the way out. */
  const corrected = text !== read

  const keep = () => {
    const written = text.trim()
    if (!written) return
    onKeep(new File([`${written}\n`], named(image), { type: 'text/markdown' }))
  }

  return (
    <div className={dialog.overlay} onClick={corrected ? undefined : onDiscard}>
      <div
        className={dialog.modal}
        role="dialog"
        aria-modal="true"
        aria-label={HEAD}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="micro">{HEAD}</div>
        <div className={dialog.modalTitle}>{image}</div>
        <p className={styles.said}>{read ? SAID : NOTHING}</p>
        <textarea
          className={styles.read}
          aria-label="What was read"
          value={text}
          rows={12}
          onChange={(event) => setText(event.target.value)}
        />
        <div className={styles.answers}>
          <button className="quiet" onClick={onDiscard}>
            Discard
          </button>
          <button className={styles.keep} onClick={keep} disabled={!text.trim()}>
            Keep it
          </button>
        </div>
      </div>
    </div>
  )
}

/** The document is the photo's name with a Markdown extension: `words.png` is kept as
 *  `words.md`, so the field lists it as what it came from. */
const named = (image: string) => `${image.replace(/\.[^.]+$/, '') || 'reading'}.md`
