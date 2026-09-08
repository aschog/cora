import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))

const NOTE = resolve(HERE, '../../../../tests/e2e/documents/note.md')
const PAGE = 'http://127.0.0.1:8765'

/** The one document every run starts with, in the field a question nobody pinned is
 *  answered in. Uploaded through the API rather than written into the store: what
 *  indexes it is what indexes a reader's own upload. */
export default async function seed() {
  const body = new FormData()
  body.append('file', new Blob([readFileSync(NOTE)]), 'note.md')
  const answered = await fetch(`${PAGE}/api/documents`, { method: 'POST', body })
  if (!answered.ok) throw new Error(`could not seed the documents: ${answered.status}`)
}
