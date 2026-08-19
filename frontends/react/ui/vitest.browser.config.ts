/// <reference types="vitest/config" />
import { defineConfig } from 'vite'

// The tier the fast one cannot be. happy-dom moves no selection boundary when a text node
// is rewritten, so what the reader keeps while an answer is being written is only
// observable in a browser — and it is the thing story 21 is named for. Its own config and
// its own command: a browser is not something `npm test` should need.
export default defineConfig({
  test: {
    include: ['browser/**/*.test.ts'],
    browser: {
      enabled: true,
      headless: true,
      provider: 'playwright',
      instances: [{ browser: 'chromium' }],
    },
  },
})
