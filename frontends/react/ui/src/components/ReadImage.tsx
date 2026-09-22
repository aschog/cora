import { useRef, useState } from 'react'
import { useEscape } from '../hooks/useEscape'
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
  /* Why the last attempt to keep it did not land. Shown here rather than over the page
     behind: this dialog covers what it would be reported on. */
  const [refused, setRefused] = useState('')
  /* The merge in flight, and what it will leave in the box. Clicking Keep blurs the
     name box first, so the click arrives while the file being merged in is still being
     fetched — and a write that did not wait would replace that file with the new
     reading alone. */
  const merging = useRef<Promise<string> | null>(null)
  /* Which name the box was last opened on, so the text of an existing file is fetched
     once per name rather than on every keystroke that spells it. */
  const [opened, setOpened] = useState('')
  /* What a merge put above the reading, so naming a second file swaps that head out
     instead of stacking the first file on top of the second. */
  const [merged, setMerged] = useState('')
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
    setMerged('')
  }

  useEscape(onDiscard)

  /* What the reader has changed. A stray click on the ground behind the dialog throws
     away a reading, and by now that may be minutes of correction — so it closes what
     nobody has touched and leaves the rest standing. Discard is the way out. */
  const corrected = text !== read

  /* The name settled, which is the one the file is written under. Compared and written
     as one value: a name trimmed on the way out and not on the way in is two names, and
     the merge then looked at one file while the write replaced another. */
  const named = name.trim()

  const adding = held.includes(named)

  /* The merge, made by showing rather than by computing: what the field holds goes into
     the box above the new reading, and the reader corrects both at once. The reading
     and the corrections made to it are what a second name merges onto, so the head
     swaps rather than stacks. Hands back what now stands in the box. */
  const openOn = (onto: string): Promise<string> => {
    const base = merged && text.startsWith(merged) ? text.slice(merged.length) : text
    setOpened(onto)
    const pulled = onRead(onto).then((there) => {
      const ahead = there === null ? '' : `${there.replace(/\n+$/, '')}\n`
      const whole = ahead + base
      setMerged(ahead)
      setText(whole)
      /* Done, and from here the box is where the merged text lives: what the reader
         types over it is the truth, and this promise must not speak for it again. */
      merging.current = null
      return whole
    })
    merging.current = pulled
    return pulled
  }

  /* Done as the name is settled rather than as it is typed, so a name passed through on
     the way to another does not pull a file in. */
  const open = () => {
    if (!named || named === opened || !held.includes(named)) return
    void openOn(named)
  }

  const keep = async () => {
    if (!named) return
    /* A merge still in flight is waited for and its text is what lands — the click
       that started it arrived before it finished. One that has already landed speaks
       through the box instead, corrections and all. */
    const landing = merging.current
    const standing = landing ? await landing : text
    /* A write is a whole-file replace, so the file is read before it is replaced even
       where the listing never offered it — a listing that did not arrive, or a name
       typed past the end of it, must not cost the reader what the field holds. What
       comes back is put up to be corrected rather than written unseen. */
    if (named !== opened) {
      const shown = await openOn(named)
      if (shown !== standing) return
    }
    const written = standing.trim()
    if (!written) return
    setKeeping(true)
    setRefused('')
    try {
      await onKeepAsFile(named, `${written}\n`)
    } catch (failed) {
      setRefused((failed as Error).message)
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
          {refused && <p className="trouble">{refused}</p>}
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
