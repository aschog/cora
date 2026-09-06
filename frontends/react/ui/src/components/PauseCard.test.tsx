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

test('a choice goes back as itself, whichever control drew it', () => {
  /* A select answers in text, so an enumeration of numbers would submit "3" through one
     and 3 through the row of buttons. */
  const taken = drawn({
    fields: [field('nights', { type: 'integer', enum: [1, 2, 3, 4, 7] })],
  })

  fireEvent.change(screen.getByRole('combobox'), { target: { value: '3' } })
  fireEvent.click(screen.getByRole('button', { name: /Search/ }))

  expect(taken).toHaveBeenCalledWith(expect.anything(), { nights: 3 })
})

test('two actions sharing a label are both drawn', () => {
  drawn({
    actions: [action('Later', { answer: 'a' }), action('Later', { answer: 'b' })],
  })

  expect(screen.getAllByRole('button', { name: 'Later' })).toHaveLength(2)
})

test('a value that is not a string is read back as the JSON it arrived as', () => {
  drawn({
    fields: [field('days', {}, { value: 3, editable: false })],
  })

  expect(screen.getByText('3')).toBeTruthy()
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

test('a required field holding only spaces is not one the reader answered', () => {
  drawn({
    fields: [field('destination', { type: 'string' }, { required: true })],
    actions: [action('Search', { needs_valid: true })],
  })

  fireEvent.change(screen.getByLabelText('destination'), { target: { value: '   ' } })

  const search = screen.getByRole('button', { name: /Search/ })
  expect(search).toHaveProperty('disabled', true)
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

test('a boolean is drawn as a checkbox and goes back as a boolean', () => {
  /* Text would send the string "true", which the schema the card was built from would
     then refuse. */
  const taken = drawn({ fields: [field('direct_only', { type: 'boolean' })] })

  fireEvent.click(screen.getByRole('checkbox'))
  fireEvent.click(screen.getByRole('button', { name: /Search/ }))

  expect(taken).toHaveBeenCalledWith(expect.anything(), { direct_only: true })
})

test('a field says what the schema says it is, not just what it is called', () => {
  drawn({
    fields: [
      field('window_start', {
        type: 'string',
        description: 'Earliest day the trip could start.',
      }),
    ],
  })

  expect(screen.getByText('Earliest day the trip could start.')).toBeTruthy()
})

test('a required field says so on the control the reader answers', () => {
  drawn({ fields: [field('origin', { type: 'string' }, { required: true })] })

  expect(screen.getByLabelText('origin')).toHaveProperty('required', true)
})

test('what the reader typed belongs to the card in front of them', () => {
  /* Turn ids repeat across conversations, so React reconciles one conversation's card
     onto another's — and the values must not go with it. */
  const first = card({ fields: [field('origin', { type: 'string' })] })
  const second = card({ fields: [field('origin', { type: 'string' })] })
  const taken = vi.fn()
  const { rerender } = render(<PauseCard card={first} onTake={taken} />)
  fireEvent.change(screen.getByLabelText('origin'), { target: { value: 'BER' } })

  rerender(<PauseCard card={second} onTake={taken} />)
  fireEvent.click(screen.getByRole('button', { name: /Search/ }))

  expect(taken).toHaveBeenCalledWith(expect.anything(), { origin: null })
})

test('a field nobody answered reads as blank, not as null', () => {
  render(
    <PauseCard
      card={card({ fields: [field('max_price', { type: 'integer' })] })}
      taken={action('Search')}
      onTake={vi.fn()}
    />,
  )

  expect(screen.queryByText('null')).toBeNull()
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
