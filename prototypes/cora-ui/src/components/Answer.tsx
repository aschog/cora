import { BLOCK_TABLE, QUESTION } from '../data'

type Props = { onCite: (key: string) => void }

export default function Answer({ onCite }: Props) {
  const cite = (n: string, key: string) => (
    <button className="cite" onClick={() => onCite(key)} aria-label={'Open cited source ' + n}>
      {n}
    </button>
  )

  return (
    <main className="answer">
      <div>
        <div className="micro">YOU ASKED</div>
        <p className="question">{QUESTION}</p>
      </div>

      <div className="answer-body">
        <p>
          Your squat isn’t stalling from programming volume — it’s stalling from recovery. Mean sleep over the last 21
          days is 5h 48m against your 7h 15m baseline{cite('1', 'sleep')}, and every one of the three missed top sets
          landed on a day following a night under six hours{cite('2', 'log')}. Your March ferritin came back at 31
          ng/mL, low-normal and consistent with the flatness you’re describing{cite('3', 'blood')}.
        </p>

        <p>
          So the next four weeks hold intensity and cut density. Four sessions, as you prefer, with the heavy squat
          moved off Monday — the day after your worst sleep, every week in the log.
        </p>

        <table className="block-table">
          <thead>
            <tr>
              <th>Week</th>
              <th>Squat</th>
              <th>Volume</th>
              <th>Intent</th>
            </tr>
          </thead>
          <tbody>
            {BLOCK_TABLE.map((row) => (
              <tr key={row.week}>
                <td>{row.week}</td>
                <td>{row.squat}</td>
                <td>{row.volume}</td>
                <td>{row.intent}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <p className="answer-coda">
          Retest in four weeks. If sleep is still under six hours by week two, I’ll hold week 3 rather than progress it —
          flag me and I’ll rewrite.
        </p>
      </div>

      <div className="composer">
        <span className="composer-glyph">›</span>
        <input placeholder="Ask in your own words…" aria-label="Ask in your own words" />
        <button className="composer-ask">Ask</button>
      </div>
    </main>
  )
}
