import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'

/* The rules of the library, held by a tool rather than by review. `react-hooks` is the
   one that matters: the order hooks are called in is what React tracks state by, and a
   dependency array that has fallen behind its closure is a stale read that no type
   catches. `react-refresh` keeps a module that exports a component exporting only
   components, so a save replaces it rather than reloading the page and losing the
   conversation on it. */
export default [
  { ignores: ['dist', 'coverage', 'browser/__screenshots__'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  reactHooks.configs.flat['recommended-latest'],
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
    },
    plugins: { 'react-refresh': reactRefresh },
    rules: {
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
      /* A name that is deliberately unused says so with a leading underscore, which is
         the convention the type checker already reads. */
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
    },
  },
  {
    files: ['**/*.test.{ts,tsx}', 'browser/**/*.ts'],
    languageOptions: { globals: { ...globals.browser, ...globals.node } },
  },
]
