import { useEffect, useState } from 'react'

import { API_URL, fetchBoard } from './api'
import { BoardColumn } from './BoardColumn'
import type { Column } from './types'
import './App.css'

// What the page is showing: still loading, an error, or the board.
type BoardState =
  | { kind: 'loading' }
  | { kind: 'error' }
  | { kind: 'ready'; columns: Column[] }

function App() {
  const [state, setState] = useState<BoardState>({ kind: 'loading' })
  // Goes up by one on "Try again", which makes the effect below fetch again.
  const [attempt, setAttempt] = useState(0)

  // Runs after the page first appears (and again after each "Try again").
  useEffect(() => {
    // Lets us cancel this request if it's no longer needed: React's StrictMode
    // runs effects twice in development, and only one answer should be used.
    const controller = new AbortController()
    fetchBoard(controller.signal)
      .then((columns) => setState({ kind: 'ready', columns }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return
        console.error('Could not load the board:', error)
        setState({ kind: 'error' })
      })
    return () => controller.abort()
  }, [attempt])

  function tryAgain() {
    setState({ kind: 'loading' })
    setAttempt((n) => n + 1)
  }

  return (
    <div className="page">
      <header className="page-header">
        <h1>Sunrise Bakery</h1>
        <p className="page-subtitle">Restock board</p>
      </header>

      {state.kind === 'loading' && (
        <p className="message" role="status">
          Loading the board…
        </p>
      )}

      {state.kind === 'error' && (
        <div className="message message-error" role="alert">
          <p>
            <strong>Can't reach the restock board.</strong>
          </p>
          <p>
            The page couldn't get the board from the API at <code>{API_URL}</code>. Check that
            the back end is running (from <code>backend/</code>: <code>uvicorn main:app --reload</code>),
            then try again.
          </p>
          <button type="button" onClick={tryAgain}>
            Try again
          </button>
        </div>
      )}

      {state.kind === 'ready' && state.columns.length === 0 && (
        <p className="message">
          The board has no columns yet. To add the demo data, run <code>python seed.py</code> in{' '}
          <code>backend/</code>.
        </p>
      )}

      {state.kind === 'ready' && state.columns.length > 0 && (
        <main className="board">
          {state.columns.map((column) => (
            <BoardColumn key={column.id} column={column} />
          ))}
        </main>
      )}
    </div>
  )
}

export default App
