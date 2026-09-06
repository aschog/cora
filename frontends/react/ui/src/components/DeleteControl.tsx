import styles from './DeleteControl.module.css'

type Props = {
  /** What this control would delete, in the reader's own words. It is the control's
   *  whole name: a column of identical icons says nothing about which row is which,
   *  to a screen reader or to anyone hovering one. */
  what: string
  onDelete: () => void
}

/** The one delete control the rails share, drawn as an icon and named for its row. */
export default function DeleteControl({ what, onDelete }: Props) {
  return (
    <button
      className={styles.rowDelete}
      title={`Delete ${what}`}
      aria-label={`Delete ${what}`}
      onClick={onDelete}
    >
      <svg width="15" height="15" viewBox="0 0 20 20" fill="none" aria-hidden="true">
        <path
          d="M3.6 5.6h12.8M7.9 5.6V3.9h4.2v1.7M5.3 5.6l.8 10.2a1.4 1.4 0 0 0 1.4 1.3h5a1.4 1.4 0 0 0 1.4-1.3l.8-10.2"
          stroke="currentColor"
          strokeWidth="1.3"
          strokeLinecap="round"
        />
        <path
          d="M8.4 8.5v5.5M11.6 8.5v5.5"
          stroke="currentColor"
          strokeWidth="1.3"
          strokeLinecap="round"
        />
      </svg>
    </button>
  )
}
