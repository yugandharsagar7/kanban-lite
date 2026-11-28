import type { Column } from './types'

// The API address comes from frontend/.env (VITE_API_URL). This is the only
// place that reads it.
export const API_URL: string = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000'

// Ask the API for the whole board. Throws an error if it can't be reached or
// answers with an error, so the page can show a message.
export async function fetchBoard(signal?: AbortSignal): Promise<Column[]> {
  const response = await fetch(`${API_URL}/board`, { signal })
  if (!response.ok) {
    throw new Error(`The API answered with an error (${response.status}).`)
  }
  return (await response.json()) as Column[]
}
