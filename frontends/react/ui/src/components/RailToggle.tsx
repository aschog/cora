import styles from './RailToggle.module.css'

type Props = { side: 'left' | 'right'; open: boolean; label: string; onToggle: () => void }

/** The rail's own outline, filled on the side it stands. */
export default function RailToggle({ side, open, label, onToggle }: Props) {
  const x = side === 'left' ? 3.2 : 12.2
  const rule = side === 'left' ? 7.8 : 12.2
  return (
    <button
      className={styles.railToggle}
      title={label}
      aria-label={label}
      aria-pressed={open}
      onClick={onToggle}
    >
      <svg width="19" height="19" viewBox="0 0 20 20" fill="none" aria-hidden="true">
        <rect x="2.5" y="3.5" width="15" height="13" rx="2.5" stroke="currentColor" strokeWidth="1.4" />
        <rect x={x} y="4.2" width="4.6" height="11.6" rx="1.8" fill="currentColor" fillOpacity={open ? 0.9 : 0.2} />
        <line x1={rule} y1="3.5" x2={rule} y2="16.5" stroke="currentColor" strokeWidth="1.4" />
      </svg>
    </button>
  )
}
