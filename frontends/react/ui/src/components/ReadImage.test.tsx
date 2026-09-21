import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import ReadImage from './ReadImage'

afterEach(cleanup)

const put = (read: string, onKeep = vi.fn(), onDiscard = vi.fn()) => {
  render(
    <ReadImage
      image="words.png"
      read={read}
      held={[]}
      onKeepAsFile={onKeep}
      onRead={async () => null}
      onDiscard={onDiscard}
    />,
  )
  return { onKeep, onDiscard }
}

const KEEP = 'Keep it'
const written = () => screen.getByRole('textbox', { name: 'What was read' })
/* A reading is kept under a name the reader gives, so every keeping starts with one. */
const naming = (name: string) =>
  fireEvent.change(screen.getByLabelText('What to call it'), {
    target: { value: name },
  })

test('what was read is drawn to be corrected, with a way to keep it and a way not to', () => {
  put('Hilfe  help')

  expect((written() as HTMLTextAreaElement).value).toBe('Hilfe  help')
  expect(screen.getByRole('button', { name: KEEP })).toBeTruthy()
  expect(screen.getByRole('button', { name: 'Discard' })).toBeTruthy()
})

test('keeping it hands over the name the reader gave', async () => {
  const { onKeep } = put('Hilfe  help')

  naming('Einheit 3.md')
  fireEvent.click(screen.getByRole('button', { name: KEEP }))

  await waitFor(() => expect(onKeep).toHaveBeenCalled())
  expect(onKeep.mock.calls[0][0]).toBe('Einheit 3.md')
})

/* Nothing is kept under no name, because a file of the field's is found by its name. */
test('an unnamed reading cannot be kept', () => {
  const { onKeep } = put('Hilfe  help')

  expect((screen.getByRole('button', { name: KEEP }) as HTMLButtonElement).disabled).toBe(
    true,
  )
  fireEvent.click(screen.getByRole('button', { name: KEEP }))

  expect(onKeep).not.toHaveBeenCalled()
})

/* The correction is the point of the step: what the reader typed is what cora keeps. */
test('what was corrected is what is kept, not what was read', async () => {
  const { onKeep } = put('Hilfe  heIp')

  fireEvent.change(written(), { target: { value: 'Hilfe  help' } })
  naming('words.md')
  fireEvent.click(screen.getByRole('button', { name: KEEP }))

  /* Ending in a newline, as a text file does. */
  await waitFor(() => expect(onKeep).toHaveBeenCalled())
  expect(onKeep.mock.calls[0][1]).toBe('Hilfe  help\n')
})

test('keeping while the merge is still in flight writes the merge', async () => {
  const onKeep = vi.fn()
  let land: (text: string) => void = () => undefined
  render(
    <ReadImage
      image="words.png"
      read="Buch  book"
      held={['Grundwortschatz.md']}
      onKeepAsFile={onKeep}
      onRead={() => new Promise<string>((said) => (land = said))}
      onDiscard={vi.fn()}
    />,
  )

  naming('Grundwortschatz.md')
  /* Blur starts the merge; the click arrives before it has landed, which is what a
     mouse does — focusout first, then click. */
  fireEvent.blur(screen.getByLabelText('What to call it'))
  fireEvent.click(screen.getByRole('button', { name: KEEP }))
  land('Apfel  apple')

  await waitFor(() => expect(onKeep).toHaveBeenCalled())
  expect(onKeep.mock.calls[0][1]).toBe('Apfel  apple\nBuch  book\n')
})

/* Found in review: the merge promise was reused for every later keep, so a correction
   made after the merged text appeared was thrown away — silently, on the one screen
   whose whole purpose is correcting what was read. */
test('a correction made after the merge is what is kept', async () => {
  const onKeep = vi.fn()
  render(
    <ReadImage
      image="words.png"
      read="Buch  book"
      held={['Grundwortschatz.md']}
      onKeepAsFile={onKeep}
      onRead={async () => 'Apfel  apple'}
      onDiscard={vi.fn()}
    />,
  )

  naming('Grundwortschatz.md')
  fireEvent.blur(screen.getByLabelText('What to call it'))
  await waitFor(() =>
    expect((written() as HTMLTextAreaElement).value).toBe('Apfel  apple\nBuch  book'),
  )

  fireEvent.change(written(), { target: { value: 'Apfel  apple\nBuch  BOOK' } })
  fireEvent.click(screen.getByRole('button', { name: KEEP }))

  await waitFor(() => expect(onKeep).toHaveBeenCalled())
  expect(onKeep.mock.calls[0][1]).toBe('Apfel  apple\nBuch  BOOK\n')
})

/* And a name changed after a merge must not drag the merged text under the new one. */
test('a name changed after a merge keeps only what the box holds', async () => {
  const onKeep = vi.fn()
  render(
    <ReadImage
      image="words.png"
      read="Buch  book"
      held={['Grundwortschatz.md']}
      onKeepAsFile={onKeep}
      onRead={async () => 'Apfel  apple'}
      onDiscard={vi.fn()}
    />,
  )

  naming('Grundwortschatz.md')
  fireEvent.blur(screen.getByLabelText('What to call it'))
  await waitFor(() =>
    expect((written() as HTMLTextAreaElement).value).toBe('Apfel  apple\nBuch  book'),
  )

  fireEvent.change(written(), { target: { value: 'Buch  book' } })
  naming('Neue Liste.md')
  fireEvent.click(screen.getByRole('button', { name: KEEP }))

  await waitFor(() => expect(onKeep).toHaveBeenCalled())
  expect(onKeep.mock.calls[0]).toEqual(['Neue Liste.md', 'Buch  book\n'])
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

/* Found in review: the text is state seeded from a prop, and a second photo read in
   the same session replaces the props around a textarea still holding the first one —
   so Keep it would upload photo A's words under photo B's name. */
test('a second reading replaces the text the first one left', () => {
  const { rerender } = render(
    <ReadImage
      image="a.png"
      read="AAA"
      held={[]}
      onKeepAsFile={vi.fn()}
      onRead={async () => null}
      onDiscard={vi.fn()}
    />,
  )

  rerender(
    <ReadImage
      image="b.png"
      read="BBB"
      held={[]}
      onKeepAsFile={vi.fn()}
      onRead={async () => null}
      onDiscard={vi.fn()}
    />,
  )

  expect((written() as HTMLTextAreaElement).value).toBe('BBB')
})

/* Minutes of hand-corrected recognition sit in that box, and every other destructive
   act in this app is confirmed. A stray click on the ground behind the dialog is not
   the way to lose it. */
test('a click on the ground behind it does not throw away a correction', () => {
  const { onDiscard } = put('Hilfe  heIp')

  fireEvent.change(written(), { target: { value: 'Hilfe  help' } })
  fireEvent.click(screen.getByRole('dialog', { name: 'READ FROM THE IMAGE' })
    .parentElement as HTMLElement)

  expect(onDiscard).not.toHaveBeenCalled()
})

test('a click on the ground behind an untouched reading closes it', () => {
  const { onDiscard } = put('Hilfe  help')

  fireEvent.click(screen.getByRole('dialog', { name: 'READ FROM THE IMAGE' })
    .parentElement as HTMLElement)

  expect(onDiscard).toHaveBeenCalledTimes(1)
})
