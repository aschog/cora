import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import SessionsPanel from './SessionsPanel'
import type { Session } from '../api'

const HERE: Session = { thread_id: 'here', opened_with: 'The one being read', pin: null }
const OTHER: Session = { thread_id: 'other', opened_with: 'An older question', pin: 'fitness' }
const BUSY: Session = { thread_id: 'busy', opened_with: 'Still being answered', pin: null }

afterEach(cleanup)

const panel = (working: string | null = null) => {
  const deleted = vi.fn()
  render(
    <SessionsPanel
      sessions={[HERE, OTHER, BUSY]}
      here={HERE.thread_id}
      working={working}
      chats={(session) => session.pin === 'fitness'}
      onOpen={() => {}}
      onDelete={deleted}
    />,
  )
  return deleted
}

const deleting = (session: Session) =>
  screen.queryByRole('button', { name: `Delete ${session.opened_with}` })

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


test('a conversation the rail would chat is marked, and the mark is explained', () => {
  panel()

  expect(screen.getByLabelText(`${OTHER.opened_with} opens as a chat here`)).toBeTruthy()
  expect(screen.queryByLabelText(`${HERE.opened_with} opens as a chat here`)).toBeNull()
  expect(screen.getByText(/opens as a chat in this rail/i)).toBeTruthy()
})

test('a list with nothing to chat explains no mark', () => {
  render(
    <SessionsPanel
      sessions={[HERE, BUSY]}
      here={HERE.thread_id}
      working={null}
      chats={() => false}
      onOpen={() => {}}
      onDelete={() => {}}
    />,
  )

  expect(screen.queryByText(/opens as a chat in this rail/i)).toBeNull()
})

test('the panel is the conversation when it is given one, with a way back', () => {
  const back = vi.fn()
  render(
    <SessionsPanel
      sessions={[HERE, OTHER]}
      here={HERE.thread_id}
      working={null}
      chats={() => true}
      chat={<p>the conversation itself</p>}
      about={{ opened: 'Squat stalling' }}
      onBack={back}
      onOpen={() => {}}
      onDelete={() => {}}
    />,
  )

  expect(screen.getByRole('heading', { name: 'Squat stalling' })).toBeTruthy()
  expect(screen.getByText('the conversation itself')).toBeTruthy()
  /* The list is behind it, not beside it. */
  expect(screen.queryByRole('button', { name: OTHER.opened_with })).toBeNull()

  screen.getByRole('button', { name: 'Back to other conversations' }).click()

  expect(back).toHaveBeenCalled()
})
