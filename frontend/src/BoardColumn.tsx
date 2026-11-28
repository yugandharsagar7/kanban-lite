import { CardTile } from './CardTile'
import type { Column } from './types'

// One column: its name, whose turn it is, then its cards in order.
export function BoardColumn({ column }: { column: Column }) {
  const headingId = `column-${column.id}`
  // Final columns (Restocked) have no next step, so nobody's turn.
  const turn = column.is_final ? 'Done' : `Turn: ${column.responsible_role_name ?? 'not set'}`

  return (
    <section className="column" aria-labelledby={headingId}>
      <header className="column-header">
        <div>
          <h2 id={headingId}>{column.name}</h2>
          <p className="column-turn">{turn}</p>
        </div>
        <span className="column-count" aria-label={`${column.cards.length} cards`}>
          {column.cards.length}
        </span>
      </header>

      {column.cards.length === 0 ? (
        <p className="column-empty">No cards</p>
      ) : (
        <ul className="card-list">
          {column.cards.map((card) => (
            <li key={card.id}>
              <CardTile card={card} />
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
