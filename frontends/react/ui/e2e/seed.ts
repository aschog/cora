import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))

const NOTE = resolve(HERE, '../../../../tests/e2e/documents/note.md')
const PAGE = 'http://127.0.0.1:8765'

/** The one document every run starts with, in every field the deployment offers.
 *
 *  Uploaded through the API rather than written into the store: what indexes it is what
 *  indexes a reader's own upload. Into every field rather than the default one, because
 *  a field owns its documents and a turn searches only the one it runs in — the stub
 *  names no field, so its turns fall to the default, while a real model routes and would
 *  land somewhere the document was not.
 */
export default async function seed() {
  const offered = await fetch(`${PAGE}/api/scopes`)
  if (!offered.ok) throw new Error(`could not read the fields: ${offered.status}`)
  const { available, default: fallback } = await offered.json()

  for (const scope of [fallback, ...available]) {
    const body = new FormData()
    body.append('file', new Blob([readFileSync(NOTE)]), 'note.md')
    body.append('scope', scope)
    const answered = await fetch(`${PAGE}/api/documents`, { method: 'POST', body })
    if (!answered.ok) {
      throw new Error(`could not seed ${scope}: ${answered.status} ${await answered.text()}`)
    }
  }
}
