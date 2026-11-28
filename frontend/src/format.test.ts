import { describe, expect, test } from 'vitest'

import { formatDate, formatMoney, formatQuantity } from './format'

describe('formatMoney', () => {
  test.each([
    // [text from the API, what the board shows]
    ['531.2500000', '$531.25'], // Saffron: 0.125 kg x 4250.0000
    ['22.0000000', '$22.00'],
    ['10.125', '$10.13'], // exactly half a cent rounds up
    ['10.1249', '$10.12'],
    ['1.005', '$1.01'], // with floats, Math.round(1.005 * 100) / 100 gives 1 (wrong)
    ['0.995', '$1.00'], // rounding carries into the dollars
    ['0.005', '$0.01'],
    ['0.004', '$0.00'],
    ['0', '$0.00'],
    ['1234.5', '$1,234.50'],
    ['1234567.891', '$1,234,567.89'],
    ['99999999999999999.999', '$100,000,000,000,000,000.00'], // too big for a float to hold exactly
  ])('%s shows as %s', (text, shown) => {
    expect(formatMoney(text)).toBe(shown)
  })

  test('text that is not a number is shown unchanged', () => {
    expect(formatMoney('n/a')).toBe('n/a')
  })
})

describe('formatQuantity', () => {
  test.each([
    ['25.000', '25'],
    ['0.125', '0.125'],
    ['18.500', '18.5'],
    ['1500.000', '1,500'],
    ['0', '0'],
  ])('%s shows as %s', (text, shown) => {
    expect(formatQuantity(text)).toBe(shown)
  })
})

describe('formatDate', () => {
  test.each([
    ['2026-11-20', 'Nov 20, 2026'],
    ['2026-01-05', 'Jan 5, 2026'],
    ['2026-12-31', 'Dec 31, 2026'],
  ])('%s shows as %s', (text, shown) => {
    expect(formatDate(text)).toBe(shown)
  })

  test('shows the bakery date, not the day before (midnight UTC trap)', () => {
    // Tests run in New York time (see vite.config.ts). The obvious JavaScript
    // way reads the date as midnight UTC, which is still the 19th in New York.
    expect(new Date('2026-11-20').getDate()).toBe(19)
    // formatDate reads the digits directly, so it keeps the 20th.
    expect(formatDate('2026-11-20')).toBe('Nov 20, 2026')
  })

  test('text that is not a date is shown unchanged', () => {
    expect(formatDate('soon')).toBe('soon')
    expect(formatDate('2026-13-01')).toBe('2026-13-01')
  })
})
