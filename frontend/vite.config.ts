import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  test: {
    // Run tests in the bakery's time zone, so date tests behave as they would there.
    env: { TZ: 'America/New_York' },
  },
})
