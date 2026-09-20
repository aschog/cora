import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import ReadImage from './ReadImage'

afterEach(cleanup)

const put = (read: string, onKeep = vi.fn(), onDiscard = vi.fn()) => {
  render(
    <ReadImage image="words.png" read={read} onKeep={onKeep} onDiscard={onDiscard} />,
  )
  return { onKeep, onDiscard }
}

const KEEP = 'Keep it'
const written = () => screen.getByRole('textbox', { name: 'What was read' })

test('what was read is drawn to be corrected, with a way to keep it and a way not to', () => {
  put('Hilfe  help')

  expect((written() as HTMLTextAreaElement).value).toBe('Hilfe  help')
  expect(screen.getByRole('button', { name: KEEP })).toBeTruthy()
  expect(screen.getByRole('button', { name: 'Discard' })).toBeTruthy()
})

test('keeping it hands over a document named after the image', () => {
  const { onKeep } = put('Hilfe  help')

  fireEvent.click(screen.getByRole('button', { name: KEEP }))

  const [file] = onKeep.mock.calls[0] as [File]
  expect(file.name).toBe('words.md')
  expect(file.type).toBe('text/markdown')
})

/* The correction is the point of the step: what the reader typed is what cora keeps. */
test('what was corrected is what is kept, not what was read', async () => {
  const { onKeep } = put('Hilfe  heIp')

  fireEvent.change(written(), { target: { value: 'Hilfe  help' } })
  fireEvent.click(screen.getByRole('button', { name: KEEP }))

  const [file] = onKeep.mock.calls[0] as [File]
  /* Ending in a newline, as a text file does. */
  expect(await file.text()).toBe('Hilfe  help\n')
})

test('discarding hands over nothing', () => {
  const { onKeep, onDiscard } = put('Hilfe  help')

  fireEvent.click(screen.getByRole('button', { name: 'Discard' }))

  expect(onKeep).not.toHaveBeenCalled()
  expect(onDiscard).toHaveBeenCalledTimes(1)
})

/* An empty reading is a photo with no words in it, which is a thing to be told rather
   than an empty document to save. */
test('a reading that found nothing says so and keeps nothing', () => {
  const { onKeep } = put('')

  expect(screen.getByText(/nothing was read/i)).toBeTruthy()
  expect(screen.getByRole('button', { name: KEEP }).hasAttribute('disabled')).toBe(true)
  expect(onKeep).not.toHaveBeenCalled()
})
