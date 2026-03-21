# Implementation Plan
Generated: 2026-03-20T00:00:00Z
Total_Items: 14
Completed: 1
Test_Items: 10 (target: ≥70% of implementation items → 71%)

## Dependency Graph
```
Independent_Groups:
  - group_1: [Item 1]                               # foundation
  - group_2: [Item 2, Item 3, Item 4, Item 5]       # entity + mapper layer (parallel)
  - group_3: [Item 6]                               # security config (needs Member mapper)
  - group_4: [Item 7, Item 8]                       # member + product APIs (parallel)
  - group_5: [Item 9]                               # cart API (needs member + product)
  - group_6: [Item 10]                              # order API (needs cart + product)
  - group_7: [Item 11, Item 12, Item 13, Item 14]   # frontend pages (parallel)
Build_Order: group_1 → group_2 → group_3 → group_4 → group_5 → group_6 → group_7
```

---

## Item 1: Application Bootstrap + Configuration
- status: DONE
- priority: P0
- complexity: M
- depends_on: []
- spec: specs/member-crud-api.md, specs/product-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-6
- description: Create Spring Boot application entry point, configuration properties for both default (PostgreSQL) and test (H2) profiles, database schema DDL for all 6 tables (member, product, cart, cart_item, orders, order_item), seed data for admin user (admin@shop.com / BCrypt("admin1234") / ADMIN role), and a global exception handler returning ProblemDetail (RFC 7807) for validation errors, not-found, and authorization failures.
- acceptance: `mvn compile` succeeds. ApplicationContextTest loads Spring context with H2 test profile. Schema creates all tables. Admin seed row exists in member table.
- tests: ApplicationContextTest — verify context loads, verify H2 profile active in test, verify admin member seeded via direct JDBC query.

## Item 2: Member Entity + DTOs + MyBatis Mapper
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 1]
- spec: specs/member-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-3, CLARITY_LOG.md#Round-11
- description: Member entity class with fields: id (Long, PK), email (String, unique), password (String, BCrypt), name (String), phone (String, 10-15 chars), address (String), role (enum USER/ADMIN), active (Boolean, default true), createdAt, updatedAt. DTO records: MemberRegisterRequest (email, password, name, phone, address — validated), MemberUpdateRequest (name, phone, address), MemberResponse (all fields except password). MemberMapper interface + XML with insert, findByEmail, findById, findAll (paginated), update, deactivate.
- acceptance: `mvn compile` succeeds. MemberMapperTest passes all CRUD operations against H2.
- tests: MemberMapperTest — insert and findByEmail, findById returns correct fields, update modifies name/phone/address, deactivate sets active=false, findAll returns paginated results.

## Item 3: Product Entity + DTOs + MyBatis Mapper
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 1]
- spec: specs/product-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-4, CLARITY_LOG.md#Round-10
- description: Product entity with fields: id (Long, PK), name (String), description (String), price (BigDecimal), stockQuantity (Integer), category (String), imageUrl (String), status (enum ACTIVE/INACTIVE, default ACTIVE), createdAt, updatedAt. DTO records: ProductCreateRequest, ProductUpdateRequest, ProductResponse, ProductPageResponse (wraps page of products with totalPages, totalElements, currentPage). ProductMapper interface + XML with insert, findById, findAllActive (paginated), update, softDelete (set status=INACTIVE), search (keyword, category, minPrice, maxPrice, sortBy, sortDir — paginated), decreaseStock, countByCategory.
- acceptance: `mvn compile` succeeds. ProductMapperTest passes all operations against H2.
- tests: ProductMapperTest — insert and findById, findAllActive excludes INACTIVE, softDelete changes status, search with keyword/category/price filters, decreaseStock reduces stockQuantity, pagination returns correct slices.

