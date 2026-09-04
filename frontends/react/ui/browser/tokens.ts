/** What the browser resolved a token to, in the form a computed style reports it — so a
 *  test names the token it means rather than the hex behind it. */
export const resolved = (token: string) => {
  const probe = document.createElement('div')
  probe.style.color = `var(${token})`
  document.body.appendChild(probe)
  const seen = getComputedStyle(probe).color
  probe.remove()
  return seen
}

const luminance = (colour: string) => {
  const [r, g, b] = colour.match(/\d+/g)!.map((each) => {
    const part = Number(each) / 255
    return part <= 0.04045 ? part / 12.92 : ((part + 0.055) / 1.055) ** 2.4
  })
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

/** WCAG's ratio between two resolved colours, so a test can say "visible" as a number. */
export const contrast = (one: string, other: string) => {
  const [light, dark] = [luminance(one), luminance(other)].sort((a, b) => b - a)
  return (light + 0.05) / (dark + 0.05)
}
