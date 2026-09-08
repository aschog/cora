import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import MemoryPanel from './MemoryPanel'

const FACT = { key: 'f1', text: 'No burpees.' }
afterEach(cleanup)

const rail = (...facts: typeof FACT[]) => {
  const forgot = vi.fn()
  const cleared = vi.fn()
  render(
    <MemoryPanel facts={facts} onForget={forgot} onForgetEverything={cleared} />,
  )
  return { forgot, cleared }
}

test('everything is forgotten at once, where there is anything to forget', () => {
  rail()
  expect(screen.queryByRole('button', { name: 'forget everything' })).toBeNull()
  cleanup()

  const { cleared } = rail(FACT)
  fireEvent.click(screen.getByRole('button', { name: 'forget everything' }))

  expect(cleared).toHaveBeenCalled()
})