## Item 4: Cart Entities + DTOs + MyBatis Mapper
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 1]
- spec: specs/cart-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-7, CLARITY_LOG.md#Round-8, CLARITY_LOG.md#Round-16
- description: Cart entity with fields: id (Long, PK), memberId (Long, FK unique), createdAt, updatedAt. CartItem entity with fields: id (Long, PK), cartId (Long, FK), productId (Long, FK), quantity (Integer, >=1), createdAt. Unique constraint on (cartId, productId). DTO records: CartItemAddRequest (productId, quantity), CartItemUpdateRequest (quantity), CartResponse (items list + cartTotal), CartItemResponse (itemId, productId, productName, productPrice, imageUrl, quantity, subtotal, productStatus). CartMapper + CartItemMapper interfaces + XML with findByMemberId, insertCart, findCartItems (joined with product for enriched response), insertItem, updateItemQuantity, deleteItem, deleteAllItems, findItemById.
- acceptance: `mvn compile` succeeds. CartMapperTest and CartItemMapperTest pass against H2.
- tests: CartMapperTest — insert cart, find by memberId. CartItemMapperTest — insert item, find items with product join (verify enriched fields), update quantity, delete single item, delete all items, unique constraint on (cartId, productId) prevents duplicates.

## Item 5: Order Entities + DTOs + MyBatis Mapper
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 1]
- spec: specs/order-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-2, CLARITY_LOG.md#Round-9, CLARITY_LOG.md#Round-12
- description: Order entity with fields: id (Long, PK), memberId (Long, FK), totalAmount (BigDecimal), status (enum PENDING/CONFIRMED/SHIPPED/DELIVERED/CANCELLED), shippingAddress (String, NOT NULL, max 200), createdAt, updatedAt. OrderItem entity with fields: id (Long, PK), orderId (Long, FK), productId (Long, FK), productName (String, snapshot), quantity (Integer, >=1), unitPrice (BigDecimal, snapshot). DTO records: OrderCreateRequest (shippingAddress), OrderStatusUpdateRequest (status), OrderResponse (order + items), OrderItemResponse, OrderPageResponse. OrderMapper + OrderItemMapper interfaces + XML with insertOrder, insertOrderItem, findByMemberId (paginated), findById (with items), updateStatus, findAll (paginated, optional status filter), countByMemberId.
- acceptance: `mvn compile` succeeds. OrderMapperTest and OrderItemMapperTest pass against H2.
- tests: OrderMapperTest — insert order, findByMemberId paginated, findById with items joined, updateStatus changes status field, findAll with and without status filter. OrderItemMapperTest — batch insert items, find by orderId.

