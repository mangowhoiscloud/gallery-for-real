# CLARITY_LOG — Socratic Phase

## Round 1

---

### R1-01
```
Round: 1
Spec: member-crud-api.md
Category: CONTRADICTION
Severity: CRITICAL
Q: The endpoint table says POST /api/members/login "returns JWT or session" but the body says "Login returns HTTP Basic credentials acceptance (stateless)." CLAUDE.md mandates "HTTP Basic Auth, stateless session." What does the login endpoint actually do?
A: The body text and CLAUDE.md are authoritative. HTTP Basic Auth is stateless — the client sends credentials on every request. The login endpoint is a credential-validation endpoint: it accepts email+password in the POST body, validates them, and returns 200 with the member profile (minus password) if valid, 401 if invalid. The frontend uses this to verify credentials before storing them in sessionStorage. The "JWT or session" text in the endpoint table is a spec error.
Confidence: 0.95
Remaining_Ambiguity: Does the login endpoint accept credentials in the POST body (email/password JSON) or via the Authorization header?
Resolution: POST /api/members/login accepts { "email": "...", "password": "..." } in the request body (no auth header required). Returns 200 with member profile (id, email, name, role) on success, 401 on failure. No JWT, no session. The frontend stores the raw email:password as Base64 in sessionStorage for subsequent HTTP Basic calls.
---
```

### R1-02
```
Round: 1
Spec: member-crud-api.md
Category: CONTRADICTION
Severity: MAJOR
Q: DELETE /api/members/me says "Deactivate account" but the Member entity has no status or active field. Is this a soft delete (needing a new field) or hard delete (contradicting "deactivate")?
A: The word "deactivate" implies soft delete, but adding an unlisted field changes the entity schema. However, a status field would also require changes to the auth flow (block login for deactivated users). For an MVP with the given schema, a hard delete is simpler and avoids cascading complexity. The word "deactivate" in the spec likely means "the user initiates account removal" rather than prescribing a soft-delete mechanism.
Confidence: 0.80
Remaining_Ambiguity: What happens to the member's cart and pending orders on deletion?
Resolution: DELETE /api/members/me performs a hard delete. Before deletion: cancel all PENDING orders (restoring stock), delete the cart and its items. The endpoint returns 204 No Content. If the member has CONFIRMED/SHIPPED orders, reject the deletion with 409 Conflict ("Cannot delete account with active orders").
---
```

### R1-03
```
Round: 1
Spec: product-crud-api.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: DELETE /api/products/{id} says "Delete (soft/hard)" — which approach should be used?
A: OrderItem holds productId as a FK reference. Hard-deleting a product with existing order references would violate FK constraints or require CASCADE which destroys order history. Soft delete (setting status to INACTIVE) preserves referential integrity, aligns with the existing status enum (ACTIVE/INACTIVE), and is consistent with cart validation ("product must be ACTIVE").
Confidence: 0.95
Remaining_Ambiguity: Should GET /api/products/{id} return INACTIVE products? Should GET /api/products (list) include INACTIVE?
Resolution: DELETE /api/products/{id} performs a soft delete by setting status = INACTIVE. GET /api/products (list) and /api/products/search return only ACTIVE products by default. GET /api/products/{id} returns the product regardless of status (needed for order history display). Returns 404 if the product doesn't exist at all.
---
```

### R1-04
```
Round: 1
Spec: frontend-pages.md, CLAUDE.md
Category: CONTRADICTION
Severity: MAJOR
Q: Frontend spec says static files go in src/main/resources/static/ but CLAUDE.md says src/main/webapp/static/. Which path is correct for a Spring Framework 4.3.4 WAR project?
A: Spring Framework 4.3.4 (non-Boot) uses src/main/webapp/ as the standard web content root for WAR packaging. src/main/resources/static/ is a Spring Boot convention that requires explicit resource handler config in non-Boot projects. CLAUDE.md is the project-specific authority.
Confidence: 0.95
Remaining_Ambiguity: None — CLAUDE.md is authoritative.
Resolution: Static frontend files go in src/main/webapp/static/. Spring MVC resource handler must be configured to serve /static/** from this location. The frontend spec path is a spec error.
---
```

