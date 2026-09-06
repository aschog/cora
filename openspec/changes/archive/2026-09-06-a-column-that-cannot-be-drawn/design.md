## Context

React unmounts the whole tree under an uncaught render error, so one bad citation costs
the whole window.

## The seam

- A boundary is a component, so where the boundaries go is where the failure stops.
- The page is already three columns, which is the granularity a reader would want.
- One boundary component, used four times, rather than a bespoke fallback per column.

## Why a class

- `getDerivedStateFromError` and `componentDidCatch` have no function-component form.
- This is the one place in the page where hooks cannot express what is needed.
- React 19's `onUncaughtError` reports, it does not draw a fallback.

## Where they go

- One per column, so a rail that throws costs that rail and not the conversation.
- Inside the rail rather than around it, so the control that folds the rail survives.
- Around the panels rather than the tab strip, so the strip is the way out.
- One at the root, for anything thrown outside a column.

## Keyed on the tab

- A boundary that failed stays failed until something remounts it.
- Keying the panel boundary on the tab makes switching tabs that remount.
- So a broken panel is escaped by moving away from it, without a reload.

## Trying again

- Resetting the flag re-draws the children rather than reloading the page.
- Where what threw is still there it throws again, which is the honest outcome.
- Where it was the document being read, opening another is the way past it.

## What the reader is told, and what is recorded

- The reader gets a sentence naming the part of the page, and what is untouched.
- The throw and the tree it came from go to the console, which is the only record.
- A sentence naming the exception would be cora repeating a stack trace at a reader.

## Guards and diagrams

- No port, no guard, no generated diagram changes.
