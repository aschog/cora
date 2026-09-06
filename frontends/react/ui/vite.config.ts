/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Each component's styles are its own, named as its own: a rule reaches what the file it
// sits beside draws and nothing else. `camelCaseOnly` because the kebab name is then
// unreachable, and one name for one class is the point.
// Exported because the browser tier is its own Vite config: without this it hashes the
// kebab name only, every `styles.someThing` reads `undefined`, and what is drawn has no
// class at all — which is a whole tier asserting about the browser's default styles.
export const modules = { modules: { localsConvention: 'camelCaseOnly' } } as const

// `/api` belongs to the Python server; in dev it runs beside Vite, in production the
// same process serves both and the proxy is not in the picture.
export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': 'http://127.0.0.1:8000' } },
  css: modules,
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
