/** The classes to draw, leaving out the ones that do not apply. Written here rather than
 *  taken as a dependency: what the packages for this do is this line, and a conditional
 *  spelled as a ternary over two template literals says the base class twice — which is
 *  two places for it to be wrong. */
export const joined = (...names: (string | false | null | undefined)[]) =>
  names.filter(Boolean).join(' ')
