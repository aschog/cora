import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@fontsource/source-serif-4/400.css'
import '@fontsource/source-serif-4/600.css'
import '@fontsource/source-serif-4/400-italic.css'
import './styles.css'
import App from './App'
import ErrorBoundary from './components/ErrorBoundary'

/* The last resort, under the three the page draws inside itself: what throws outside a
   column takes the window with it, and a blank window says nothing at all. */
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary said="cora could not draw this page. Your conversations, documents and memory are untouched.">
      <App />
    </ErrorBoundary>
  </StrictMode>,
)
