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
- Owner: gives final approval, seeing the estimated total.

In v1 there is no sign-in, and anyone can do any action. Role rules come with
sign-in in a later version.

## Board columns
Running low -> Manager review -> Owner review -> Ordered -> Restocked,
plus Delayed.

Each column shows whose turn it is. Moving a card forward is that person's
approval, and the card history records who moved it and when.

## Card movement rules
- A card moves one step at a time, forward or back.
- Moving a card back requires a note explaining why. The person in the
  earlier step reads the note, acts on it and moves the card forward again.
- There is no reject action. An owner who doesn't approve a card moves it
  back to Manager review with a note.
- A card can move to Delayed only from Ordered, with a reason and a next
  action, and returns to Ordered when the problem is solved.
- The unit price can be edited only in Manager review. It locks when the
  card moves to Owner review, and unlocks if it moves back.
- Only the bakery manager can delete a card (for example, one created by
  mistake). Delete needs a reason. A deleted card is hidden from the board
  but kept in the history. Role rules are enforced once sign-in is added.

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
   orders with their expected delivery date.
9. As anyone, when I move a card back one step, I must enter a note
   explaining why.
10. As a bakery manager, I can edit a card's unit price until I move it to
    Owner review.
11. As a bakery manager, I can delete a card created by mistake, with a
    reason. It is hidden from the board but kept in the history.

## Out of scope for v1 (planned later)
- Sign-in and role rules (only the owner can move a card on from Owner review, and so on)
- One-time purchase requests (a bulb, a chair, a temporary cleaner)
- Notifications for missed reviews (v1 shows an alert on the board only)
- Opening days and public holidays in admin settings (v1 assumes open every day)
- Reports over time (week, month, 3, 6 and 12 months) and usage metrics
- Mobile layout; more than one bakery

## Non-functional requirements
- Works in Chrome and Edge.
- The board loads in under 2 seconds with 200 cards.
- All data changes go through the API.
- Times are stored in UTC and shown in the bakery's local time.
- Money and quantities are stored exactly, with no rounding errors.
- Payments: the app records only that an order was paid. It never stores
  card details.
- All demo data is made up.

## Data model (starting point)
- Supplier: id, name, phone, address
- Ingredient: id, name, unit (kg, litres, dozen, pieces), price_per_unit,
  regular_restock_qty, usual_delivery_days, supplier_id
- RestockStatus: id, name, position
- RestockCard: id, ingredient_id, status_id, supplier_id, quantity,
  unit_price, expected_delivery_date, delay_reason, delay_next_action,
  position, created_at, deleted_at, deleted_by, deleted_reason
- CardEvent: id, card_id, from_column, to_column, actor, timestamp, note
- ReviewSignOff: id, date, session (morning or afternoon), signed_by,
  signed_at, items_reviewed

Each card keeps the unit price and supplier at the time of the order, so
later price or supplier changes don't alter past orders or reports.
