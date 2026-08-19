import { useEffect, useRef, useState } from 'react'
import RailToggle from './RailToggle'

type Props = {
  plugins: string[]
  leftOpen: boolean
  rightOpen: boolean
  onToggleLeft: () => void
  onToggleRight: () => void
  onNew: () => void
  canStart: boolean
}

const BARE = 'bare cora'
const HEADING = 'domain plugins — the agent stays the same'
const FIXED = 'Named by the deployment in CORA_PLUGINS, and bound when cora was assembled.'

export default function Header({
  plugins,
  leftOpen,
  rightOpen,
  onToggleLeft,
  onToggleRight,
  onNew,
  canStart,
}: Props) {
  const [open, setOpen] = useState(false)
  const wrap = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const away = (e: MouseEvent) => {
      if (wrap.current && !wrap.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', away)
    return () => document.removeEventListener('mousedown', away)
  }, [open])

  return (
    <header className="header">
      <RailToggle side="left" open={leftOpen} label="Documents" onToggle={onToggleLeft} />

      <span className="brand-name">cora</span>
      <span className="micro">DOCUMENT AGENT</span>

      <div className="plugin-wrap" ref={wrap}>
        <button
          className="plugin-badge"
          aria-expanded={open}
          aria-haspopup="true"
          onClick={() => setOpen((shown) => !shown)}
        >
          <svg className="plug" width="17" height="17" viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <path
              d="M7 3v3.2M13 3v3.2M4.5 6.5h11v4.2a5.5 5.5 0 0 1-11 0Z"
              stroke="currentColor"
              strokeWidth="1.4"
              strokeLinejoin="round"
            />
            <path d="M10 16.2V18" stroke="currentColor" strokeWidth="1.4" />
          </svg>
          <span className="plugin-badge-name">
            {plugins.length === 0 ? BARE : plugins.map(shortly).join(' · ')}
          </span>
          <span className="plugin-badge-caret">▾</span>
        </button>
        {open && (
          <div className="plugin-menu">
            <div className="micro plugin-menu-heading">{HEADING}</div>
            {plugins.length === 0 ? (
              <div className="plugin-option-blurb">No plugin is loaded.</div>
            ) : (
              plugins.map((module) => (
                <div key={module} className="plugin-option">
                  <span className="plugin-option-name">{shortly(module)}</span>
                  <div className="plugin-option-blurb">{module}</div>
                </div>
              ))
            )}
            <div className="plugin-menu-foot">{FIXED}</div>
          </div>
        )}
      </div>

      {/* Reachable while it is unavailable: `disabled` would take it out of the
          accessibility tree, and having nothing to start is something to be told. */}
      <button
        className="new-session"
        aria-disabled={!canStart}
        onClick={() => canStart && onNew()}
      >
        <span className="new-session-plus" aria-hidden="true">
          +
        </span>
        New session
      </button>

      <RailToggle
        side="right"
        open={rightOpen}
        label="Plan & memory"
        onToggle={onToggleRight}
      />
    </header>
  )
}

/** `cora.plugins.fitness` reads as `fitness` on a badge; the menu keeps the full name. */
const shortly = (module: string) => module.split('.').pop() ?? module
