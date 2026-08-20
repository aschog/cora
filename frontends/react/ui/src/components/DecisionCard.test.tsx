import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import DecisionCard, { NO_OPTION } from './DecisionCard'

afterEach(cleanup)

const OFFERED = {
  question: 'Which bodyweight should I treat as current?',
  options: [{ label: '77 kg', note: '' }, { label: '75 kg', note: '' }],
  decline: '',
}

test('a card the model wrote no way out of still has one', () => {
  /* The page disables the composer while a card is open, so a card with nothing to
     click is a conversation the reader cannot leave. */
  const chose = vi.fn()
  render(
    <DecisionCard
      decision={OFFERED}
      changing={false}
      onChoose={chose}
      onChange={() => {}}
    />,
  )

  fireEvent.click(screen.getByRole('button', { name: NO_OPTION }))

  expect(chose).toHaveBeenCalledWith(null)
})
