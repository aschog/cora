/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// `/api` belongs to the Python server; in dev it runs beside Vite, in production the
// same process serves both and the proxy is not in the picture.
export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': 'http://127.0.0.1:8000' } },
  test: {
    environment: 'happy-dom',
    include: ['src/**/*.test.ts', 'src/**/*.test.tsx'],
    // A click whose default action is a navigation is a click this suite asserts about,
    // never one it should perform: left on, happy-dom dials the href.
    environmentOptions: {
      happyDOM: { settings: { navigation: { disableMainFrameNavigation: true } } },
    },
  },
})
