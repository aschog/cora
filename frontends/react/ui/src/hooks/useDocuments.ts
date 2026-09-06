import { useState } from 'react'
import type { Dispatch, RefObject, SetStateAction } from 'react'
import * as cora from '../api'
import { message } from '../fail'
import type { Notice } from '../components/UploadNotice'
import type { Read } from './useSource'

/** What an upload did, in the words the page uses for what a document is made of. A store
 *  that already had those bytes indexes nothing and says so — the count is how the two
 *  outcomes differ, and it is the one thing the page used to throw away. */
const ingested = ({
  document,
  chunks,
}: {
  document: string
  chunks: number
}): Notice =>
  chunks
    ? {
        said: `Added “${document}” — ${chunks} ${chunks === 1 ? 'passage' : 'passages'}.`,
        wrong: false,
      }
    : { said: `“${document}” is already in your documents.`, wrong: true }

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
  /* What the last upload did. Its own state, because it is not trouble and a refresh
     going through does not take it away: a duplicate upload is answered with `0` chunks,
     and saying nothing about it reads the same as success and the same as nothing
     happening. Moving to another conversation does end it — it is news about the desk the
     reader was at. */
  const [notice, setNotice] = useState<Notice | null>(null)

  /** An upload the reader started and then left behind. Ingestion takes seconds and
   *  nothing stops them opening another conversation while it runs, so the notice is
   *  stamped with the one they started it in — news about a desk they have left is not
   *  drawn, and cannot be left standing where nothing clears it. Taking a notice *away*
   *  is stamped for the same reason: a refusal from a conversation they have left must not
   *  clear news about an upload that worked in this one. The refresh and the refusal's own
   *  sentence are not stamped — a document is added, or refused, wherever they are. */
  const upload = (file: File) => {
    const from = here.current
    return cora
      .upload(file, field)
      .then((added) => {
        if (here.current === from) setNotice(ingested(added))
        return refresh()
      })
      .catch((failed) => {
        if (here.current === from) setNotice(null)
        setTrouble(message(failed))
      })
  }

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

  return { notice, setNotice, upload, erase }
}
