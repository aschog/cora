import { Component } from 'react'
import type { ErrorInfo, ReactNode } from 'react'

type Props = {
  /** What this part of the page is, in the sentence the reader gets instead of it. */
  said: string
  children: ReactNode
}

type State = { failed: boolean }

/**
 * What is drawn where a part of the page threw while rendering. React unmounts the whole
 * tree under an uncaught render error, so without one of these a bad offset in one
 * citation leaves the reader a blank window and no way to tell what happened.
 *
 * A class because this is the one thing hooks cannot do: `getDerivedStateFromError` and
 * `componentDidCatch` have no function-component equivalent.
 *
 * Trying again re-mounts the children rather than reloading. Where the thing that threw
 * is still there it throws again, which is the honest outcome — and where it was the
 * document the reader had open, moving to another one is the way past it.
 */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { failed: false }

  static getDerivedStateFromError(): State {
    return { failed: true }
  }

  componentDidCatch(failed: Error, where: ErrorInfo) {
    /* The reader is told a sentence; whoever is looking at the console gets the throw
       and the tree it came from, which is the only record of it. */
    console.error('cora could not draw the page:', failed, where.componentStack)
  }

  render() {
    if (!this.state.failed) return this.props.children
    return (
      <div className="broke" role="alert">
        <p>{this.props.said}</p>
        <button
          type="button"
          className="broke-again"
          onClick={() => this.setState({ failed: false })}
        >
          Try again
        </button>
      </div>
    )
  }
}
