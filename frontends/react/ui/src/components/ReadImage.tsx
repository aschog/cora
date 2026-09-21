import { useEffect, useRef, useState } from 'react'
import dialog from './dialog.module.css'
import styles from './ReadImage.module.css'

const HEAD = 'READ FROM THE IMAGE'
const NOTHING = 'Nothing was read in that image.'
const SAID =
  'Correct what was read before it is kept. The image stays on this machine either way.'
const NAME = 'Name'
const NAMED = 'What to call it'
const ADDING = 'That name is already here, so what it holds is above the new reading.'
const KEEPING = 'Keeping…'

type Props = {
  /** What the photo was called, shown so the reader can tell which one they are
   *  correcting when a second arrives behind the first. */
  image: string
  /** The words as they were recognised. Empty is a photo with no text in it, which is
   *  news rather than a list to save. */
  read: string
  /** The names this field already keeps files under, offered as the reader types so a
   *  second photograph of one list adds to it instead of making a near-miss of it. */
  held: string[]
  /** Keep what is on screen as one of the field's own files, under this name. Nothing
   *  indexes it, so it is data the field works from rather than prose to search. The
   *  dialog stays up until this settles, so a refusal is refused over the text that
   *  was refused rather than over an empty screen. */
  onKeepAsFile: (name: string, text: string) => Promise<void>
  /** What the field holds under a name, for the box to open on when one is named that
   *  already exists. Nothing where the name is new. */
  onRead: (name: string) => Promise<string | null>
  onDiscard: () => void
}

/** What was read out of a photo, put up to correct before cora holds any of it.
 *
 *  Recognition is a draft — a screenshot read on a phone gets letters wrong — so this
 *  stands between the reading and the field, and nothing reaches the field until the
 *  reader says so.
 *
 *  What it keeps is one of the field's own files: a photograph of a page is data the
 *  field works from rather than prose to be answered from, so nothing indexes it.
 *  Naming a file the field already holds opens what is there above the new reading, so
 *  one correction pass covers the merge as well.
 */
export default function ReadImage({
  image,
  read,
  held,
  onKeepAsFile,
  onRead,
  onDiscard,
}: Props) {
  const [text, setText] = useState(read)
  const [name, setName] = useState('')
  const [keeping, setKeeping] = useState(false)
  /* The merge in flight, and what it will leave in the box. Clicking Keep blurs the
     name box first, so the click arrives while the file being merged in is still being
     fetched — and a write that did not wait would replace that file with the new
     reading alone. */
  const merging = useRef<Promise<string> | null>(null)
  /* Which name the box was last opened on, so the text of an existing file is fetched
     once per name rather than on every keystroke that spells it. */
  const [opened, setOpened] = useState('')
  /* A second photo read in the same session arrives as new props around the box the
     first one is still in. State seeded from a prop is seeded once, so the reading it
     came from is held beside it and the box follows a new one — otherwise Keep it
     would write the first reading under the second's name. */
  const [reading, setReading] = useState(read)
  if (reading !== read) {
    setReading(read)
    setText(read)
    setName('')
    setOpened('')
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

  const adding = held.includes(name)

  /* The merge, made by showing rather than by computing: what the field holds goes into
     the box above the new reading, and the reader corrects both at once. Done as the
     name is settled rather than as it is typed, so a name passed through on the way to
     another does not pull a file in. */
  const open = (): Promise<string> => {
    if (!name || name === opened || !held.includes(name)) {
      return merging.current ?? Promise.resolve(text)
    }
    setOpened(name)
    const merged = onRead(name).then((there) => {
      const whole = there === null ? text : `${there.replace(/\n+$/, '')}\n${text}`
      setText(whole)
      return whole
    })
    merging.current = merged
    return merged
  }

  const keep = async () => {
    /* Whatever the name box started before the click, finished — so what is written is
       the merge the reader would have seen, never the half of it they did not. */
    const written = (await open()).trim()
    if (!written || !name.trim()) return
    setKeeping(true)
    try {
      await onKeepAsFile(name.trim(), `${written}\n`)
    } finally {
      setKeeping(false)
    }
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
        <div className={styles.naming}>
          <label className={styles.nameLabel} htmlFor="file-name">
            {NAME}
          </label>
          <input
            id="file-name"
            className={styles.name}
            value={name}
            placeholder={NAMED}
            aria-label={NAMED}
            list="field-files"
            onChange={(event) => setName(event.target.value)}
            disabled={keeping}
            onBlur={open}
            onKeyDown={(event) => event.key === 'Enter' && open()}
          />
          <datalist id="field-files">
            {held.map((one) => (
              <option key={one} value={one} />
            ))}
          </datalist>
          {adding && <p className={styles.said}>{ADDING}</p>}
        </div>
        <div className={styles.answers}>
          <button className="quiet" onClick={onDiscard} disabled={keeping}>
            Discard
          </button>
          <button
            className={styles.keep}
            onClick={keep}
            disabled={keeping || !text.trim() || !name.trim()}
          >
            {keeping ? KEEPING : 'Keep it'}
          </button>
        </div>
      </div>
    </div>
  )
}
