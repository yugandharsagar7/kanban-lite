import { formatDate, formatMoney, formatQuantity } from './format'
import type { Card } from './types'

// Fixed text from docs/requirements.md ("Board display"). The role name must
// match Role.bakery_manager in ROLE_DISPLAY_NAMES in backend/models.py.
const AWAITING_PAYMENT_LABEL = 'Awaiting payment (Bakery Manager)'

// One restock card.
export function CardTile({ card }: { card: Card }) {
  const hasDelay = Boolean(card.delay_reason || card.delay_next_action)

  return (
    <article className={card.is_overdue ? 'card card-overdue' : 'card'}>
      <h3 className="card-title">{card.ingredient}</h3>

      {(card.is_overdue || card.is_paid || card.awaiting_payment) && (
        <div className="card-badges">
          {card.is_overdue && <span className="badge badge-overdue">Overdue</span>}
          {card.is_paid && <span className="badge badge-paid">Paid</span>}
          {card.awaiting_payment && (
            <span className="badge badge-awaiting">{AWAITING_PAYMENT_LABEL}</span>
          )}
        </div>
      )}

      <dl className="card-details">
        <dt>Quantity</dt>
        <dd>
          {formatQuantity(card.quantity)} {card.unit}
        </dd>
        <dt>Estimated total</dt>
        <dd>{formatMoney(card.estimated_total)}</dd>
        <dt>Supplier</dt>
        <dd>{card.supplier}</dd>
        {card.expected_delivery_date && (
          <>
            <dt>Expected delivery</dt>
            <dd>{formatDate(card.expected_delivery_date)}</dd>
          </>
        )}
      </dl>

      {hasDelay && (
        <div className="card-delay">
          <p>
            <strong>Reason:</strong> {card.delay_reason}
          </p>
          <p>
            <strong>Next action:</strong> {card.delay_next_action}
          </p>
        </div>
      )}
    </article>
  )
}