### R1-05
```
Round: 1
Spec: order-crud-api.md, cart-crud-api.md
Category: MISSING_ERROR_HANDLING
Severity: CRITICAL
Q: Order creation has 5 steps (validate cart, validate products, snapshot, decrease stock, clear cart). What transaction boundary applies? If stock decrease fails for one item, should all changes roll back?
A: This is a classic atomicity requirement. All 5 steps must execute within a single database transaction. If any step fails (e.g., insufficient stock for item 3 after items 1-2 succeed), the entire operation rolls back. Spring's @Transactional on the service method provides this guarantee with MyBatis + Spring TX.
Confidence: 0.95
Remaining_Ambiguity: None — this is a standard transactional pattern.
Resolution: Order creation must be wrapped in a single @Transactional method. On any failure (stock validation, product status check, etc.), the entire transaction rolls back — no partial stock decrements, no orphaned orders. Return 400 with a message identifying which product(s) failed validation.
---
```

### R1-06
```
Round: 1
Spec: cart-crud-api.md, order-crud-api.md, product-crud-api.md
Category: INTEGRATION_GAP
Severity: CRITICAL
Q: Both cart (on add) and order (on create) validate stock. What happens when stock changes between cart-add and order-creation? Cart holds stale quantity.
A: Cart is a "wishlist with intent" — it reflects what the user wants, not a reservation. Stock validation on cart-add is a courtesy check (fail-fast UX). The authoritative stock check happens at order creation time. If stock becomes insufficient after cart-add, the order creation should fail, not the cart display.
Confidence: 0.90
Remaining_Ambiguity: Should GET /api/cart show warnings for items that now exceed available stock?
Resolution: Cart validates stock on add/update as a courtesy (return 400 if insufficient at that moment). Order creation re-validates stock authoritatively (fails the whole transaction if insufficient). GET /api/cart does NOT filter or warn about stock changes — it returns the cart as-is with current product prices. The order creation error message identifies which items have insufficient stock.
---
```

### R1-07
```
Round: 1
Spec: order-crud-api.md, member-crud-api.md, frontend-pages.md
Category: INTEGRATION_GAP
Severity: CRITICAL
Q: Order requires shippingAddress (NOT NULL). The order creation flow (from cart) doesn't specify where shippingAddress comes from. The frontend "Proceed to Order" button has no address input. Member.address is nullable.
A: The order creation POST body must include shippingAddress. The frontend should either: (a) pre-fill from member.address and allow editing, or (b) prompt for address on the cart page before ordering. Since the frontend spec doesn't define an address form and member.address is nullable, the simplest approach is to accept shippingAddress in the POST /api/orders request body.
Confidence: 0.85
Remaining_Ambiguity: What does the frontend UI look like for entering the shipping address?
Resolution: POST /api/orders accepts { "shippingAddress": "..." } in the request body. If not provided, fall back to the member's address. If both are null/empty, return 400 ("Shipping address is required"). The frontend cart page shows a shipping address text input (pre-filled from member.address if available) above the "Proceed to Order" button.
---
```

### R1-08
```
Round: 1
Spec: product-crud-api.md, cart-crud-api.md, order-crud-api.md
Category: MISSING_PERFORMANCE_CONSTRAINT
Severity: MAJOR
Q: No spec addresses concurrent stock modifications. Two users ordering the last item simultaneously could oversell.
A: For an MVP, pessimistic locking (SELECT FOR UPDATE) on the product row during order creation is the simplest approach. Optimistic locking (version column) adds complexity. Database-level CHECK constraint (stockQuantity >= 0) provides a safety net.
Confidence: 0.85
Remaining_Ambiguity: None for MVP — pessimistic locking is sufficient.
Resolution: Use pessimistic locking (SELECT FOR UPDATE) when reading product stock during order creation. Add a database CHECK constraint (stock_quantity >= 0) as a safety net. No optimistic locking version column needed for MVP.
---
```

### R1-09
```
Round: 1
Spec: member-crud-api.md, cart-crud-api.md, order-crud-api.md
Category: INTEGRATION_GAP
Severity: MAJOR
Q: Cart, order, and member /me endpoints all need to resolve the current member from the HTTP Basic auth header. No spec defines this cross-cutting mechanism.
A: Spring Security with HTTP Basic auth populates SecurityContextHolder with the authenticated principal. The UserDetailsService loads the member by email. Controllers can inject the principal and look up the member ID. This is a standard Spring Security pattern.
Confidence: 0.95
Remaining_Ambiguity: None — standard Spring Security pattern.
Resolution: Implement a custom UserDetailsService that loads Member by email. Store member ID in a custom UserDetails implementation. Controllers access the authenticated member via SecurityContextHolder.getContext().getAuthentication().getPrincipal(). All /me, /api/cart, and /api/orders endpoints use this to resolve the current member's ID.
---
```

