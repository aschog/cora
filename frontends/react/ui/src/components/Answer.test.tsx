import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import Answer from './Answer'

afterEach(cleanup)

const composer = (onUpload = vi.fn(), uploading = false, asking = false) => {
  const drawn = render(
    <Answer
      mode={null}
      thread="t1"
      entries={[]}
      asking={asking}
      askingElsewhere={false}
      onAsk={vi.fn()}
      onStop={vi.fn()}
      onCite={vi.fn()}
      onTake={vi.fn()}
      onChange={vi.fn()}
      onUpload={onUpload}
      uploading={uploading}
    />,
  )
  return { ...drawn, onUpload }
}

const ADD = 'Add a file or photo'
/* The ＋ carries the control's name and the picker behind it carries its own: the menu
   between them is what made two labels out of one. */
const PICKER = 'Upload from computer'

const shot = () => new File([new Uint8Array([1])], 'words.png', { type: 'image/png' })

test('a file is added from beside the question', () => {
  composer()

  expect(screen.getByLabelText(ADD)).toBeTruthy()
})

test('what is picked goes to the upload the rail uses', () => {
  const { onUpload } = composer()

  const picked = screen.getByLabelText(PICKER) as HTMLInputElement
  fireEvent.change(picked, { target: { files: [shot()] } })

  expect(onUpload).toHaveBeenCalledTimes(1)
  expect(onUpload.mock.calls[0][0].name).toBe('words.png')
})

/* An upload is seconds of real work, and the control is the only thing saying so to a
   reader whose rail is folded away. */
test('the control says an upload is running and takes no second file', () => {
  const { onUpload } = composer(vi.fn(), true)

  expect(screen.getByLabelText('Adding a file…')).toBeTruthy()
  const running = screen.getByLabelText(PICKER) as HTMLInputElement
  expect(running.disabled).toBe(true)
  fireEvent.change(running, { target: { files: [shot()] } })

  expect(onUpload).not.toHaveBeenCalled()
})

/* Found in review: the rail's control filters what cora cannot read, and this one sent
   everything to the server for a refusal it could have said itself. */
test('it offers what cora reads, and photos', () => {
  composer()

  const picked = screen.getByLabelText(PICKER) as HTMLInputElement
  expect(picked.accept).toBe('.txt,.md,.pdf,image/*')
})

/* While a turn runs the one control stops it rather than asks one: the reader cannot
   ask and stop at once. */
test('while a turn runs the control stops it, and while none does it asks', () => {
  const onStop = vi.fn()
  const onAsk = vi.fn()
  const { rerender } = render(
    <Answer
      mode={null}
      thread="t1"
      entries={[]}
      asking={true}
      askingElsewhere={false}
      onAsk={onAsk}
      onStop={onStop}
      onCite={vi.fn()}
      onTake={vi.fn()}
      onChange={vi.fn()}
    />,
  )

  const stopping = screen.getByRole('button', { name: 'Stop' })
  expect(screen.queryByRole('button', { name: 'Ask' })).toBeNull()
  fireEvent.click(stopping)
  expect(onStop).toHaveBeenCalledTimes(1)
  expect(onAsk).not.toHaveBeenCalled()

  rerender(
    <Answer
      mode={null}
      thread="t1"
      entries={[]}
      asking={false}
      askingElsewhere={false}
      onAsk={onAsk}
      onStop={onStop}
      onCite={vi.fn()}
      onTake={vi.fn()}
      onChange={vi.fn()}
    />,
  )
  expect(screen.getByRole('button', { name: 'Ask' })).toBeTruthy()
  expect(screen.queryByRole('button', { name: 'Stop' })).toBeNull()
})
