import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import MemoryPanel from './MemoryPanel'

const FACT = { key: 'f1', text: 'No burpees.' }
const ALSO = { key: 'f2', text: 'Four sessions a week.' }

afterEach(cleanup)

const rail = (...facts: typeof FACT[]) => {
  const forgot = vi.fn()
  const cleared = vi.fn()
  render(
    <MemoryPanel facts={facts} onForget={forgot} onForgetEverything={cleared} />,
  )
  return { forgot, cleared }
}

test('each fact carries the icon a conversation carries, named for that fact', () => {
  /* One shape for both rails: a fact and a conversation are each a row with a control
     at the end of it, so a reader learns the rail once — and a column of identical
     icons still says which row is which. */
  const { forgot } = rail(FACT, ALSO)

  const control = screen.getByRole('button', { name: `Delete ${FACT.text}` })
  expect(control.querySelector('svg')).toBeTruthy()
  expect(screen.getByRole('button', { name: `Delete ${ALSO.text}` })).toBeTruthy()

  fireEvent.click(control)

  expect(forgot).toHaveBeenCalledWith(FACT)
})

test('no row says the word', () => {
  rail(FACT)

  expect(screen.queryByText('forget')).toBeNull()
})

test('everything is forgotten at once, where there is anything to forget', () => {
  rail()
  expect(screen.queryByRole('button', { name: 'forget everything' })).toBeNull()
  cleanup()

  const { cleared } = rail(FACT)
  fireEvent.click(screen.getByRole('button', { name: 'forget everything' }))

  expect(cleared).toHaveBeenCalled()
})
