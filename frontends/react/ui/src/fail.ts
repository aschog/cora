export const message = (failed: unknown) =>
  failed instanceof Error ? failed.message : String(failed)

export const reportTo = (say: (said: string) => void) => (failed: unknown) =>
  say(message(failed))