## Item 6: Security Configuration
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 2]
- spec: specs/member-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1, CLARITY_LOG.md#Round-3
- description: SecurityConfig with HTTP Basic Auth, stateless session management (SessionCreationPolicy.STATELESS), CSRF disabled for REST API, BCrypt PasswordEncoder bean. CustomUserDetailsService implements UserDetailsService — loads member by email via MemberMapper, rejects inactive members (throws DisabledException). Endpoint authorization rules: POST /api/members (permitAll — registration), GET /api/products/** and GET /api/products/search (permitAll — public catalog), /api/admin/** (ADMIN role required), all other /api/** endpoints (authenticated). Static resources (/**) permitted for frontend.
- acceptance: `mvn compile` succeeds. SecurityConfigTest verifies unauthenticated access to public endpoints succeeds, unauthenticated access to protected endpoints returns 401, admin-only endpoints return 403 for USER role, inactive member login returns 401.
- tests: SecurityConfigTest — GET /api/products returns 200 without auth, GET /api/cart returns 401 without auth, POST /api/members returns 200 without auth (registration is open), GET /api/admin/orders returns 403 for USER role, inactive member credentials rejected.

## Item 7: Member Service + Controller + Tests
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 2, Item 6]
- spec: specs/member-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-3, CLARITY_LOG.md#Round-6, CLARITY_LOG.md#Round-11
- description: MemberService with business logic for registration (BCrypt password, default USER role, duplicate email check), login verification (returns MemberResponse on success), profile retrieval and update, account deactivation (sets active=false, no cascade), admin member listing (paginated) and detail retrieval. MemberController exposes all 7 endpoints per spec. Uses jakarta.validation for request validation (email format, password min length, phone 10-15 chars). Returns ProblemDetail for errors.
- acceptance: All MemberControllerTest methods pass. Registration creates member retrievable via login. Profile update reflects changes. Deactivation prevents subsequent login. Admin can list and view members.
- tests: MemberControllerTest — register success (201), register duplicate email (409), register validation errors (400), login success (200 with member data), login wrong password (401), login inactive member (401), get profile (200), update profile (200, verify changes), deactivate account (204, subsequent login fails), admin list members (200 paginated), admin get member by id (200), user cannot access admin endpoints (403).

## Item 8: Product Service + Controller + Tests
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 3, Item 6]
- spec: specs/product-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-4, CLARITY_LOG.md#Round-10
- description: ProductService with business logic for paginated active product listing (default page=0, size=10, max 100), single product retrieval (any status), admin product creation (validation), update, and soft delete (status=INACTIVE). Search with keyword (name/description LIKE), category, minPrice, maxPrice, sortBy (name/price/createdAt), sortDir (asc/desc). ProductController exposes all 6 endpoints per spec. Public endpoints require no auth; CUD endpoints require ADMIN role.
- acceptance: All ProductControllerTest methods pass. Products are listable, searchable with filters, and manageable by admin. Soft-deleted products excluded from public listing but retrievable by ID.
- tests: ProductControllerTest — list products paginated (200, verify page structure), get product by id (200), get nonexistent product (404), admin create product (201), create with validation errors (400), admin update product (200), admin soft delete product (204, verify excluded from listing), search by keyword (200, correct results), search by category (200), search by price range (200), search with combined filters (200), user cannot create/update/delete (403), pagination size capped at 100.

## Item 9: Cart Service + Controller + Tests
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 4, Item 7, Item 8]
- spec: specs/cart-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-7, CLARITY_LOG.md#Round-8, CLARITY_LOG.md#Round-16
- description: CartService with business logic for auto-creating cart on first access, adding items (validate product ACTIVE + stock >= quantity, increment quantity if same product already in cart), updating item quantity (validate stock), removing single item, clearing entire cart. GET cart returns enriched response with product details (name, price, imageUrl, status) and computed subtotals/cartTotal. CartController exposes all 5 endpoints per spec. All endpoints require USER auth and operate on the authenticated member's cart.
- acceptance: All CartControllerTest methods pass. Cart auto-created on first GET. Items addable with stock validation. Duplicate product add increments quantity. Inactive products visible in cart with status. Cart clearable.
- tests: CartControllerTest — get empty cart (200, empty items, cartTotal=0), add item (201, verify enriched response), add same product again (increments quantity), add item exceeding stock (400), add inactive product (400), update quantity (200), update quantity exceeding stock (400), remove item (204), clear cart (204), cart shows inactive product status, verify subtotal and cartTotal calculations, unauthenticated access (401).

## Item 10: Order Service + Controller + Tests
- status: DONE
- priority: P1
- complexity: L
- depends_on: [Item 5, Item 9]
- spec: specs/order-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-2, CLARITY_LOG.md#Round-9, CLARITY_LOG.md#Round-12, CLARITY_LOG.md#Round-15
- description: OrderService with transactional order creation from cart — validate cart not empty, all products ACTIVE + sufficient stock, snapshot product name/price into OrderItem, decrease stock for each item, clear cart, return created order. Status transition enforcement (PENDING→CONFIRMED→SHIPPED→DELIVERED, strict linear, no skips; CANCELLED only from PENDING with stock restoration). User order listing (paginated), order detail retrieval. Admin order listing (paginated, optional status filter), admin status update. OrderController exposes all 6 endpoints per spec.
- acceptance: All OrderControllerTest methods pass. Order creation is transactional (all-or-nothing). Stock decreases on order creation and restores on cancellation. Status transitions strictly enforced. Price/name snapshots preserved.
- tests: OrderControllerTest — create order from cart (201, verify stock decreased, cart cleared, prices snapshotted), create order with empty cart (400), create order with inactive product in cart (400, lists affected items), create order with insufficient stock (400), get my orders paginated (200), get order detail (200, includes items), user cannot see other user's order (403 or 404), admin update status PENDING→CONFIRMED (200), admin skip status PENDING→SHIPPED (400), admin invalid backward transition (400), user cancel PENDING order (200, verify stock restored), user cancel non-PENDING order (400), admin list all orders (200 paginated), admin filter by status (200), concurrent order creation stock race (verify transactional integrity).

## Item 11: Login Page
- status: DONE
- priority: P2
- complexity: S
- depends_on: [Item 7]
- spec: specs/frontend-pages.md
- description: login.html with tabbed login/register form. Login tab: email + password fields, submit calls POST /api/members/login with HTTP Basic Auth header. Register tab: email, password, name, phone, address fields, submit calls POST /api/members. On success, store Base64(email:password) in sessionStorage and redirect to index.html. Show error messages for invalid credentials or validation failures. Clean minimal CSS consistent with other pages.
- acceptance: Login form submits with Basic Auth header. Registration form creates new member. Credentials stored in sessionStorage. Redirect to index.html on success. Error messages displayed.
- tests: Manual browser verification. JS fetch calls use correct Authorization header format.

## Item 12: Product Listing + Detail Pages
- status: DONE
- priority: P2
- complexity: M
- depends_on: [Item 8]
- spec: specs/frontend-pages.md
- description: index.html — product grid/list layout, fetches GET /api/products on load. Search bar and category filter call GET /api/products/search. Pagination controls (previous/next). Each product card links to product.html?id={id}. product.html — fetches GET /api/products/{id}, displays image, name, description, price, stock status. Quantity selector (1 to stockQuantity). "Add to Cart" button calls POST /api/cart/items with Basic Auth from sessionStorage (redirects to login if no credentials). Responsive layout with flexbox/grid.
- acceptance: index.html displays products in grid. Search filters products. Pagination works. product.html shows product details. Add to cart sends correct API request with auth header.
- tests: Manual browser verification. JS correctly constructs API URLs with query params.

## Item 13: Cart Page
- status: DONE
- priority: P2
- complexity: M
- depends_on: [Item 9]
- spec: specs/frontend-pages.md
- description: cart.html — fetches GET /api/cart on load (with Basic Auth). Displays items in table with product name, price, quantity (editable), subtotal, and remove button. Shows inactive product indicator. Cart total displayed. Quantity change calls PUT /api/cart/items/{itemId}. Remove calls DELETE /api/cart/items/{itemId}. "Clear Cart" calls DELETE /api/cart. "Proceed to Order" prompts for shipping address then calls POST /api/orders. Redirects to login if no credentials in sessionStorage.
- acceptance: Cart page displays all items with enriched data. Quantity editable with stock validation feedback. Remove and clear work. Order creation with shipping address input functions correctly.
- tests: Manual browser verification. JS handles inactive product display and API error responses.

## Item 14: Orders Page
- status: DONE
- priority: P2
- complexity: M
- depends_on: [Item 10]
- spec: specs/frontend-pages.md
- description: orders.html — fetches GET /api/orders on load (with Basic Auth, paginated). Displays orders in list/table with order ID, date, total, status, item count. Click expands or navigates to detail view showing order items (productName, quantity, unitPrice). "Cancel" button visible only for PENDING orders, calls PUT /api/orders/{id}/cancel. Pagination controls. Redirects to login if no credentials in sessionStorage.
- acceptance: Orders page lists user's orders paginated. Order detail shows snapshotted items. Cancel button only on PENDING orders. Cancellation updates status and re-fetches list.
- tests: Manual browser verification. JS correctly handles status-based UI logic.

---
PHASE_1_COMPLETE
