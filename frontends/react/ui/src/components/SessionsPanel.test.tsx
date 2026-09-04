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

/** The row that slides, which is the part a gesture moves and the part that covers the
 *  delete behind it. Read by the conversation it holds. */
const row = (session: Session) =>
  screen.getByRole('button', { name: session.opened_with }).parentElement!

/** A gesture across a row, in pixels: negative is leftward. Let go at the end, which is
 *  where the row snaps open or shut. */
const drawn = (session: Session, by: number) => {
  const sliding = row(session)
  fireEvent.pointerDown(sliding, { clientX: 200, pointerId: 1 })
  fireEvent.pointerMove(sliding, { clientX: 200 + by, pointerId: 1 })
  fireEvent.pointerUp(sliding, { clientX: 200 + by, pointerId: 1 })
}

const offset = (session: Session) => row(session).style.transform

test('a listed conversation is deleted by its own control', () => {
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

test('a leftward gesture uncovers the delete, and deletes nothing itself', () => {
  /* The gesture is the asking: it says which conversation, and the control that comes
     out from under the row is what answers. Nothing is lost by dragging. */
  const deleted = panel()

  drawn(OTHER, -70)

  expect(offset(OTHER)).toBe('translateX(-56px)')
  expect(deleted).not.toHaveBeenCalled()
})

test('the control the gesture uncovered is what deletes', () => {
  const deleted = panel()

  drawn(OTHER, -70)
  fireEvent.click(deleting(OTHER)!)

  expect(deleted).toHaveBeenCalledWith(OTHER)
})

test('a gesture back covers the delete again', () => {
  const deleted = panel()
  drawn(OTHER, -70)

  drawn(OTHER, 70)

  expect(offset(OTHER)).toBe('translateX(0px)')
  expect(deleted).not.toHaveBeenCalled()
})

test('the row of the conversation being read does not answer the gesture', () => {
  panel()

  drawn(HERE, -70)

  expect(offset(HERE)).toBe('translateX(0px)')
})

test('the row follows the pointer while the gesture is under way', () => {
  /* A row that only moves once the finger is lifted is a row that reads as broken
     while the gesture is being made. */
  panel()
  const sliding = row(OTHER)

  fireEvent.pointerDown(sliding, { clientX: 200, pointerId: 1 })
  fireEvent.pointerMove(sliding, { clientX: 180, pointerId: 1 })

  expect(offset(OTHER)).toBe('translateX(-20px)')
})

test('a gesture too small to be one leaves the row where it was', () => {
  panel()

  drawn(OTHER, -8)

  expect(offset(OTHER)).toBe('translateX(0px)')
})
