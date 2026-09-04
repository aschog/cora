import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import SessionsPanel from './SessionsPanel'
import type { Session } from '../api'

const HERE: Session = { thread_id: 'here', opened_with: 'The one being read' }
const OTHER: Session = { thread_id: 'other', opened_with: 'An older question' }
const BUSY: Session = { thread_id: 'busy', opened_with: 'Still being answered' }

afterEach(cleanup)

const drawn = (working: string | null = null) => {
  const deleted = vi.fn()
  render(
    <SessionsPanel
      sessions={[HERE, OTHER, BUSY]}
      here={HERE.thread_id}
      working={working}
      onOpen={() => {}}
      onDelete={deleted}
    />,
  )
  return deleted
}

const deleting = (session: Session) =>
  screen.queryByRole('button', { name: `Delete ${session.opened_with}` })

test('a listed conversation is deleted by its own control', () => {
  const deleted = drawn()

  fireEvent.click(deleting(OTHER)!)

  expect(deleted).toHaveBeenCalledWith(OTHER)
})

test('the conversation being read offers no delete', () => {
  /* It is the page: deleting it would leave the reader in a conversation that is gone.
     Leaving it is a click away, and the list is what they leave it through. */
  drawn()

  expect(deleting(HERE)).toBeNull()
  expect(deleting(OTHER)).toBeTruthy()
})

test('a conversation still being answered in offers no delete', () => {
  /* The turn would land after the delete and record the conversation straight back
     into the list. Waiting is seconds; a conversation that comes back is forever. */
  drawn(BUSY.thread_id)

  expect(deleting(BUSY)).toBeNull()
  expect(deleting(OTHER)).toBeTruthy()
})
