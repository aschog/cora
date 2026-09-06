import { useState } from 'react'
import type { Asked, Card, Offered } from '../api'

export const WAITING = 'Paused · needs your input'
export const SETTLED = 'Settled · your answer'
export const FILL_IN_FIRST = 'Fill it in first.'
export const took = (action: Offered) => action.settled || `You chose ${action.label}.`

type Props = {
  card: Card
  /** The action taken, once one has been. Absent is a card still waiting on the
   *  reader. */
  taken?: Offered
  /** What is offered on a settled card — *Change* on a decision, nothing on an effect
   *  that already ran. The page decides, because only it knows whether the thing behind
   *  the card can be asked again. */
  again?: { label: string; onPick: () => void }
  onTake: (action: Offered, values: Record<string, unknown>) => void
}

/** One card over every way a turn stops: what cora put to the reader, and afterwards the
 *  line that says what they did about it.
 *
 *  It knows nothing of decisions, proposals or forms. A card is a prompt, fields to fill
 *  and actions to take, and the three differ only in which fields are writable and which
 *  actions are offered — so a fourth kind of pause is a card the backend writes and no
 *  component here.
 *
 *  Every part of it is drawn as text. A card may have been written by a plugin, and a
 *  plugin describing what the page shows must not be a plugin running code on it. */
export default function PauseCard({ card, taken, again, onTake }: Props) {
  /* Keyed on the card, so what the reader typed belongs to the card in front of them.
     Turn ids repeat across conversations, so React reconciles one conversation's card
     onto another's — and without this the values would go with it. */
  const [written, setWritten] = useState<Record<string, unknown>>(() => filled(card))
  const [drawn, setDrawn] = useState(card)
  if (drawn !== card) {
    setDrawn(card)
    setWritten(filled(card))
  }
  const open = taken === undefined
  const state = open ? WAITING : SETTLED
  const short = !complete(card, written)
  return (
    <div className="decision" role="group" aria-label={state}>
      <p className="decision-head micro">
        <span
          className={open ? 'decision-dot' : 'decision-dot settled'}
          aria-hidden="true"
        >
          ●
        </span>
        {state}
      </p>
      <p className="decision-question">{card.prompt}</p>
      {/* Drawn open or settled: a reader coming back to the conversation is owed what
          they answered on, not only that they did. */}
      {card.fields.length > 0 && (
        <div className="card-fields">
          {card.fields.map((field) => (
            <Control
              key={field.name}
              field={field}
              value={written[field.name]}
              settled={!open}
              onWrite={(value) =>
                setWritten((held) => ({ ...held, [field.name]: value }))
              }
            />
          ))}
        </div>
      )}
      {open ? (
        <div className="decision-options">
          {card.actions.map((action, at) => {
            const held = action.needs_valid && short
            return (
              <button
                key={at}
                className="decision-option"
                disabled={held}
                onClick={() => onTake(action, written)}
              >
                <span className="decision-label">{action.label}</span>
                {(held || action.note) && (
                  <span className="decision-note">
                    {held ? FILL_IN_FIRST : action.note}
                  </span>
                )}
              </button>
            )
          })}
        </div>
      ) : (
        <p className="decision-resolved">
          <span className="decision-settled">{took(taken)}</span>
          {again && (
            <button className="decision-change" onClick={again.onPick}>
              {again.label}
            </button>
          )}
        </p>
      )}
    </div>
  )
}

/** One field, drawn as the control its schema describes. A schema this has no case for
 *  falls back to text: a field the reader cannot answer is worse than one drawn plainly,
 *  and a plugin's schema is not something the page can be exhaustive about. */
