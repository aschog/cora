
test('an answer never lands on a conversation that was replaced while it ran', async () => {
  /* A turn takes tens of seconds and only the Ask button is disabled while it does, so
     opening an earlier conversation mid-turn is ordinary use. Replacing "the last
     entry" would then delete that conversation's last turn and show, inside it, an
     answer computed on a thread the reader has left. */
  render(<App />)
  await screen.findByText('notes.md')

  fireEvent.change(screen.getByPlaceholderText(/Ask a question/), {
    target: { value: 'Why am I stalling?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
  await screen.findByText(/Working/)

  fireEvent.click(screen.getByRole('tab', { name: 'SESSIONS' }))
  fireEvent.click(await screen.findByRole('button', { name: OLDER.question }))
  expect(await screen.findByText(OLDER.result.answer)).toBeTruthy()

  turn.release()
  await new Promise((settle) => setTimeout(settle, 0))

  expect(screen.getByText(OLDER.result.answer)).toBeTruthy()
  expect(screen.queryByText(/Sleep, not volume/)).toBeNull()
  expect(screen.queryByText('Why am I stalling?')).toBeNull()
})
