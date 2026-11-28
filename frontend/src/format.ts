// Turning the API's exact text values into display text.
//
// Money and quantities arrive as exact decimal text, such as "531.2500000".
// None of these functions ever turns that text into a JavaScript number,
// because JavaScript numbers are floats and can't hold most decimals exactly
// (in floats, 1.005 * 100 is 100.49999999999999). Instead they work on the
// digits as text, and use BigInt (exact whole numbers of any size) for cents.

const DECIMAL_TEXT = /^(-?)(\d+)(?:\.(\d+))?$/

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

/** Group whole-number digits with commas, e.g. "1234567" -> "1,234,567". */
function groupDigits(digits: string): string {
  return BigInt(digits).toLocaleString('en-US')
}

/**
 * Exact money text -> US dollars rounded to 2 decimals, for display only.
 * "531.2500000" -> "$531.25", "10.125" -> "$10.13" (half rounds up).
 * Text that isn't a decimal number is returned unchanged.
 */
export function formatMoney(text: string): string {
  const match = DECIMAL_TEXT.exec(text.trim())
  if (!match) return text
  const [, sign, whole, decimals = ''] = match

  // Work in whole cents: dollars x 100 + the first two decimals.
  const digits = decimals.padEnd(3, '0')
  let cents = BigInt(whole) * 100n + BigInt(digits.slice(0, 2))
  // The third decimal decides the rounding: 5 or more rounds up.
  if (digits[2] >= '5') cents += 1n

  const dollars = (cents / 100n).toString()
  const rest = (cents % 100n).toString().padStart(2, '0')
  const minus = sign && cents !== 0n ? '-' : ''
  return `${minus}$${groupDigits(dollars)}.${rest}`
}

/**
 * Exact quantity text -> shown in full, without trailing zeros (never rounded).
 * "25.000" -> "25", "0.125" -> "0.125", "18.500" -> "18.5".
 */
export function formatQuantity(text: string): string {
  const match = DECIMAL_TEXT.exec(text.trim())
  if (!match) return text
  const [, sign, whole, decimals = ''] = match
  const trimmed = decimals.replace(/0+$/, '')
  return `${sign}${groupDigits(whole)}${trimmed ? `.${trimmed}` : ''}`
}

/**
 * The bakery's date as "YYYY-MM-DD" -> "Nov 20, 2026".
 * Reads the year, month and day straight from the text. It deliberately avoids
 * new Date("2026-11-20"), which means midnight in UTC and shows as
 * 19 November in New York.
 */
export function formatDate(text: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(text.trim())
  if (!match) return text
  const [, year, month, day] = match
  const monthName = MONTHS[Number(month) - 1]
  if (!monthName) return text
  return `${monthName} ${Number(day)}, ${year}`
}
