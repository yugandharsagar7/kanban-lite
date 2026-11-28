// Shapes of the data the API sends from GET /board.
// They mirror ColumnOut and CardOut in backend/schemas.py: keep them in step.

// Role codes, as in Role in backend/models.py.
export type RoleCode = 'kitchen_assistant' | 'head_chef' | 'bakery_manager' | 'owner'

export interface Card {
  id: number
  ingredient: string
  unit: string
  // Money and quantities arrive as exact text (for example "531.2500000").
  // They stay text: turning them into JavaScript numbers would add float errors.
  quantity: string
  unit_price: string
  estimated_total: string
  supplier: string
  // The bakery's date as "YYYY-MM-DD", or null when there is none.
  expected_delivery_date: string | null
  is_paid: boolean
  delay_reason: string | null
  delay_next_action: string | null
  is_overdue: boolean
  awaiting_payment: boolean
}

export interface Column {
  id: number
  name: string
  position: number
  responsible_role: RoleCode | null
  responsible_role_name: string | null
  is_final: boolean
  cards: Card[]
}
