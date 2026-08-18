import { useEffect, useRef, useState } from 'react'
import { PLUGINS } from '../data'

type Props = { plugin: string; onPickPlugin: (name: string) => void }

export default function Header({ plugin, onPickPlugin }: Props) {
  const [menuOpen, setMenuOpen] = useState(false)
  const wrap = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!menuOpen) return
    const onDown = (e: MouseEvent) => {
      if (wrap.current && !wrap.current.contains(e.target as Node)) setMenuOpen(false)
    }
    document.addEventListener('mousedown', onDown)
    return () => document.removeEventListener('mousedown', onDown)
  }, [menuOpen])

  return (
    <header className="header">
      <div className="brand">
        <span className="brand-name">cora</span>
        <span className="micro">DOCUMENT AGENT</span>
      </div>

      <div className="plugin-wrap" ref={wrap}>
        <button
          className="plugin-badge"
          aria-expanded={menuOpen}
          aria-haspopup="menu"
          onClick={() => setMenuOpen((open) => !open)}
        >
          <span className="micro">PLUGIN</span>
          <span className="plugin-badge-name">{plugin}</span>
          <span className="plugin-badge-caret">▾</span>
        </button>
        {menuOpen && (
          <div className="plugin-menu" role="menu">
            <div className="micro plugin-menu-label">domain plugins — the agent stays the same</div>
            {PLUGINS.map((p) => (
              <button
                key={p.name}
                className="plugin-option"
                role="menuitem"
                onClick={() => {
                  onPickPlugin(p.name)
                  setMenuOpen(false)
                }}
              >
                <span className="plugin-option-name">{p.name}</span>
                <span className="plugin-option-tools"> · {p.tools}</span>
                <div className="plugin-option-blurb">{p.blurb}</div>
              </button>
            ))}
          </div>
        )}
      </div>
    </header>
  )
}
