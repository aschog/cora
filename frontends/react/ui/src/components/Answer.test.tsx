import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import Answer from './Answer'

afterEach(cleanup)

const composer = (onUpload = vi.fn(), uploading = false) => {
  const drawn = render(
    <Answer
      mode={null}
      thread="t1"
      entries={[]}
      asking={false}
      askingElsewhere={false}
      onAsk={vi.fn()}
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

const shot = () => new File([new Uint8Array([1])], 'words.png', { type: 'image/png' })

test('a file is added from beside the question', () => {
  composer()

  expect(screen.getByLabelText(ADD)).toBeTruthy()
})

test('what is picked goes to the upload the rail uses', () => {
  const { onUpload } = composer()

  const picked = screen.getByLabelText(ADD) as HTMLInputElement
  fireEvent.change(picked, { target: { files: [shot()] } })

  expect(onUpload).toHaveBeenCalledTimes(1)
  expect(onUpload.mock.calls[0][0].name).toBe('words.png')
})

/* An upload is seconds of real work, and the control is the only thing saying so to a
   reader whose rail is folded away. */
test('the control says an upload is running and takes no second file', () => {
  const { onUpload } = composer(vi.fn(), true)

  const running = screen.getByLabelText('Adding a file…') as HTMLInputElement
  expect(running.disabled).toBe(true)
  fireEvent.change(running, { target: { files: [shot()] } })

  expect(onUpload).not.toHaveBeenCalled()
})

/* Found in review: the rail's control filters what cora cannot read, and this one sent
   everything to the server for a refusal it could have said itself. */
test('it offers what cora reads, and photos', () => {
  composer()

  const picked = screen.getByLabelText(ADD) as HTMLInputElement
  expect(picked.accept).toBe('.txt,.md,.pdf,image/*')
})
