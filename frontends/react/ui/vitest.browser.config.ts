/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import { modules } from './vite.config'

// The tier the fast one cannot be, for the two things happy-dom cannot answer for. It moves
// no selection boundary when a text node is rewritten, so what the reader keeps while an
// answer is being written passes and fails alike there — the thing story 21 is named for.
// And it applies no stylesheet, so which colour a cited passage is actually drawn in is only
// observable where the cascade is real. Its own config and its own command: a browser is not
// something `npm test` should need.
export default defineConfig({
  css: modules,
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
