import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query'
import { useRemoving } from './useRemoving'
import { rail } from './useRails'

const FACTS = [
  { key: 'f1', text: 'No burpees.' },
  { key: 'f2', text: 'Trains on Tuesdays.' },
]

afterEach(cleanup)

/** A held request, so the assertion can be made while the store has answered nothing —
 *  which is the whole of what "optimistic" means here. */
const held = () => {
  let go: (failed?: Error) => void = () => {}
  const until = new Promise<void>((settle, refuse) => {
    go = (failed) => (failed ? refuse(failed) : settle())
  })
  return { until, go: (failed?: Error) => go(failed) }
}

function Listing({
  send,
  trouble,
}: {
  send: () => Promise<void>
  trouble: (said: string | null) => void
}) {
  const listed = useQuery({ queryKey: rail.memory, queryFn: async () => FACTS })
  const removing = useRemoving({ reread: async () => {}, setTrouble: trouble })
  return (
    <>
      <button
        onClick={() =>
          removing.mutate({
            send,
            from: rail.memory,
            without: (kept: typeof FACTS) => kept.filter((fact) => fact.key !== 'f1'),
          })
        }
      >
        forget it
      </button>
      {(listed.data ?? []).map((fact) => (
        <p key={fact.key}>{fact.text}</p>
      ))}
    </>
  )
}

const drawn = () => {
  const request = held()
  const trouble = vi.fn()
  const store = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={store}>
      <Listing send={() => request.until} trouble={trouble} />
    </QueryClientProvider>,
  )
  return { request, trouble }
}

test('the row goes when the reader says so, not when the store answers', async () => {
  const { request } = drawn()
  await waitFor(() => expect(screen.getByText(FACTS[0].text)).toBeTruthy())

  screen.getByText('forget it').click()

  /* Nothing has been released, so the store has said nothing at all — and the row the
     reader confirmed away is already gone. */
  await waitFor(() => expect(screen.queryByText(FACTS[0].text)).toBeNull())
  expect(screen.getByText(FACTS[1].text)).toBeTruthy()
  request.go()
})

test('a delete the store refuses puts the row back, and says why', async () => {
  const { request, trouble } = drawn()
  await waitFor(() => expect(screen.getByText(FACTS[0].text)).toBeTruthy())

  screen.getByText('forget it').click()
  await waitFor(() => expect(screen.queryByText(FACTS[0].text)).toBeNull())

  request.go(new Error('The memory store is temporarily unavailable.'))

  /* Back where it was, with the sentence — a row reappearing on its own would read as
     the click having missed rather than as the store having refused. */
  await waitFor(() => expect(screen.getByText(FACTS[0].text)).toBeTruthy())
  expect(trouble).toHaveBeenCalledWith('The memory store is temporarily unavailable.')
})

test('a delete that goes through clears the sentence the one before it left', async () => {
  /* Same contract as an upload and a turn: what went through clears what the page last
     could not do. Without it the sentence from a refused delete stands over a list the
     next delete has visibly changed. */
  const trouble = vi.fn()
  const store = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  let answer: () => Promise<void> = () =>
    Promise.reject(new Error('The memory store is temporarily unavailable.'))
  function Twice() {
    const removing = useRemoving({ reread: async () => {}, setTrouble: trouble })
    return (
      <button
        onClick={() =>
          removing.mutate({
            send: () => answer(),
            from: rail.memory,
            without: (kept: typeof FACTS) => kept,
          })
        }
      >
        forget it
      </button>
    )
  }
  render(
    <QueryClientProvider client={store}>
      <Twice />
    </QueryClientProvider>,
  )

  screen.getByText('forget it').click()
  await waitFor(() =>
    expect(trouble).toHaveBeenCalledWith('The memory store is temporarily unavailable.'),
  )

  answer = () => Promise.resolve()
  screen.getByText('forget it').click()

  await waitFor(() => expect(trouble).toHaveBeenCalledWith(null))
})

test('what is drawn after a delete is the listing the store gives back', async () => {
  /* The optimistic guess is only a guess: the store may have changed more than the one
     row. The re-read after settling is what makes the page honest, and this is the test
     that fails if it goes. */
  let serverFacts = FACTS
  const store = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  function Confirmed() {
    const listed = useQuery({ queryKey: rail.memory, queryFn: async () => serverFacts })
    const removing = useRemoving({
      reread: async () => {
        await store.invalidateQueries({ queryKey: rail.memory })
      },
      setTrouble: () => {},
    })
    return (
      <>
        <button
          onClick={() =>
            removing.mutate({
              send: async () => {},
              from: rail.memory,
              without: (kept: typeof FACTS) => kept.filter((fact) => fact.key !== 'f1'),
            })
          }
        >
          forget it
        </button>
        {(listed.data ?? []).map((fact) => (
          <p key={fact.key}>{fact.text}</p>
        ))}
      </>
    )
  }
  render(
    <QueryClientProvider client={store}>
      <Confirmed />
    </QueryClientProvider>,
  )
  await waitFor(() => expect(screen.getByText(FACTS[0].text)).toBeTruthy())

  /* The store's truth after the delete differs from the page's guess: another writer
     reworded the fact that remains. */
  serverFacts = [{ key: 'f2', text: 'Trains on Tuesdays and Fridays.' }]
  screen.getByText('forget it').click()

  await waitFor(() =>
    expect(screen.getByText('Trains on Tuesdays and Fridays.')).toBeTruthy(),
  )
  expect(screen.queryByText(FACTS[0].text)).toBeNull()
})
