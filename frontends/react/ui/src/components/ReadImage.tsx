import { useEffect, useState } from 'react'
import dialog from './dialog.module.css'
import styles from './ReadImage.module.css'

const HEAD = 'READ FROM THE IMAGE'
const NOTHING = 'Nothing was read in that image.'
const SAID =
  'Correct what was read before it is kept. The image stays on this machine either way.'
const AS_DOCUMENT = 'A document to answer from'
const AS_FILE = "One of this field's own files"
const NAME = 'Name'
const NAMED = 'What to call it'
const ADDING = 'That name is already here, so what it holds is above the new reading.'

type Props = {
  /** What the photo was called. The document is named after it, so the reader can tell
   *  which photo a list in the field came from. */
  image: string
  /** The words as they were recognised. Empty is a photo with no text in it, which is
   *  news rather than a document to save. */
  read: string
  /** The names this field already keeps files under, offered as the reader types so a
   *  second photograph of one list adds to it instead of making a near-miss of it. */
  held: string[]
  /** Keep what is on screen: the same upload every other file goes through. */
  onKeep: (file: File) => void
  /** Keep what is on screen as one of the field's own files, under this name. Nothing
   *  indexes it, so it is drill data rather than another document to search. */
  onKeepAsFile: (name: string, text: string) => void
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
 *  Two things can be kept: a document, which is indexed and cited, and one of the
 *  field's own files, which is not. Naming a file the field already holds opens what is
 *  there above the new reading, so one correction pass covers the merge as well.
 */
export default function ReadImage({
  image,
  read,
  held,
  onKeep,
  onKeepAsFile,
  onRead,
  onDiscard,
}: Props) {
  const [text, setText] = useState(read)
  const [asFile, setAsFile] = useState(false)
  const [name, setName] = useState('')
  /* Which name the box was last opened on, so the text of an existing file is fetched
     once per name rather than on every keystroke that spells it. */
  const [opened, setOpened] = useState('')
  /* A second photo read in the same session arrives as new props around the box the
     first one is still in. State seeded from a prop is seeded once, so the reading it
     came from is held beside it and the box follows a new one — otherwise Keep it
     would upload the first reading under the second's name. */
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
  const open = async () => {
    if (!asFile || !name || name === opened || !held.includes(name)) return
    const there = await onRead(name)
    setOpened(name)
    if (there !== null) setText(`${there.replace(/\n+$/, '')}\n${text}`)
  }

  const keep = () => {
    const written = text.trim()
    if (!written) return
    if (!asFile) {
      onKeep(new File([`${written}\n`], named(image), { type: 'text/markdown' }))
      return
    }
    if (!name.trim()) return
    onKeepAsFile(name.trim(), `${written}\n`)
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
        <fieldset className={styles.kind}>
          <legend className="micro">KEEP IT AS</legend>
          <label>
            <input
              type="radio"
              name="keep-as"
              checked={!asFile}
              onChange={() => setAsFile(false)}
            />
            {AS_DOCUMENT}
          </label>
          <label>
            <input
              type="radio"
              name="keep-as"
              checked={asFile}
              onChange={() => setAsFile(true)}
            />
            {AS_FILE}
          </label>
        </fieldset>
        {asFile && (
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
        )}
        <div className={styles.answers}>
          <button className="quiet" onClick={onDiscard}>
            Discard
          </button>
          <button
            className={styles.keep}
            onClick={keep}
            disabled={!text.trim() || (asFile && !name.trim())}
          >
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
