import { useState } from 'react'
import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

/** A component drawn on its own, given the store its reads go through. Its own store per
 *  render, so what one test read is not still held when the next one asks — and no
 *  retries, so a read that was refused is refused once and the assertion is about the
 *  sentence rather than about waiting for three attempts. */
export default function WithStore({ children }: { children: ReactNode }) {
  const [store] = useState(
    () => new QueryClient({ defaultOptions: { queries: { retry: false } } }),
  )
  return <QueryClientProvider client={store}>{children}</QueryClientProvider>
}
