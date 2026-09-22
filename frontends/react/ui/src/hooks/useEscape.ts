import { useEffect } from 'react'

/** Escape closes what is on top of the page.
 *
 *  Bound on the document rather than on the dialog, because the key has to work before
 *  anything inside has been clicked. Written once: three dialogs had the same listener,
 *  and the one that would have been missed is the one nobody has a test for.
 */
export function useEscape(onEscape: () => void) {
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onEscape()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onEscape])
}
