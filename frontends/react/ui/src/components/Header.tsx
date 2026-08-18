type Props = { plugins: string[] }

const BARE = 'bare cora'

export default function Header({ plugins }: Props) {
  return (
    <header className="header">
      <div className="brand">
        <span className="brand-name">cora</span>
        <span className="micro">DOCUMENT AGENT</span>
      </div>

      <div className="plugin-badge" title="Plugins are named by the deployment">
        <span className="micro">PLUGIN</span>
        {plugins.length === 0 ? (
          <span className="plugin-badge-name">{BARE}</span>
        ) : (
          plugins.map((name) => (
            <span key={name} className="plugin-badge-name">
              {name}
            </span>
          ))
        )}
      </div>
    </header>
  )
}
