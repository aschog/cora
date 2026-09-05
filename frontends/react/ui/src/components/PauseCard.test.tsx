import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import PauseCard, { FILL_IN_FIRST } from './PauseCard'
import type { Asked, Card, Offered } from '../api'

afterEach(cleanup)

const field = (
  name: string,
  schema: Record<string, unknown>,
  over: Partial<Asked> = {},
) => ({ name, schema, value: null, editable: true, required: false, ...over }) as Asked

const action = (label: string, over: Partial<Offered> = {}) =>
  ({
    label,
    answer: label,
    note: '',
    needs_valid: false,
    settled: '',
    ...over,
  }) as Offered

const card = (over: Partial<Card> = {}): Card => ({
  prompt: 'Give me the trip.',
  fields: [],
  actions: [action('Search')],
  ...over,
})

const drawn = (over: Partial<Card> = {}, onTake = vi.fn()) => {
  render(<PauseCard card={card(over)} onTake={onTake} />)
  return onTake
}

test('a card of fields draws a control for each, and its actions', () => {
  drawn({
    fields: [
      field('destination', { type: 'string' }),
      field('nights', { type: 'integer' }),
    ],
    actions: [action('Search'), action('Not now', { answer: null })],
  })

  expect(screen.getAllByRole('textbox')).toHaveLength(1)
  expect(screen.getAllByRole('spinbutton')).toHaveLength(1)
  expect(screen.getAllByRole('button', { name: /Search|Not now/ })).toHaveLength(2)
})

test('a card of no fields draws buttons alone', () => {
  drawn({ actions: [action('77 kg'), action('75 kg')] })

  expect(screen.queryByRole('textbox')).toBeNull()
  expect(screen.getAllByRole('button')).toHaveLength(2)
})

test('a string of format date is drawn as a date control', () => {
  drawn({ fields: [field('depart', { type: 'string', format: 'date' })] })

  expect(screen.getByLabelText('depart')).toHaveProperty('type', 'date')
})

test('a short enumeration is drawn as those choices and no free text', () => {
  drawn({
    fields: [field('budget', { type: 'string', enum: ['Lean', 'Middle', 'No cap'] })],
  })

  expect(screen.queryByRole('textbox')).toBeNull()
  expect(screen.getAllByRole('button', { name: /Lean|Middle|No cap/ })).toHaveLength(3)
})

test('a long enumeration is drawn as a select', () => {
  drawn({ fields: [field('currency', { enum: ['EUR', 'GBP', 'USD', 'JPY', 'CHF'] })] })

  expect(within(screen.getByRole('combobox')).getAllByRole('option')).toHaveLength(6)
})

test('a schema the page has no control for still asks, as text', () => {
  drawn({ fields: [field('shape', { type: 'polygon' })] })

  expect(screen.getByLabelText('shape')).toHaveProperty('type', 'text')
})

test('an action that waits is held while a required field is empty, and says why', () => {
  drawn({
    fields: [field('destination', { type: 'string' }, { required: true })],
    actions: [action('Search', { needs_valid: true })],
  })

  const search = screen.getByRole('button', { name: /Search/ })
  expect(search).toHaveProperty('disabled', true)
  expect(within(search).getByText(FILL_IN_FIRST)).toBeTruthy()
})

test('that same action is takeable once the required field holds a value', () => {
  const taken = drawn({
    fields: [field('destination', { type: 'string' }, { required: true })],
    actions: [action('Search', { needs_valid: true })],
  })

  fireEvent.change(screen.getByLabelText('destination'), { target: { value: 'LIS' } })
  fireEvent.click(screen.getByRole('button', { name: /Search/ }))

  expect(taken).toHaveBeenCalledWith(expect.objectContaining({ label: 'Search' }), {
    destination: 'LIS',
  })
})

test('an action that waits for nothing is takeable on an empty card', () => {
  const taken = drawn({
    fields: [field('destination', { type: 'string' }, { required: true })],
    actions: [action('Not now', { answer: null })],
  })

  fireEvent.click(screen.getByRole('button', { name: 'Not now' }))

  expect(taken).toHaveBeenCalledWith(expect.objectContaining({ answer: null }), {
    destination: null,
  })
})

test('a number written into an integer field goes back as a number', () => {
  const taken = drawn({ fields: [field('nights', { type: 'integer' })] })

  fireEvent.change(screen.getByLabelText('nights'), { target: { value: '3' } })
  fireEvent.click(screen.getByRole('button', { name: /Search/ }))

  expect(taken).toHaveBeenCalledWith(expect.anything(), { nights: 3 })
})

test('a field the card marked unwritable is read, and never sent', () => {
  const taken = drawn({
    fields: [field('tool', {}, { value: 'save_itinerary', editable: false })],
  })

  expect(screen.getByText('save_itinerary')).toBeTruthy()
  expect(screen.queryByRole('textbox')).toBeNull()

  fireEvent.click(screen.getByRole('button', { name: /Search/ }))
  expect(taken).toHaveBeenCalledWith(expect.anything(), {})
})

test('a settled card says what the action said, and offers none', () => {
  render(
    <PauseCard
      card={card({ actions: [action('Approve', { settled: 'You approved it.' })] })}
      taken={action('Approve', { settled: 'You approved it.' })}
      onTake={vi.fn()}
    />,
  )

  expect(screen.getByText('You approved it.')).toBeTruthy()
  expect(screen.queryByRole('button', { name: 'Approve' })).toBeNull()
})

test('an action with nothing of its own to say names itself', () => {
  render(<PauseCard card={card()} taken={action('75 kg')} onTake={vi.fn()} />)

  expect(screen.getByText('You chose 75 kg.')).toBeTruthy()
})

test('a card written with markup is drawn as text, and none of it runs', () => {
  drawn({
    prompt: '<img src=x onerror="alert(1)">',
    actions: [action('<b>bold</b>')],
  })

  expect(screen.getByText('<img src=x onerror="alert(1)">')).toBeTruthy()
  expect(screen.getByText('<b>bold</b>')).toBeTruthy()
  expect(document.querySelector('img')).toBeNull()
  expect(document.querySelector('b')).toBeNull()
})
