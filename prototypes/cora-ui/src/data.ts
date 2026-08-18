export type Paragraph = { text: string; cited?: boolean }

export type Doc = {
  key: string
  name: string
  title: string
  meta: string
  note: string
  body: Paragraph[]
}

export const QUESTION =
  'I’ve been flat on squats for three weeks and my sleep is trash. What should the next block look like?'

export const DOCS: Doc[] = [
  {
    key: 'intake',
    name: 'Intake form.pdf',
    title: 'Intake form.pdf',
    meta: 'page 1 of 3 · your document',
    note: 'This is where the plan’s four-session constraint comes from.',
    body: [
      { text: 'Intake form.pdf — page 1 of 3. Completed 2026-03-12.' },
      { text: 'Training age: 7 years. Current bodyweight 84kg. Equipment: full commercial gym.' },
      {
        cited: true,
        text: '“Four sessions a week, max. 180kg squat by December. Left knee tracks in under load — cue it. I will not do burpees.”',
      },
      { text: 'Prior injuries: left meniscus, 2022, non-surgical. Cleared for loaded squatting by physio, Nov 2022.' },
      { text: 'Sleep, self-reported: “6–7 hours, worse when travelling.”' },
      { text: 'Preferred contact: async. “Send the plan, don’t call me.”' },
    ],
  },
  {
    key: 'blood',
    name: 'Bloodwork_2026-03.pdf',
    title: 'Bloodwork_2026-03.pdf',
    meta: 'page 2 of 4 · your document',
    note: 'cora will not interpret this medically — it flags the value and cites the page.',
    body: [
      { text: 'Bloodwork_2026-03.pdf — page 2 of 4. Collected 2026-03-09, fasting. Reference ranges per lab.' },
      { text: 'Complete blood count within reference range. Hemoglobin 14.6 g/dL. Hematocrit 43%. MCV 89 fL.' },
      {
        cited: true,
        text: 'Ferritin 31 ng/mL (ref. 24–336). Vitamin D 28 ng/mL (ref. 30–100). Note from ordering physician: recheck in six months.',
      },
      { text: 'TSH 1.9 mIU/L. Free T4 1.2 ng/dL. No further flags.' },
      { text: 'Lipids: total 178 mg/dL, HDL 58, LDL 102, triglycerides 89.' },
      {
        text: 'Comment: “Iron stores at the low end for an athlete in a heavy training block. Dietary review advised before supplementation.”',
      },
    ],
  },
  {
    key: 'log',
    name: 'Training log (Notion export)',
    title: 'Training log (Notion export).csv',
    meta: '1,204 rows · last edited yesterday · your document',
    note: 'Passage located by search, not by keyword match — cora read the surrounding rows to confirm the pattern.',
    body: [
      { text: 'Training log (Notion export).csv — 1,204 rows, columns: date, block, session, lift, prescription, result, note.' },
      { text: '2026-07-28 back squat 4×5 @ 140kg — all sets complete. Note: “felt easy.”' },
      { text: '2026-07-31 front squat 3×6 @ 105kg — complete. RDL 3×8 @ 130kg.' },
      {
        cited: true,
        text: '2026-08-04 back squat 4×5 @ 145kg — set 4 failed at rep 3. Note: “legs felt hollow, 5h sleep.” Same pattern 08-11 and 08-15.',
      },
      { text: '2026-08-08 bench 5×5 @ 100kg — complete. Upper body sessions unaffected across the block.' },
      { text: '2026-08-11 back squat 4×5 @ 145kg — set 4 failed at rep 4. Note: “same as last week.”' },
      { cited: true, text: '2026-08-15 back squat 4×5 @ 145kg — set 3 failed at rep 5, set 4 skipped.' },
      { text: 'Front squat and RDL loads unchanged across the block. Session attendance 12 of 12.' },
    ],
  },
  {
    key: 'sleep',
    name: 'Whoop export — sleep',
    title: 'Whoop export — sleep, 21 days',
    meta: 'wearable.sleep() · pulled 4 min ago · plugin tool',
    note: 'Returned by the fitness plugin, not stored by cora. The plan cites the numbers it actually read.',
    body: [
      {
        text: 'WHOOP export — sleep & recovery, 2026-07-28 → 2026-08-17. Units: hours:minutes. Baseline computed over trailing 90 days.',
      },
      { text: 'Week of 07-28 — mean 6h 22m · 3 nights under 6h · HRV 61ms · RHR 54bpm.' },
      { text: 'Week of 08-04 — mean 5h 31m · 5 nights under 6h · HRV 52ms · RHR 58bpm. Two late flights logged.' },
      { cited: true, text: 'Week of 08-11 — mean 5h 30m · 3 nights under 6h · HRV 54ms · RHR 57bpm.' },
      {
        cited: true,
        text: 'Mean sleep duration 5h 48m (baseline 7h 15m). 11 of 21 nights under 6h. Mean respiratory rate stable; HRV −14% vs. 90-day mean.',
      },
      { text: 'Sleep debt accumulating from 2026-07-31 onward. No recovery scores above 70% after 08-03.' },
      { text: 'Nap data excluded. Two nights (08-09, 08-16) flagged low-confidence — strap disconnected.' },
    ],
  },
  {
    key: 'notes',
    name: 'Coach notes — Feb.md',
    title: 'Coach notes — Feb.md',
    meta: '4 entries · your document',
    note: 'Read during indexing, not used in this answer — nothing here bore on the stall.',
    body: [
      { text: 'Coach notes — Feb.md. Indexed 2026-03-01, four entries, free text.' },
      { text: 'Feb 3 — moved heavy squat to Tuesday for two weeks; complained about Monday sessions after travel.' },
      { text: 'Feb 11 — knee cue landing well: “knees over mid-foot, spread the floor.” Keep using it.' },
      { text: 'Feb 19 — asked for fewer accessories. Cut arms to one slot.' },
      { text: 'Feb 27 — mood good, loads climbing. No recovery complaints this month.' },
    ],
  },
  {
    key: 'physio',
    name: 'Physio discharge letter.pdf',
    title: 'Physio discharge letter.pdf',
    meta: '1 page · your document',
    note: 'Available to cora, not cited here. It informs the knee cue, not the block.',
    body: [
      { text: 'Physio discharge letter.pdf — 2022-11-14. One page, signed.' },
      { text: 'Left meniscus, posterior horn, managed non-surgically. Full range of motion restored.' },
      { text: 'Cleared for loaded bilateral squatting without depth restriction. Advise single-leg work twice weekly.' },
      { text: 'No follow-up scheduled. Return if joint line pain recurs under load.' },
    ],
  },
]

