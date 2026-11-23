# Kanban Lite: Requirements (v1)

## Goal
A restocking board for a small bakery (demo business: "Sunrise Bakery", fictional).
Kitchen staff flag ingredients that are running low. Each request moves through
review, approval, ordering and delivery on one shared board, so everyone can see
what is needed, what is approved and what is late.

## Users (roles)
- Kitchen Assistant: flags ingredients that are running low.
- Head Chef: reviews cards in Running low twice a day, confirms or adjusts
  quantities, moves approved cards to Manager review, and signs off each
  review, even when there are zero items.
- Bakery Manager: reviews cards in Manager review, confirms the supplier and
  exact price, sends them to the owner, places orders, handles delays, and
  can delete cards created by mistake.
- Owner: gives the last approval before ordering, seeing the estimated total.

In v1 there is no sign-in, and anyone can do any action. Role rules come with
sign-in in a later version.

## Board columns
Running low -> Manager review -> Owner review -> Ordered -> Restocked,
plus Delayed.

Each column shows whose turn it is. Moving a card forward is that person's
approval, and the card history records who moved it and when.

Each status records the role whose turn it is to act on cards in that column:
- Running low: Head Chef
- Manager review: Bakery Manager
- Owner review: Owner
- Ordered: Bakery Manager
- Delayed: Bakery Manager
- Restocked: none (final status)

Once sign-in is added, the same field decides who may move cards out of that
column.

Restocked is a final, success status with no next step forward, so it has no
role. A status records whether it is final.

From owner approval until the card is complete, the Bakery Manager is
accountable for the restock, including supplier problems and delays. A card is
complete when it is in Restocked and marked paid.

## Card movement rules
- A card moves one step at a time, forward or back.
- Moving a card back requires a note explaining why. The person in the
  earlier step reads the note, acts on it and moves the card forward again.
- There is no reject action. An owner who doesn't approve a card moves it
  back to Manager review with a note.
- A card can move to Delayed only from Ordered, with a reason and a next
  action, and returns to Ordered when the problem is solved.
- A restocked card can move back to Ordered, with a note (for example, a
  wrong delivery).
- The unit price can be edited only in Manager review. It locks when the
  card moves to Owner review, and unlocks if it moves back.
- Only the bakery manager can delete a card (for example, one created by
  mistake). Delete needs a reason. A deleted card is hidden from the board
  but kept in the history. Role rules are enforced once sign-in is added.
- The bakery manager marks a card paid once it is in Ordered or later
  (Ordered, Delayed or Restocked). The card records who marked it and when.
- A card that has been marked paid cannot move back from Ordered.
- A card that has been marked paid cannot be deleted.

## Board display
- A card is overdue when its expected delivery date is before the bakery's
  today and it is in Ordered or Delayed. The board marks overdue cards.
- The board shows each delayed card's reason and next action.
- A restocked card that isn't paid yet shows "Awaiting payment (Bakery
  Manager)".

## User stories (v1)
1. As a kitchen assistant, I can create a restock card for an ingredient. It
   appears in Running low with that ingredient's regular restock quantity.
2. As a head chef, I can change the quantity on a card (for example, more than
   usual when I expect extra customers), and the estimated total updates
   (quantity x price per unit).
3. As anyone, I can drag a card one step forward or back, following the card
   movement rules.
4. As a bakery manager, when I move a card to Delayed, I must enter a reason
   (for example, supplier out of stock) and a next action (for example, try
   another supplier or collect from the warehouse).
5. As a head chef, I can sign off a review session (morning or afternoon),
   including when there are zero items to approve.
6. As a bakery manager, I see a red alert on the board if the morning review is
   not signed off by 12:00, or the afternoon review by 17:00.
7. As anyone, I can see a card's history: who moved it, when, and from which
   column to which.
8. As anyone, I can filter cards by supplier or ingredient, or show in-progress
   orders (in Ordered or Delayed) with their expected delivery date.
9. As anyone, when I move a card back one step, I must enter a note
   explaining why.
10. As a bakery manager, I can edit a card's unit price until I move it to
    Owner review.
11. As a bakery manager, I can delete a card created by mistake, with a
    reason. It is hidden from the board but kept in the history.
12. As a bakery manager, I can mark a card paid once it is in Ordered or later.

## Out of scope for v1 (planned later)
- Sign-in and role rules (only the owner can move a card on from Owner review, and so on)
- One-time purchase requests (a bulb, a chair, a temporary cleaner)
- Notifications for missed reviews (v1 shows an alert on the board only)
- Opening days and public holidays in admin settings (v1 assumes open every day)
- Reports over time (week, month, 3, 6 and 12 months) and usage metrics
- Mobile layout; more than one bakery

## Open questions
- How are refunds or cancelled paid orders handled? Out of scope for v1.

## Non-functional requirements
- Works in Chrome and Edge.
- The board loads in under 2 seconds with 200 cards.
- All data changes go through the API.
- Times are stored in UTC and shown in the bakery's local time.
- The bakery's time zone is America/New_York. 'Today', business dates and the
  12:00 and 17:00 review deadlines use this time zone. Times are still stored
  in UTC.
- Money and quantities are stored exactly, with no rounding errors.
- Quantities keep up to 3 decimal places and unit prices up to 4. A value with
  more decimal places is rejected with a clear message, never rounded.
- Totals are rounded to 2 decimal places only for display; calculations use
  the full values.
- In v1 (SQLite), all money calculations are done in Python, never in the
  database. See docs/decisions/0001-money-storage.md.
- Payments: the app records only that an order was paid. It never stores
  card details.
- All demo data is made up.

## Data model (starting point)
- Supplier: id, name, phone, address
- Ingredient: id, name, unit (kg, litres, dozen, pieces), price_per_unit,
  regular_restock_qty, usual_delivery_days, supplier_id
- RestockStatus: id, name, position, responsible_role, is_final

  responsible_role is one of the roles under "Users (roles)". It is empty only
  for final statuses, and is_final is true only for Restocked.
- RestockCard: id, ingredient_id, status_id, supplier_id, quantity,
  unit_price, expected_delivery_date, delay_reason, delay_next_action,
  position, created_at, paid_at, paid_by, deleted_at, deleted_by,
  deleted_reason
- CardEvent: id, card_id, action, from_status_id, to_status_id, actor, note,
  timestamp

  action is one of: created, moved, edited, paid, deleted. A move back one step
  must include a note. Marking a card paid records a "paid" event. Deletes are
  also recorded as events, so the history is complete.
  A delete must include the reason as its note. A move to Delayed records the
  reason and next action in its note, so past delays stay in the history. An
  edit records what changed, from and to, in its note. from_status_id and
  to_status_id are filled only for moves (and to_status_id for created).
- ReviewSignOff: id, business_date, session (morning or afternoon), signed_by,
  signed_at, items_reviewed

  business_date is the bakery's local date the review belongs to; signed_at is
  the exact time in UTC.

Each card keeps the unit price and supplier at the time of the order, so
later price or supplier changes don't alter past orders or reports.