### R1-10
```
Round: 1
Spec: cart-crud-api.md, product-crud-api.md
Category: UNSTATED_ASSUMPTION
Severity: MAJOR
Q: Cart response includes "product name, price" — is this live data (JOIN to Product) or snapshotted at add-time? If live, cart prices change as products are updated.
A: The cart entity only stores productId and quantity — no price snapshot. The response spec says "includes product name, price" which implies fetching from the Product table at query time. This is intentional: the cart shows current prices (live), while the order snapshots prices at creation time. This is a common e-commerce pattern (cart = current prices, order = locked prices).
Confidence: 0.95
Remaining_Ambiguity: None — this is a deliberate design choice.
Resolution: Cart GET response fetches product name and price via JOIN to the Product table (live data). Cart does not snapshot prices. Order creation snapshots product name and price into OrderItem at the moment of order placement.
---
```

### R1-11
```
Round: 1
Spec: order-crud-api.md, cart-crud-api.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: Order creation flow says "Clear the cart" (step 5). Does this delete CartItem rows only or the Cart entity too?
A: The Cart entity is "one cart per member (auto-created on first add)." If we delete the Cart entity, it gets auto-recreated on next add. If we just delete CartItems, the empty Cart persists. Either works, but deleting only CartItems is simpler — the Cart row is lightweight and avoids unnecessary re-creation.
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: "Clear the cart" during order creation deletes all CartItem rows for the member's cart. The Cart entity row is preserved (empty cart). This matches the behavior of DELETE /api/cart (clear entire cart).
---
```

### R1-12
```
Round: 1
Spec: product-crud-api.md, cart-crud-api.md
Category: EDGE_CASE
Severity: MAJOR
Q: If a product becomes INACTIVE after being added to a cart, what happens? GET /api/cart would return items referencing an INACTIVE product. Can the user still see them? Order creation would fail validation.
A: The cart should return all items regardless of product status — it's the user's wishlist. Order creation validates ACTIVE status and rejects INACTIVE products. The frontend could optionally show a visual indicator but this is a UI choice.
Confidence: 0.85
Remaining_Ambiguity: Should the cart response include product status so the frontend can render warnings?
Resolution: GET /api/cart returns all items including those referencing INACTIVE products. The cart response includes product status in each item's data. Order creation rejects items with INACTIVE products (return 400 listing affected items). The frontend can use the status field to show "unavailable" styling but this is optional for MVP.
---
```

### R1-13
```
Round: 1
Spec: cart-crud-api.md, product-crud-api.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: PUT /api/cart/items/{itemId} updates quantity. Does stock validation apply? Is the validation against total stock or additional stock needed?
A: The spec says "validate requested quantity <= available stock" for adding items. The update should follow the same principle: the new quantity must not exceed available stock. The validation is against total available stock (not incremental), since the cart doesn't reserve stock.
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: PUT /api/cart/items/{itemId} with { "quantity": N } validates that N <= product.stockQuantity (total stock, not incremental). The request body contains the absolute new quantity, not a delta. Returns 400 if the product is INACTIVE or N exceeds available stock.
---
```

### R1-14
```
Round: 1
Spec: frontend-pages.md, member-crud-api.md
Category: MISSING_ERROR_HANDLING
Severity: MAJOR
Q: The product list (public) shows "Add to Cart" buttons. Cart endpoints require USER auth. What happens when an unauthenticated user clicks "Add to Cart"?
A: The frontend must check auth state before cart operations. If not authenticated (no credentials in sessionStorage), redirect to the login page. This is standard e-commerce UX.
Confidence: 0.95
Remaining_Ambiguity: None.
Resolution: Frontend checks sessionStorage for stored credentials before any cart/order API call. If no credentials, redirect to login.html with a return URL parameter. After login, redirect back to the original page. The "Add to Cart" button is always visible but triggers the auth check on click.
---
```

