import { useQuery } from '@tanstack/react-query'
import * as cora from '../api'
import { message } from '../fail'

/** One sentence for every way a passage's document cannot be read: deleted, indexed
 *  before cora kept any text, or cited by an index that names no field to look in. All
 *  three arrive as nothing, so guessing between them would sometimes be a lie — and a
 *  reader who clicked `[1]` is owed the same sentence as one who opened the rail. */
export const UNKEPT = 'cora cannot open this document.'

/**
 * The kept text of an upload, or why it cannot be read. Both answers live here so that
 * every way of opening a passage gives the same one: a citation from an index written
 * before cora kept any text names no upload, and a reader who clicked `[1]` deserves
 * that sentence as much as a reader who opened the document in the rail.
 *
 * Held under the upload it is of, which is the whole of the bookkeeping: text belonging
 * to another upload cannot be drawn under this one's name, a document opened twice is
 * read once, and the panel and the citation modal asking for the same passage at the
 * same time make one request between them.
 */
export function usePassage(source: { scope: string; upload: string } | null) {
  const read = useQuery({
    queryKey: ['passage', source?.scope ?? '', source?.upload ?? ''],
    queryFn: ({ signal }) => cora.passage(source!.scope, source!.upload, signal),
    enabled: source !== null,
  })

  return {
    text: read.data ?? null,
    /* A source that names no upload is the one failure that is not a failed read: there
       is nothing to ask for, and the sentence is the same one either way. */
    trouble: source === null ? UNKEPT : read.error ? message(read.error) : null,
  }
}
