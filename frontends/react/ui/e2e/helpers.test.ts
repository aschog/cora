import { describe, expect, test } from 'vitest'
import { contrast, over } from './helpers'

/* What a browser may answer with when a spec asks for a resolved colour. The alpha is
   the point: a veil rated as the colour it is mixed from is a number about something
   nobody sees. */
describe('a resolved colour', () => {
  test.each([
    ['rgb(10, 12, 17)', 'rgb(255, 255, 255)', 'rgb(10, 12, 17)'],
    ['rgba(47, 129, 247, 0.32)', 'rgb(10, 12, 17)', 'rgb(22, 49, 91)'],
    ['rgb(47 129 247 / 32%)', 'rgb(10, 12, 17)', 'rgb(22, 49, 91)'],
    ['color(srgb 0.184 0.506 0.969 / 0.32)', 'rgb(10, 12, 17)', 'rgb(22, 49, 91)'],
  ])('%s over %s composites to %s', (front, back, mixed) => {
    expect(over(front, back)).toBe(mixed)
  })

  test('a colour space whose name carries a digit is read by its channels', () => {
    expect(over('color(display-p3 0 0 0 / 1)', 'rgb(255, 255, 255)')).toBe(
      'rgb(0, 0, 0)',
    )
  })
})

describe('contrast', () => {
  test('white on black is the ratio WCAG names', () => {
    expect(contrast('rgb(255, 255, 255)', 'rgb(0, 0, 0)')).toBeCloseTo(21, 1)
  })

  test('a colour rated against itself is no contrast at all', () => {
    expect(contrast('rgb(47, 129, 247)', 'rgb(47, 129, 247)')).toBeCloseTo(1, 5)
  })

  /* The docstring says both are taken as opaque, and `--sunken` is a translucent token
     in the palette: a ratio against a colour that was never composited is a number
     that means nothing, so it is refused rather than reported. */
  test('a translucent colour is refused rather than rated', () => {
    expect(() => contrast('rgba(0, 0, 0, 0.28)', 'rgb(10, 12, 17)')).toThrow()
    expect(() => over('rgb(47, 129, 247)', 'rgba(0, 0, 0, 0.28)')).toThrow()
  })
})
