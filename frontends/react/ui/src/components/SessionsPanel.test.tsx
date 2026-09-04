import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import SessionsPanel from './SessionsPanel'
import type { Session } from '../api'

const HERE: Session = { thread_id: 'here', opened_with: 'The one being read' }
const OTHER: Session = { thread_id: 'other', opened_with: 'An older question' }
const BUSY: Session = { thread_id: 'busy', opened_with: 'Still being answered' }

afterEach(cleanup)

const panel = (working: string | null = null) => {
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

test("a listed conversation's own control asks for it to be deleted", () => {
  const deleted = panel()

  fireEvent.click(deleting(OTHER)!)

  expect(deleted).toHaveBeenCalledWith(OTHER)
})

test('the conversation being read offers no delete', () => {
  /* It is the page: deleting it would leave the reader in a conversation that is gone.
     Leaving it is a click away, and the list is what they leave it through. */
  panel()

  expect(deleting(HERE)).toBeNull()
  expect(deleting(OTHER)).toBeTruthy()
})

test('a conversation still being answered in offers no delete', () => {
  /* The turn would land after the delete and record the conversation straight back
     into the list. Waiting is seconds; a conversation that comes back is forever. */
  panel(BUSY.thread_id)

  expect(deleting(BUSY)).toBeNull()
  expect(deleting(OTHER)).toBeTruthy()
})

test('the control is an icon, named for the conversation it deletes', () => {
  /* A word per row repeated down a narrow rail reads as noise; the name is what says
     which conversation is about to go, to a screen reader and to a test alike. */
  panel()

  expect(screen.queryByText('delete')).toBeNull()
  expect(deleting(OTHER)!.querySelector('svg')).toBeTruthy()
})

test('the conversation being read is marked in the list', () => {
  /* Its row is where the reader is, so the list says so rather than leaving them to
     work it out from which row does nothing when clicked. */
  panel()

  const row = screen.getByRole('button', { name: HERE.opened_with }).parentElement!
  expect(row.className).toContain('here')
})
