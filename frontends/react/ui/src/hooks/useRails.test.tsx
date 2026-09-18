import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import WithStore from '../test/withStore'
import { useRails } from './useRails'

const FIELDS = ['fitness', 'travel']

function serving(offered: unknown) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (path: string) => ({
      ok: true,
      json: async () => (path.split('?')[0] === '/api/scopes' ? offered : []),
    })),
  )
}

/** The hook read through a component, as the page reads it: what it answers is on the
 *  screen, so the assertion is about the answer and not about a call. The fields are
 *  said with it, both being read from the one listing — so an assertion about the page
 *  cannot be satisfied by the empty answer the hook gives before that listing lands, and
 *  a page it does not answer with at all reads as neither rather than passing for none. */
function Rails({ pin, answered }: { pin: string | null; answered: string | null }) {
  const { field, fields, page } = useRails({ pin, answered })
  return (
    <p>{`${field} in ${fields.join(',')} — ${page === null ? 'no page' : String(page)}`}</p>
  )
}

const drawn = (pin: string | null, answered: string | null = null) =>
  render(
    <WithStore>
      <Rails pin={pin} answered={answered} />
    </WithStore>,
  )

beforeEach(() => vi.unstubAllGlobals())
afterEach(cleanup)

test('the page is the one the fixed field brings', async () => {
  serving({
    available: FIELDS,
    default: 'cora',
    pages: { fitness: '/pages/fitness/' },
  })

  drawn('fitness')

  expect(await screen.findByText('fitness in fitness,travel — /pages/fitness/')).toBeTruthy()
})

test('a fixed field with no page, and nothing fixed, bring none', async () => {
  serving({
    available: FIELDS,
    default: 'cora',
    pages: { fitness: '/pages/fitness/' },
  })

  const fixedElsewhere = drawn('travel')
  expect(await screen.findByText('travel in fitness,travel — no page')).toBeTruthy()
  fixedElsewhere.unmount()

  drawn(null)

  expect(await screen.findByText('cora in fitness,travel — no page')).toBeTruthy()
})

test('a field merely answered in brings no page', async () => {
  /* The pin is the reader saying this conversation is that subject for good. A field
     routing chose would otherwise replace the screen on the strength of one question. */
  serving({
    available: FIELDS,
    default: 'cora',
    pages: { fitness: '/pages/fitness/' },
  })

  drawn(null, 'fitness')

  expect(await screen.findByText('fitness in fitness,travel — no page')).toBeTruthy()
})

test('one field is the field it is fixed to, so its page is drawn unpinned', async () => {
  /* One field loaded is one routing cannot choose against, and the picker that would
     pin it is not drawn at all — the deployment that drops in a single plugin. */
  serving({
    available: ['fitness'],
    default: 'cora',
    pages: { fitness: '/pages/fitness/' },
  })

  drawn(null)

  expect(await screen.findByText('fitness in fitness — /pages/fitness/')).toBeTruthy()
})

test('a field answered in that the deployment no longer offers is not where the rail sits', async () => {
  /* The plugin that field belonged to has been deleted, and the conversation's own turns
     still name it. Left to outrank the listing it would point the documents rail at a
     field that is gone, and name the page of the field that is left after it. */
  serving({ available: ['fitness'], default: 'cora', pages: { fitness: '/pages/fitness/' } })

  drawn(null, 'travel')

  expect(await screen.findByText('fitness in fitness — /pages/fitness/')).toBeTruthy()
})
