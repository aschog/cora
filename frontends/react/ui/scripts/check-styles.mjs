import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join, basename, dirname, relative } from 'node:path'

/*
 * What the type checker cannot say about a stylesheet.
 *
 * `vite/client` types `*.module.css` as `Record<string, string>`, so `styles.narrow` is
 * a `string` whether or not `.narrow` is declared anywhere — it is `undefined` at
 * runtime and the element is drawn with the word "undefined" for a class. Nothing else
 * in the toolchain looks: it type-checks, it lints, it builds, and the only symptom is
 * a control that quietly loses its shape.
 *
 * Two questions, both cheap:
 *
 *   1. Does every `styles.x` a component reads exist in the module it reads it from?
 *   2. Does every class named in the global sheet still exist as a plain class name —
 *      or has it been moved into a module, leaving a rule that matches nothing? This is
 *      the one that bites when a stylesheet is split: a rule like `.modal.narrow` whose
 *      two halves end up on opposite sides of the boundary is silently dead, because
 *      each half is now hashed under a different name.
 */

const UI = join(dirname(new URL(import.meta.url).pathname), '..')
const GLOBAL = join(UI, 'src', 'styles.css')

const walk = (at) =>
  readdirSync(at).flatMap((name) => {
    const path = join(at, name)
    if (name === 'node_modules' || name === 'dist') return []
    return statSync(path).isDirectory() ? walk(path) : [path]
  })

const camel = (name) => name.replace(/-(\w)/g, (_, c) => c.toUpperCase())

/** Every class a sheet declares, by the name a module would export it as. */
const declared = (text) =>
  new Set([...text.matchAll(/\.([a-zA-Z][\w-]*)/g)].map((m) => camel(m[1])))

const files = walk(join(UI, 'src'))
const source = files.filter((f) => /\.tsx?$/.test(f) && !f.includes('.test.'))
const wrong = []

// 1. every `ident.name` read against the module that `ident` was imported from
for (const file of source) {
  const text = readFileSync(file, 'utf8')
  const imports = [...text.matchAll(/import\s+(\w+)\s+from\s+'([^']*\.module\.css)'/g)]
  for (const [, ident, spec] of imports) {
    const sheet = join(dirname(file), spec)
    const has = declared(readFileSync(sheet, 'utf8'))
    const read = new RegExp(`\\b${ident}\\.([A-Za-z]\\w*)`, 'g')
    /* Without the import lines: `import dialog from './dialog.module.css'` matches the
       same shape as a read of `dialog.module`, and is not one. */
    const body = text.replace(/^import .*$/gm, '')
    for (const [, name] of body.matchAll(read)) {
      if (!has.has(name)) {
        wrong.push(
          `${relative(UI, file)}: ${ident}.${name} is not declared in ${basename(sheet)}`,
        )
      }
    }
  }
}

// 2. every class the global sheet still names must still be global
const globals = declared(readFileSync(GLOBAL, 'utf8'))
const modules = files.filter((f) => f.endsWith('.module.css'))
const owned = new Map()
for (const sheet of modules) {
  for (const name of declared(readFileSync(sheet, 'utf8'))) {
    owned.set(name, basename(sheet))
  }
}
/* Read off the components rather than off the sheets: a name may be declared in a module
   *and* left in the global sheet, which is fine while the global one is what is drawn.
   What is not fine is the global sheet naming a class only a module now declares. */
const literals = new Set()
for (const file of source) {
  const text = readFileSync(file, 'utf8')
  for (const m of text.matchAll(/className=(?:"([^"]*)"|\{`([^`]*)`\}|\{'([^']*)'\})/g)) {
    for (const token of (m[1] ?? m[2] ?? m[3] ?? '').split(/[\s${}]+/)) {
      if (token && !token.includes('.')) literals.add(camel(token))
    }
  }
}
for (const name of globals) {
  if (owned.has(name) && !literals.has(name)) {
    wrong.push(
      `src/styles.css: .${name} is drawn only by ${owned.get(name)} now, so the rule ` +
        `naming it here matches nothing — move it into that module.`,
    )
  }
}

if (wrong.length) {
  console.error('styles:\n  ' + wrong.join('\n  '))
  process.exit(1)
}
console.log(`styles: ${modules.length} modules, every class drawn is declared`)