export type PlanStep = {
  n: number
  label: string
  call: string
  result: string
  origin: string
}

export const PLAN_STEPS: PlanStep[] = [
  {
    n: 1,
    label: 'Read the client’s goals and constraints',
    call: 'docs.search("goals, sessions per week, constraints")',
    result: 'Intake form.pdf → 4 sessions/wk max, 180kg by December, knee cue',
    origin: 'core retrieval',
  },
  {
    n: 2,
    label: 'Pull the last 21 days of sessions',
    call: 'training_log.query(range: "21d", lift: "back squat")',
    result: '3 missed top sets: 08-04, 08-11, 08-15',
    origin: 'plugin tool · fitness-coach',
  },
  {
    n: 3,
    label: 'Check recovery markers against baseline',
    call: 'wearable.sleep(range: "21d", compare: "baseline")',
    result: 'Mean 5h48m vs 7h15m baseline; HRV −14%',
    origin: 'plugin tool · fitness-coach',
  },
  {
    n: 4,
    label: 'Cross-check labs before blaming programming',
    call: 'docs.search("ferritin, vitamin D, hemoglobin")',
    result: 'Bloodwork_2026-03.pdf p.2 → ferritin 31 ng/mL',
    origin: 'core retrieval',
  },
  {
    n: 5,
    label: 'Draft a four-week block that holds intensity',
    call: 'periodize(model: "undulating", weeks: 4, sessions: 4)',
    result: 'Volume −20% wk1, retest wk4',
    origin: 'plugin tool · fitness-coach',
  },
]

export const PLAN_FOOTER =
  'cora chose these steps. Nothing here is a fixed pipeline — the tools come from the loaded plugin.'

export const BLOCK_TABLE = [
  { week: '1', squat: '4 × 4 @ 82%', volume: '−20%', intent: 'Reset, no misses' },
  { week: '2', squat: '4 × 3 @ 85%', volume: '−15%', intent: 'Speed off the floor' },
  { week: '3', squat: '3 × 2 @ 89%', volume: '−15%', intent: 'Heavy, low fatigue' },
  { week: '4', squat: 'Single @ 92%', volume: '−40%', intent: 'Test, then deload' },
]

export type Plugin = { name: string; tools: string; blurb: string }

export const PLUGINS: Plugin[] = [
  { name: 'fitness-coach v0.4', tools: '6 tools', blurb: 'training_log, wearable, periodize, nutrition…' },
  { name: 'clinic-intake v0.2', tools: '4 tools', blurb: 'ehr_lookup, triage, referral, scheduling' },
  { name: 'legal-discovery v0.1', tools: '5 tools', blurb: 'docket, precedent, redact, privilege_log' },
]

export type Inference = { id: string; text: string; session: string }

export const INFERENCES: Inference[] = [
  { id: 'sessions', text: 'Four sessions a week — never proposes five', session: 'session 1' },
  { id: 'knee', text: 'Left knee tracks in under load; cue it every squat block', session: 'session 1' },
  { id: 'burpees', text: 'Won’t do burpees. Stop offering conditioning circuits', session: 'session 3' },
  { id: 'tables', text: 'Prefers plans as tables, reasoning underneath', session: 'session 6' },
  { id: 'ferritin', text: 'Ferritin low-normal since March — recheck due September', session: 'session 11' },
]

export const SESSIONS_INTRO =
  'What cora inferred on its own, session by session. Editable — forget a line and it stops assuming it.'

export type SavedLine = { id: string; text: string; stamp: string }

export const SAVED_LINES: SavedLine[] = [
  { id: 'four', text: 'Four sessions a week, max. Never propose five.', stamp: 'saved by you · 12 Mar · session 1' },
  { id: 'burpees', text: 'No burpees, no conditioning circuits. Ever.', stamp: 'saved by you · 2 Apr · session 3' },
  {
    id: 'table',
    text: 'Give me the plan as a table first, reasoning underneath.',
    stamp: 'saved by you · 19 May · session 6',
  },
  { id: 'ferritin', text: 'Recheck ferritin in September — remind me.', stamp: 'saved by you · 4 Aug · session 11' },
]

export const MEMORY_FOOTER = '4 saved · used in 2 of this answer’s steps.'

export const SESSION_LINE = 'session 14 · continued from Tue'

export const uploadedDoc = (name: string): Doc => ({
  key: 'upload:' + name,
  name,
  title: name,
  meta: 'just added · indexing',
  note: 'Newly added, not yet cited.',
  body: [
    { text: 'Indexing ' + name + ' …' },
    {
      text: 'cora reads the file locally, then makes it available to the plan. Ask a question and it decides whether this document belongs in the answer.',
    },
  ],
})
