# Kanban Lite: Requirements (v1)

## Goal
A restocking board for a small bakery (demo business: "Sunrise Bakery", fictional).
Kitchen staff flag ingredients that are running low. Each request moves through
review, approval, ordering and delivery on one shared board, so everyone can see
what is needed, what is approved and what is late.

## Users (roles)
- Kitchen Assistant: flags ingredients that are running low.
- Head Chef: reviews requests twice a day, confirms or adjusts quantities, and
  signs off each review, even when nothing needs ordering.
- Bakery Manager: sends chef-approved requests to the owner, places orders with
  suppliers, handles delays and watches for missed reviews.
- Owner: gives final approval, seeing the estimated total.

In v1 there is no sign-in, and anyone can do any action. Role rules come with
sign-in in a later version.

## Board columns
Running low -> Chef approved -> Owner approved -> Ordered -> Restocked,
plus a Delayed column for problems.

## User stories (v1)
1. As a kitchen assistant, I can create a restock card for an ingredient. It
   appears in Running low with that ingredient's regular restock quantity.
2. As a head chef, I can change the quantity on a card (for example, more than
   usual when I expect extra customers), and the estimated total updates
   (quantity x price per unit).
3. As anyone, I can drag a card from one column to another.
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

## Out of scope for v1 (planned later)
- Sign-in and role rules (only the owner can give owner approval, and so on)
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
- Payments: the app records only that an order was paid. It never stores
  card details.
- All demo data is made up.

## Data model (starting point)
- Supplier: id, name, phone, address
- Ingredient: id, name, unit (kg, litres, dozen, pieces), price_per_unit,
  regular_restock_qty, usual_delivery_days, supplier_id
- RestockStatus: id, name, position
- RestockCard: id, ingredient_id, quantity, status_id, expected_delivery_date,
  delay_reason, delay_next_action, created_at, position
- CardEvent: id, card_id, from_column, to_column, actor, timestamp, note
- ReviewSignOff: id, date, session (morning or afternoon), signed_by,
  signed_at, items_reviewed