function Control({
  field,
  value,
  settled,
  onWrite,
}: {
  field: Asked
  value: unknown
  settled: boolean
  onWrite: (value: unknown) => void
}) {
  /* The schema's own words, which is what the tool wrote them for. The name is the
     fallback, because a property with no description is still one the reader must
     answer. */
  const said = String(field.schema.title ?? field.schema.description ?? field.name)
  /* Required is marked by the control's own `required`, which the cascade draws and a
     screen reader announces — rather than by an asterisk beside the words, which is a
     mark only the sighted reader gets and only if they know the convention. */
  const label = <span className="card-name micro">{said}</span>
  /* A field the reader may not write is read off the card itself: what is drawn is what
     cora put up, not what the page is holding on their behalf. */
  if (!field.editable || settled)
    return (
      <div className="card-field">
        {label}
        <span className="card-read">
          {written(field.editable ? value : field.value)}
        </span>
      </div>
    )
  const choices = field.schema.enum
  return (
    <label className="card-field">
      {label}
      {Array.isArray(choices) ? (
        <Choices choices={choices} value={value} onWrite={onWrite} />
      ) : field.schema.type === 'boolean' ? (
        <input
          className="card-check"
          type="checkbox"
          checked={value === true}
          required={field.required}
          onChange={(event) => onWrite(event.target.checked)}
        />
      ) : (
        <input
          className="card-input"
          type={input(field.schema)}
          required={field.required}
          value={value === null || value === undefined ? '' : String(value)}
          onChange={(event) => onWrite(read(field.schema, event.target.value))}
        />
      )}
    </label>
  )
}

/** A short enumeration as buttons, a long one as a select. Four is where a row of them
 *  stops fitting beside its label. Either way what goes back is the choice itself and
 *  not the string a control drew it as: a select answers in text, and an enumeration of
 *  numbers would submit "3" where the row of buttons submits 3. */
const MANY = 4

function Choices({
  choices,
  value,
  onWrite,
}: {
  choices: unknown[]
  value: unknown
  onWrite: (value: unknown) => void
}) {
  if (choices.length > MANY)
    return (
      <select
        className="card-input"
        value={value === null || value === undefined ? '' : String(value)}
        onChange={(event) =>
          onWrite(choices.find((each) => String(each) === event.target.value) ?? null)
        }
      >
        <option value="" />
        {choices.map((each) => (
          <option key={String(each)} value={String(each)}>
            {String(each)}
          </option>
        ))}
      </select>
    )
  return (
    <span className="card-choices">
      {choices.map((each) => (
        <button
          key={String(each)}
          type="button"
          className={each === value ? 'card-choice picked' : 'card-choice'}
          aria-pressed={each === value}
          onClick={() => onWrite(each)}
        >
          {String(each)}
        </button>
      ))}
    </span>
  )
}

/** Which control a schema asks for. Type and `format` and nothing else: a row here is
 *  what a new kind of field costs, which is the point of drawing from the schema. */
const CONTROLS: Record<string, string> = {
  'string:date': 'date',
  'string:date-time': 'datetime-local',
  'string:email': 'email',
  'string:uri': 'url',
  integer: 'number',
  number: 'number',
}

const input = (schema: Record<string, unknown>) => {
  const kind = String(schema.type ?? 'string')
  return CONTROLS[`${kind}:${String(schema.format ?? '')}`] ?? CONTROLS[kind] ?? 'text'
}

/** What the reader typed, as the schema says it is. A number field holding nothing is
 *  nothing rather than zero — an empty control means unanswered, and a required field
 *  answered zero by the browser would submit itself. */
const read = (schema: Record<string, unknown>, typed: string): unknown => {
  const kind = String(schema.type ?? 'string')
  if (kind !== 'integer' && kind !== 'number') return typed
  if (typed.trim() === '') return null
  const figure = Number(typed)
  return Number.isNaN(figure) ? typed : figure
}

/** A value as the reader reads it. A string is shown as written; anything else is drawn
 *  as the JSON it arrived as, because a number, a list and a nested object all have to be
 *  readable and none of them is prose. Nothing reads as nothing: a field the reader left
 *  alone saying `null` reads as a value cora sent. */
const written = (value: unknown) =>
  value === null || value === undefined
    ? ''
    : typeof value === 'string'
      ? value
      : JSON.stringify(value)

/** What the card already knows, so a field the model filled in arrives filled in. The
 *  reader's own fields and no others: what goes back is what they were offered to
 *  write, and a value for anything else is a value nobody asked them for. */
const filled = (card: Card) =>
  Object.fromEntries(
    card.fields
      .filter((field) => field.editable)
      .map((field) => [field.name, field.value]),
  )

/** Whether every field the reader must answer holds something. Required is read off each
 *  field's own schema, because a card's fields come from one schema or several and only
 *  the field knows which of them it was required by. */
const complete = (card: Card, written: Record<string, unknown>) =>
  card.fields.every(
    (field) => !field.editable || !field.required || !empty(written[field.name]),
  )

const empty = (value: unknown) => value === null || value === undefined || value === ''