### R1-15
```
Round: 1
Spec: member-crud-api.md, frontend-pages.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: After successful registration (POST /api/members), should the user be auto-logged in? What does the registration response contain?
A: The registration endpoint creates the user. Since the frontend already has the email+password from the registration form, it can store them in sessionStorage immediately (auto-login without a separate API call). The response should return the created member profile (id, email, name, role) with 201 status.
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: POST /api/members returns 201 with the created member profile (id, email, name, role — no password). The frontend stores the email:password from the registration form as Base64 in sessionStorage (auto-login). No separate login API call needed after registration.
---
```

### R1-16
```
Round: 1
Spec: order-crud-api.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: PUT /api/orders/{id}/status (ADMIN) — is there validation of status transitions? Can an admin skip states (e.g., PENDING → SHIPPED)?
A: The status flow diagram in the spec shows a linear progression: PENDING → CONFIRMED → SHIPPED → DELIVERED, with CANCELLED only from PENDING. This implies only forward-adjacent transitions are valid. Skipping states would break the flow semantics.
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: Status transitions are strictly validated: PENDING→CONFIRMED, CONFIRMED→SHIPPED, SHIPPED→DELIVERED. No skipping. CANCELLED only from PENDING. Invalid transitions return 400 ("Cannot transition from X to Y"). The request body is { "status": "CONFIRMED" }.
---
```

### R1-17
```
Round: 1
Spec: order-crud-api.md, product-crud-api.md
Category: EDGE_CASE
Severity: MAJOR
Q: If a product is soft-deleted (INACTIVE) or hard-deleted between order creation and cancellation, what happens when trying to restore stock on cancellation?
A: With soft-delete (our resolution from R1-03), the product row always exists. Stock restoration should work regardless of product status — it's a data correction, not a business operation. The product might be INACTIVE but its stock count should still be accurate for inventory tracking.
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: Order cancellation restores stock to the product regardless of the product's current status (ACTIVE or INACTIVE). The product row is guaranteed to exist (soft-delete only). Stock restoration is a data correction operation within the cancellation transaction.
---
```

### R1-18
```
Round: 1
Spec: product-crud-api.md, frontend-pages.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MINOR
Q: Product spec defines both GET /api/products (list with search params) and GET /api/products/search (search). Are these redundant? Which does the frontend use?
A: The pagination section defines keyword, category, minPrice, maxPrice params on the list endpoint. The /search endpoint is listed separately but with identical semantics. This is redundant. The simplest approach is to use GET /api/products with query params for everything and implement /search as an alias or remove it.
Confidence: 0.85
Remaining_Ambiguity: None.
Resolution: GET /api/products handles all listing and searching via query params (keyword, category, minPrice, maxPrice, sortBy, sortDir, page, size). GET /api/products/search is implemented as an alias that delegates to the same service method. The frontend uses GET /api/products with query params.
---
```

### R1-19
```
Round: 1
Spec: order-crud-api.md, member-crud-api.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MINOR
Q: GET /api/orders (list my orders) and GET /api/members (list all members, ADMIN) — are these paginated? What format?
A: The product spec defines the pagination convention (page, size, totalPages, totalElements, currentPage). For consistency, all list endpoints should follow the same pagination convention.
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: All list endpoints (products, orders, members) use the same pagination convention: query params page (0-based), size (default 10, max 100). Response wrapper: { "content": [...], "totalPages": N, "totalElements": N, "currentPage": N, "size": N }. GET /api/orders (user) is paginated, GET /api/admin/orders (admin) is paginated, GET /api/members (admin) is paginated.
---
```

### R1-20
```
Round: 1
Spec: order-crud-api.md, frontend-pages.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MINOR
Q: Frontend orders page says "Click to view order detail" but there's no order detail page listed. Where is order detail shown?
A: The spec lists 5 pages. Order detail can be shown inline on orders.html (expand/modal) without a separate page. This avoids adding an unlisted page.
Confidence: 0.85
Remaining_Ambiguity: None.
Resolution: Order detail is displayed inline on orders.html. Clicking an order expands it to show OrderItem details (product name, quantity, unit price, subtotal) below the order row. No separate order-detail.html page needed.
---
```

