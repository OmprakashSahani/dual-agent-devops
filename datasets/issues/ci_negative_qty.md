Title: Negative quantity accepted via API

Observed:
- POST /api/cart/items accepts {"qty": -2}, making totals negative

Expected:
- Server-side validation: qty >= 1 else HTTP 400 with error code CART_INVALID_QTY

Impact:
- Financial/data integrity risk; affects billing/refunds

Context:
- Service: cart-service (FastAPI)
- File of interest: services/cart/routers/items.py
- Tests: services/cart/tests/test_items.py

Requested:
- Add validation and tests; return CART_INVALID_QTY on invalid input
