import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import { useState } from 'react'
import ErrorBoundary from './ErrorBoundary'

const SAID = 'This panel could not be drawn.'

function Throws({ when }: { when: boolean }) {
  if (when) throw new Error('a span past the end of the document')
  return <p>the document</p>
}

afterEach(cleanup)

/* React logs every caught render error to the console itself. Silenced around the render
   that throws rather than for the whole run, so a throw nobody expected still shows. */
const quietly = (draw: () => void) => {
  const said = vi.spyOn(console, 'error').mockImplementation(() => {})
  try {
    draw()
  } finally {
    said.mockRestore()
  }
}

test('what threw is replaced by a sentence rather than by nothing', () => {
  quietly(() =>
    render(
      <ErrorBoundary said={SAID}>
        <Throws when />
      </ErrorBoundary>,
    ),
  )

  expect(screen.getByRole('alert').textContent).toContain(SAID)
})

test('what did not throw is drawn as it was', () => {
  render(
    <ErrorBoundary said={SAID}>
      <Throws when={false} />
    </ErrorBoundary>,
  )

  expect(screen.getByText('the document')).toBeTruthy()
  expect(screen.queryByRole('alert')).toBeNull()
})

test('trying again draws what threw, so a panel is not broken until the page is reloaded', () => {
  function Sometimes() {
    const [broken, setBroken] = useState(true)
    return (
      <>
        <button onClick={() => setBroken(false)}>mend it</button>
        <ErrorBoundary said={SAID}>
          <Throws when={broken} />
        </ErrorBoundary>
      </>
    )
  }
  quietly(() => render(<Sometimes />))
  expect(screen.getByRole('alert')).toBeTruthy()

  /* Mended first, so trying again finds something that draws. A retry over a child that
     still throws is the first test's sentence again, which is the honest outcome. */
  fireEvent.click(screen.getByText('mend it'))
  fireEvent.click(screen.getByRole('button', { name: 'Try again' }))

  expect(screen.getByText('the document')).toBeTruthy()
  expect(screen.queryByRole('alert')).toBeNull()
})