### R1-21
```
Round: 1
Spec: member-crud-api.md, frontend-pages.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MINOR
Q: Member spec defines GET/PUT/DELETE /api/members/me but there's no profile page in the frontend spec. Are these endpoints unused?
A: The endpoints exist in the API spec and should be implemented. The frontend MVP can add a simple profile section (e.g., header dropdown or a nav link). Not blocking for MVP — the API is the deliverable, frontend is "sample pages."
Confidence: 0.85
Remaining_Ambiguity: None.
Resolution: The /api/members/me endpoints are implemented as specified. For the frontend MVP, add a minimal "My Account" link in the nav that shows/edits profile info inline or as a simple section on any existing page. Not a separate page — keep the 5-page structure.
---
```

### R1-22
```
Round: 1
Spec: member-crud-api.md
Category: INTEGRATION_GAP
Severity: MINOR
Q: There's no endpoint to create an ADMIN user or promote a USER to ADMIN. How does the first admin get created?
A: This is common in MVPs. Seed the database with an initial admin account. No admin-creation endpoint needed for MVP.
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: Seed the database with a default admin account (e.g., admin@example.com / admin1234). No role-management endpoints. The role field is set at registration (always USER) or via direct DB manipulation. SQL seed script should create the admin.
---
```

### R1-23
```
Round: 1
Spec: frontend-pages.md
Category: INTEGRATION_GAP
Severity: MINOR
Q: The frontend "Category filter sidebar" on the home page needs category values. There's no dedicated category endpoint. Where do categories come from?
A: Products have a category field (String, 1-50 chars). Categories can be derived from existing product data with a SELECT DISTINCT query. Adding a dedicated endpoint is cleaner than hardcoding.
Confidence: 0.85
Remaining_Ambiguity: None.
Resolution: Add GET /api/products/categories endpoint (public, no auth) that returns a list of distinct category strings from ACTIVE products. The frontend uses this to populate the filter sidebar. Alternatively, the product list response could include facet data, but a separate endpoint is simpler.
---
```

## Ambiguity Score

```
AMBIGUITY_SCORE: 0.04
Rounds_Completed: 1
Ambiguities_Found: 23
Ambiguities_Resolved: 22
Ambiguities_Remaining: 1
```

The one remaining ambiguity (R1-02: cascading behavior for member deletion with non-PENDING orders) has a resolution but at slightly lower confidence (0.80). All other items are resolved at >= 0.85 confidence.

```
CONVERGENCE_DATA:
  round: 1
  score: 0.04
  prev_score: 1.0
  delta: -0.96
  category_distribution:
    CRITICAL: 0
    MAJOR: 0
    MINOR: 0
  stagnation_count: 0
```

## Summary of Architectural Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | HTTP Basic Auth, no JWT | CLAUDE.md mandates stateless HTTP Basic. Login endpoint validates credentials only. |
| 2 | Hard-delete members | No status field in entity. Cancel PENDING orders, delete cart, reject if active orders exist. |
| 3 | Soft-delete products | Set INACTIVE. Preserves FK integrity with OrderItem. |
| 4 | Static files in src/main/webapp/static/ | CLAUDE.md is authoritative over frontend spec. |
| 5 | Order creation is fully transactional | Single @Transactional wrapping all 5 steps. Rollback on any failure. |
| 6 | Cart validates stock as courtesy; order validates authoritatively | Cart doesn't reserve stock. Order creation is the commit point. |
| 7 | POST /api/orders accepts { "shippingAddress": "..." } | Falls back to member.address if omitted. 400 if both null. |
| 8 | Pessimistic locking for stock | SELECT FOR UPDATE on product during order creation. |
| 9 | Custom UserDetailsService for member auth resolution | Standard Spring Security pattern. Stores member ID in principal. |
| 10 | Cart uses live product data; order snapshots at creation | Standard e-commerce pattern. |
| 11 | Clear cart = delete CartItems, keep Cart entity | Avoids re-creation overhead. |
| 12 | Strict status transitions for orders | Only forward-adjacent transitions. No skipping. |
| 13 | Same pagination convention for all list endpoints | page, size, totalPages, totalElements, currentPage. |
| 14 | GET /api/products/search aliases GET /api/products | Avoid redundancy. Same service method. |
| 15 | Seed DB with default admin account | No admin-creation endpoint for MVP. |
| 16 | GET /api/products/categories for filter sidebar | Distinct categories from ACTIVE products. |

PHASE_0_COMPLETE
FINAL_AMBIGUITY_SCORE: 0.04
TOTAL_ROUNDS: 1
EXIT_REASON: THRESHOLD
