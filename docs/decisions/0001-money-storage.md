# 0001: How to store money and quantities

Date: 2026-11-17
Status: Accepted

## Context
The requirements say money and quantities are stored exactly, with no rounding
errors. Quantities need 3 decimal places (for example 0.125 kg) and unit prices
need 4.

v1 uses SQLite, which has no exact decimal type: it stores `Decimal` fields as
floating-point numbers. A single value reads back correctly, but arithmetic done
by the database can be slightly off. In a test, adding 0.10 and 0.20 in the
database gave 0.30000000000000004. Over many orders, errors like this would make
totals and reports disagree with supplier invoices.

## Options considered
1. **Integer cents.** Store values as whole numbers of the smallest unit (for
   4-decimal prices, ten-thousandths). Exact in every database, but every value
   must be converted on the way in and out, which is easy to get wrong.
2. **PostgreSQL now.** Has an exact decimal type, but adds a database server to
   install and run during the first weeks, and we plan to move to Azure SQL
   anyway.
3. **`Decimal` with Python maths.** Keep `Decimal` fields and do every money
   calculation in Python, which is exact. Simple, but relies on a rule the
   database does not enforce.

## Decision
Option 3 for v1: `Decimal` fields, with all money calculations done in Python,
never in the database. When the app moves to Azure SQL, use exact `DECIMAL`
columns (3 decimal places for quantities, 4 for unit prices), so the database
can then calculate safely too.

## Consequences
- Totals and sums are calculated in Python. The API must not use database
  `SUM`, `AVG` or other arithmetic on money or quantity columns.
- Values with more decimal places than allowed are rejected by the API, not
  rounded.
- Moving to Azure SQL means changing column types. v1 data is made-up demo
  data, so it can be recreated rather than copied.

## Revisit when
- We move to Azure SQL (planned for week 5-6).
- We add reports that total many orders. These are faster in the database,
  which needs exact columns.
