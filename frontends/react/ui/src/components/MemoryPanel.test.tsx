import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import MemoryPanel from './MemoryPanel'

const FACT = { key: 'f1', text: 'No burpees.' }

afterEach(cleanup)

test('a fact is forgotten by the same icon a conversation is deleted by', () => {
  /* One shape for both rails: a fact and a conversation are both a row with a control
     at the end of it, and a reader learns the rail once. */
  const forgotten = vi.fn()
  render(
    <MemoryPanel facts={[FACT]} onForget={forgotten} onForgetEverything={() => {}} />,
  )

  const control = screen.getByRole('button', { name: `Delete ${FACT.text}` })
  expect(control.querySelector('svg')).toBeTruthy()
  expect(screen.queryByText('forget')).toBeNull()

  fireEvent.click(control)

  expect(forgotten).toHaveBeenCalledWith(FACT.key)
})

test('everything is forgotten at once, and only where there is anything to forget', () => {
  const cleared = vi.fn()
  const { rerender } = render(
    <MemoryPanel facts={[]} onForget={() => {}} onForgetEverything={cleared} />,
  )
  expect(screen.queryByRole('button', { name: 'forget everything' })).toBeNull()

  rerender(
    <MemoryPanel facts={[FACT]} onForget={() => {}} onForgetEverything={cleared} />,
  )
  fireEvent.click(screen.getByRole('button', { name: 'forget everything' }))

  expect(cleared).toHaveBeenCalled()
})
