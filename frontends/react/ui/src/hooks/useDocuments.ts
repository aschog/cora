import { useState } from 'react'
import type { Dispatch, RefObject, SetStateAction } from 'react'
import * as cora from '../api'
import { message } from '../fail'
import type { Notice } from '../components/UploadNotice'
import type { Read } from './useSource'

/** What the reader can do to the documents rail. The listing itself comes from
 *  `useRails`, which loads it with the other three; this is what changes it. */
export function useDocuments({
  field,
  here,
  refresh,
  setTrouble,
  setRead,
}: {
  field: string
  here: RefObject<string>
  refresh: () => Promise<void>
  setTrouble: (said: string | null) => void
  setRead: Dispatch<SetStateAction<Read | null>>
}) {
  /* What the last upload did, where the list does not already say it. Cleared by every
     upload: the answer names the document and the field, and the list saying the same
     is the news. Moving to another conversation ends it — it is news about the desk
     the reader was at. */
  const [notice, setNotice] = useState<Notice | null>(null)

  /* Every upload still running, by the name it was uploaded as and the field it is
     landing in. Ingestion parses, chunks and embeds before it answers, which is seconds
     the reader is otherwise told nothing about: the file is in neither place they look —
     not in the list, which does not hold it yet, and not in a sentence, because the one
     that worked no longer writes one. */
  const [running, setRunning] = useState<{ name: string; scope: string }[]>([])

  /* The last upload that went through, for the region that reads news out. Its own
     state rather than a notice: nothing is drawn for it, because the list is what says
     it to a reader who can see the list. Stamped with its field for the reason a
     running upload is — news about a desk they have left is not read out over the one
     they are at. */
  const [indexed, setIndexed] = useState<{ name: string; scope: string } | null>(null)

  /** An upload the reader started and then left behind. Ingestion takes seconds and
   *  nothing stops them opening another conversation while it runs, so the notice is
   *  stamped with the one they started it in — news about a desk they have left is not
   *  drawn, and cannot be left standing where nothing clears it. Taking a notice *away*
   *  is stamped for the same reason: a refusal from a conversation they have left must not
   *  clear news about an upload that worked in this one. The refresh and the refusal's own
   *  sentence are not stamped — a document is added, or refused, wherever they are. */
  const add = (file: File) => {
    const from = here.current
    /* Held by identity rather than by name, so the same file uploaded twice at once
       takes its own row away and not the other's. */
    const started = { name: file.name, scope: field }
    setRunning((uploads) => [...uploads, started])
    /* What is running clears what finished. A live region announces what changes in
       it, and the same sentence set twice is a region that never changed — so the same
       file uploaded again would be indexed in silence. */
    setIndexed(null)
    return cora
      .upload(file, field)
      .then((added) => {
        if (here.current === from) {
          setNotice(null)
          setIndexed({ name: added.document, scope: started.scope })
        }
        return refresh()
      })
      .catch((failed: unknown) => {
        if (here.current === from) {
          setNotice(null)
          setIndexed(null)
        }
        /* Thrown on as well as written to the line: a caller with a screen of its own
           to refuse over — the reading, whose corrections a closed dialog loses — has
           to hear about it, and the picker has nowhere but the line. */
        throw failed
      })
      .finally(() =>
        setRunning((uploads) => uploads.filter((each) => each !== started)),
      )
  }

  /** An upload started from the picker, where the line is the only place a refusal can
   *  be written: nothing else is on screen to refuse over. */
  const upload = (file: File) =>
    add(file).catch((failed: unknown) => setTrouble(message(failed)))

  /** A document deleted, and the panel reading it let go of: it would otherwise draw a
   *  file the field no longer holds, under a name nothing can open. The field is passed
   *  rather than read here: the question that raised this may have stood while a turn
   *  landed and moved the rail, and what is deleted is the field the reader was looking
   *  at when they asked. */
  const erase = (scope: string, name: string) =>
    cora
      .deleteDocument(scope, name)
      /* The field as well as the name: one name covers a document in each field, so
         deleting `kyoto.md` from travel must not close a panel reading the fitness one. */
      .then(() =>
        setRead((shown) =>
          shown?.document === name && shown?.scope === scope ? null : shown,
        ),
      )

  return {
    notice,
    setNotice,
    add,
    upload,
    erase,
    indexed: indexed?.scope === field ? indexed.name : null,
    /* This field's, because a rail switched to another one lists another field's
       documents: a row for an upload landing elsewhere would name a file that is not
       going to appear there. */
    indexing: running
      .filter((each) => each.scope === field)
      .map((each) => each.name),
  }
}
