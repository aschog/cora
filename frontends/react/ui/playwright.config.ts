import { defineConfig } from '@playwright/test'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))

/* cora, driven through a real browser against a real server: the real page, the real
   API, the real stores, the real turn.
 *
 * Two runs, and the only difference between them is which model answers.
 * `make e2e` points `OPENROUTER_BASE_URL` at `scripts/fake_model_service.py`, so a run
 * costs nothing and says the same thing every time. `make e2e-live` sets `CORA_E2E_LIVE`
 * and leaves the key and the URL alone, so the one thing the stub cannot cover — the
 * provider — is covered by hand before a submission.
 *
 * Both are started from the Makefile, which builds the page and lays out a fresh store
 * first. `npx playwright test` on its own picks up whatever the last run left behind.
 */

const ROOT = resolve(HERE, '../../..')
const STORE = resolve(ROOT, '.cora/e2e')
const PAGE = 'http://127.0.0.1:8765'
const MODEL = 'http://127.0.0.1:8911'
const live = process.env.CORA_E2E_LIVE === '1'

const stubbed = {
  CORA_MODEL: 'fake',
  OPENROUTER_API_KEY: 'no key needed',
  OPENROUTER_BASE_URL: `${MODEL}/v1`,
}
const served = {
  CORA_DB_PATH: `${STORE}/cora.sqlite`,
  CORA_DOCUMENTS_PATH: `${STORE}/documents`,
  CORA_OUTPUT_PATH: `${STORE}/out`,
  CORA_PLUGINS_PATH: `${STORE}/plugins`,
  /* A field the configuration named, beside the one the plugin brings: two is what
     makes the picker a control rather than a label. */
  CORA_SCOPES: 'notes',
  CORA_PORT: '8765',
  ...(live ? {} : stubbed),
}

const model = {
  command: 'uv run python scripts/fake_model_service.py',
  url: `${MODEL}/`,
  cwd: ROOT,
  reuseExistingServer: false,
  timeout: 30_000,
}

export default defineConfig({
  testDir: './e2e',
  globalSetup: './e2e/seed.ts',
  /* One worker: the suite drives one deployment over one store, and two of it at once
     would be two readers deleting each other's rows. */
  workers: 1,
  fullyParallel: false,
  forbidOnly: true,
  reporter: [['list']],
  timeout: 30_000,
  expect: { timeout: 10_000 },
  use: { baseURL: PAGE, trace: 'retain-on-failure' },
  testIgnore: live ? undefined : /live\.spec\.ts/,
  testMatch: live ? /live\.spec\.ts/ : undefined,
  webServer: [
    ...(live ? [] : [model]),
    {
      command: 'uv run python -m cora.frontends.react.server',
      url: `${PAGE}/api/scopes`,
      cwd: ROOT,
      env: served,
      reuseExistingServer: false,
      /* The embedding model loads on the first import, which is most of this. */
      timeout: 180_000,
    },
  ],
})
