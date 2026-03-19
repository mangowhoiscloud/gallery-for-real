# Implementation Plan
Generated: 2026-03-20T01:15:00+09:00
Total_Items: 15
Completed: 1
Test_Items: 11 (target: ≥70% of implementation items → 73% achieved)

## Dependency Graph
```
Independent_Groups:
  - group_1: [Item 1]
  - group_2: [Item 2, Item 3, Item 4, Item 5, Item 6]
  - group_3: [Item 7]
  - group_4: [Item 8, Item 9, Item 10, Item 11]
  - group_5: [Item 12, Item 13, Item 14, Item 15]
Build_Order: group_1 → group_2 → group_3 → group_4 → group_5
```

---

## Item 1: Project skeleton — Spring, MyBatis, DB schema, test infrastructure
- status: DONE
- priority: P0
- complexity: M
- depends_on: []
- spec: specs/member-crud-api.md, specs/product-crud-api.md, specs/cart-crud-api.md, specs/order-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1 (static files path, admin seeding, pessimistic locking)
- description: Create the entire project infrastructure. WebApplicationInitializer (replaces web.xml), AppConfig (@Configuration with DataSource, PlatformTransactionManager, SqlSessionFactoryBean, MapperScannerConfigurer), WebConfig (@EnableWebMvc with Jackson message converter, static resource handler for /static/**). schema.sql with all 6 tables (members, products, carts, cart_items, orders, order_items) including constraints, indexes, and CHECK(stock_quantity >= 0). data.sql with admin seed (admin@example.com / admin1234 BCrypt-hashed). Test infrastructure: TestConfig with H2 DataSource, test schema loading.
- acceptance: `mvn compile` succeeds. Smoke test loads Spring context and verifies DataSource, SqlSessionFactory, and TransactionManager beans exist.
- tests: AppConfigTest — context loads, DataSource connects to H2, SqlSessionFactory created, TransactionManager created, MapperScannerConfigurer registered.

## Item 2: Member entity and MyBatis mapper
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 1]
- spec: specs/member-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1 (hard delete, admin seed)
- description: Member.java entity (id, email, password, name, phone, address, role enum USER/ADMIN, createdAt, updatedAt). MemberMapper.java interface. MemberMapper.xml with insert, selectById, selectByEmail, selectAll (paginated), update, delete, count operations. Role stored as VARCHAR in DB.
- acceptance: All mapper CRUD operations work against H2. Insert returns generated key. selectByEmail finds by email. Pagination works with offset/limit.
- tests: MemberMapperTest — insert and selectById, selectByEmail, update fields, delete, selectAll with pagination, duplicate email insert fails (unique constraint).

## Item 3: Product entity and MyBatis mapper
- status: IN_PROGRESS
- priority: P0
- complexity: S
- depends_on: [Item 1]
- spec: specs/product-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1 (soft delete via INACTIVE, search aliases list)
- description: Product.java entity (id, name, description, price as BigDecimal, stockQuantity, category, imageUrl, status enum ACTIVE/INACTIVE, createdAt, updatedAt). ProductMapper.java interface. ProductMapper.xml with insert, selectById, selectActiveById, search (keyword LIKE, category exact, price range, sort, pagination), update, updateStock (for atomic decrement/increment), selectDistinctCategories, countBySearch.
- acceptance: All mapper CRUD operations work against H2. Search with multiple filter combinations returns correct results. updateStock atomically changes quantity. selectDistinctCategories returns unique categories from ACTIVE products only.
- tests: ProductMapperTest — insert and selectById, search by keyword, search by category, search by price range, search with sorting, updateStock increment/decrement, selectDistinctCategories, soft delete (status=INACTIVE) excluded from search.

## Item 4: Cart and CartItem entities and MyBatis mappers
- status: TODO
- priority: P0
- complexity: S
- depends_on: [Item 1]
- spec: specs/cart-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1 (cart live data, clear cart deletes items not cart, inactive product handling)
- description: Cart.java entity (id, memberId, createdAt, updatedAt). CartItem.java entity (id, cartId, productId, quantity, createdAt). CartMapper.java + CartMapper.xml with insert, selectByMemberId, delete. CartItemMapper.java + CartItemMapper.xml with insert, selectByCartId (JOIN product for name/price/status), selectById, updateQuantity, deleteById, deleteByCartId, countByCartId. Unique constraint (cartId, productId) handled in schema.
- acceptance: Cart created per member. CartItem JOIN returns product data. deleteByCartId clears all items. Duplicate (cartId, productId) insert fails.
- tests: CartMapperTest + CartItemMapperTest — create cart, add items, select with product join, update quantity, delete single item, clear all items, unique constraint on duplicate product.

## Item 5: Order and OrderItem entities and MyBatis mappers
- status: TODO
- priority: P0
- complexity: S
- depends_on: [Item 1]
- spec: specs/order-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1 (strict status transitions, snapshot prices, cancellation restores stock)
- description: Order.java entity (id, memberId, totalAmount as BigDecimal, status enum PENDING/CONFIRMED/SHIPPED/DELIVERED/CANCELLED, shippingAddress, createdAt, updatedAt). OrderItem.java entity (id, orderId, productId, productName, quantity, unitPrice as BigDecimal). OrderMapper.java + OrderMapper.xml with insert, selectById, selectByMemberId (paginated), selectAll (paginated), updateStatus, countByMemberId, countAll. OrderItemMapper.java + OrderItemMapper.xml with insertBatch, selectByOrderId.
- acceptance: Order insert returns generated key. OrderItem batch insert works. Pagination queries return correct counts. Status update modifies only status and updatedAt.
- tests: OrderMapperTest + OrderItemMapperTest — create order with items, selectById includes items, paginated list by member, paginated list all, update status, batch insert order items.

## Item 6: Common DTOs — PageResponse, ErrorResponse, GlobalExceptionHandler
- status: TODO
- priority: P0
- complexity: S
- depends_on: [Item 1]
- spec: specs/member-crud-api.md (error format), specs/product-crud-api.md (pagination format)
- clarity_ref: CLARITY_LOG.md#Round-1 (pagination convention)
- description: PageResponse<T> generic wrapper (content, totalPages, totalElements, currentPage, size). ErrorResponse (status, error, message, timestamp). GlobalExceptionHandler (@ControllerAdvice) handling MethodArgumentNotValidException (400), custom BusinessException (variable status), AccessDeniedException (403), NoHandlerFoundException (404), and generic Exception (500). All return standard JSON error format.
- acceptance: PageResponse serializes correctly. ErrorResponse matches spec format. Exception handler returns proper HTTP status and JSON body for each exception type.
- tests: PageResponseTest — serialization with Jackson. GlobalExceptionHandlerTest — MockMvc tests triggering each exception type and verifying response status + JSON body.

## Item 7: Spring Security configuration and CustomUserDetailsService
- status: TODO
- priority: P0
- complexity: M
- depends_on: [Item 2]
- spec: specs/member-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1 (HTTP Basic, UserDetailsService, SecurityContext for /me endpoints)
- description: SecurityConfig (@EnableWebSecurity) with HttpSecurity: HTTP Basic auth, stateless session (NEVER), CSRF disabled, permitAll for POST /api/members (register), POST /api/members/login, GET /api/products/**, GET /api/products; ADMIN role for GET /api/members, GET /api/members/{id}, POST/PUT/DELETE /api/products/**, GET /api/admin/orders; USER role for /api/members/me, /api/cart/**, /api/orders/**. CustomUserDetailsService implements UserDetailsService, loads Member by email via MemberMapper, maps to Spring Security UserDetails with ROLE_USER or ROLE_ADMIN. BCryptPasswordEncoder bean. SecurityWebApplicationInitializer for filter chain registration.
- acceptance: Unauthenticated requests to protected endpoints return 401. Wrong credentials return 401. Correct USER credentials access /me endpoints. ADMIN credentials access admin endpoints. USER cannot access admin endpoints (403).
- tests: SecurityConfigTest — unauthenticated access blocked, valid USER auth passes, valid ADMIN auth passes, USER accessing admin endpoint returns 403, BCrypt password verification works.

## Item 8: Member service and controller
- status: TODO
- priority: P0
- complexity: M
- depends_on: [Item 2, Item 6, Item 7]
- spec: specs/member-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1 (login endpoint, hard delete cascading, post-registration response, profile endpoints)
- description: MemberService with register (BCrypt hash, duplicate email check), login (validate credentials, return profile), getProfile, updateProfile, deleteMember (cancel PENDING orders restoring stock, delete cart+items, hard delete member, reject if CONFIRMED/SHIPPED orders exist), listAll (paginated), getById. MemberController (@RestController /api/members) with all 7 endpoints. Request DTOs: MemberRegisterRequest (email, password, name, phone, address with javax.validation), MemberUpdateRequest, MemberLoginRequest. Response DTO: MemberResponse (no password field).
- acceptance: POST /api/members creates member and returns 201 with profile (no password). POST /api/members/login returns 200 with profile or 401. GET /me returns authenticated member. PUT /me updates fields. DELETE /me hard-deletes with cascade. GET /api/members (admin) returns paginated list. Duplicate email returns 409.
- tests: MemberControllerTest (MockMvc integration) — register success 201, register duplicate email 409, register invalid email 400, login success 200, login wrong password 401, get profile 200, update profile 200, delete member 204, delete member with active orders 409, admin list members paginated, admin get member by id, unauthenticated access 401.

## Item 9: Product service and controller
- status: TODO
- priority: P0
- complexity: M
- depends_on: [Item 3, Item 6, Item 7]
- spec: specs/product-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1 (soft delete, search aliases list, categories endpoint)
- description: ProductService with create, getById (any status), search (keyword, category, price range, sort, pagination — same method for list and search), update, delete (set INACTIVE), getCategories. ProductController (@RestController /api/products) with 7 endpoints including GET /api/products/categories. Request DTOs: ProductCreateRequest, ProductUpdateRequest (with javax.validation). Response DTO: ProductResponse.
- acceptance: GET /api/products returns paginated ACTIVE products. GET /api/products/{id} returns any product or 404. POST creates (admin), PUT updates (admin), DELETE soft-deletes (admin). Search filters work in combination. GET /categories returns distinct categories.
- tests: ProductControllerTest (MockMvc integration) — list products paginated, get product by id, get nonexistent product 404, create product as admin 201, create product as user 403, update product, delete product (verify INACTIVE), search by keyword, search by category, search by price range, search with sort, get categories, validation errors 400.

## Item 10: Cart service and controller
- status: TODO
- priority: P1
- complexity: M
- depends_on: [Item 3, Item 4, Item 6, Item 7]
- spec: specs/cart-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1 (stock validation, inactive product handling, cart live data, clear cart behavior)
- description: CartService with getCart (auto-create if not exists, return items with live product data and subtotals), addItem (create cart if needed, merge quantity if product already in cart, validate product ACTIVE and stock), updateItemQuantity (validate absolute quantity against stock and product status), removeItem (verify ownership), clearCart (delete all items, keep cart entity). CartController (@RestController /api/cart) with 5 endpoints. Request DTOs: CartAddItemRequest (productId, quantity), CartUpdateItemRequest (quantity). Response DTOs: CartResponse (items list with productName, unitPrice, quantity, subtotal, productStatus + cartTotal).
- acceptance: GET /api/cart returns cart with items and totals (auto-creates cart if first access). POST /api/cart/items adds new item or merges quantity. PUT updates quantity. DELETE item removes single item. DELETE /api/cart clears all items. Adding INACTIVE product returns 400. Exceeding stock returns 400.
- tests: CartControllerTest (MockMvc integration) — get empty cart, add item to cart, add same product merges quantity, add inactive product 400, add exceeding stock 400, update item quantity, update item exceeding stock 400, remove single item, clear cart, cart items show live product data, unauthenticated access 401, cannot modify another user's cart items.

## Item 11: Order service and controller
- status: TODO
- priority: P1
- complexity: L
- depends_on: [Item 3, Item 4, Item 5, Item 6, Item 7]
- spec: specs/order-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1 (transactional creation, pessimistic locking, strict status transitions, cancellation stock restoration, shipping address fallback)
- description: OrderService with createOrder (@Transactional: validate cart not empty, validate all products ACTIVE with sufficient stock using SELECT FOR UPDATE, snapshot product name/price into OrderItems, decrease stock, clear cart items, create order with PENDING status; shippingAddress from request body or fallback to member.address, 400 if both null), getMyOrders (paginated), getOrderDetail (verify ownership or admin), updateStatus (admin, enforce strict transitions), cancelOrder (user, only PENDING, restore stock), getAllOrders (admin, paginated). OrderController (@RestController /api/orders + /api/admin/orders) with 6 endpoints. Request DTOs: OrderCreateRequest (shippingAddress), OrderStatusUpdateRequest (status). Response DTOs: OrderResponse, OrderItemResponse.
- acceptance: POST /api/orders creates order from cart, snapshots prices, decreases stock, clears cart in single transaction. Empty cart returns 400. Inactive product in cart returns 400. Insufficient stock returns 400 (no partial changes). GET /api/orders returns user's orders paginated. GET /api/orders/{id} returns detail with items (own or admin). PUT status enforces PENDING→CONFIRMED→SHIPPED→DELIVERED only. Cancel restores stock. Admin list works. Missing shipping address with no member address returns 400.
- tests: OrderControllerTest (MockMvc integration) — create order success (verify stock decreased, cart cleared, prices snapshotted), create with empty cart 400, create with inactive product 400, create with insufficient stock 400 (verify no partial changes), create with shipping address, create with fallback to member address, create with no address 400, list my orders paginated, get order detail, get other user's order 403, admin get any order, update status valid transitions, update status invalid transition 400, cancel pending order (verify stock restored), cancel non-pending order 400, admin list all orders.

## Item 12: Login and Register frontend page
- status: TODO
- priority: P1
- complexity: M
- depends_on: [Item 8]
- spec: specs/frontend-pages.md
- clarity_ref: CLARITY_LOG.md#Round-1 (post-registration auto-login, Basic auth storage in sessionStorage)
- description: src/main/webapp/static/login.html with tab toggle between Login and Register forms. Login: email + password fields, submit calls POST /api/members/login with JSON body, on success store Base64(email:password) in sessionStorage and redirect to index.html. Register: email + password + name + phone + address fields, submit calls POST /api/members, on success auto-login (store credentials in sessionStorage, redirect). Error messages displayed inline. Shared CSS file (style.css) with clean minimal layout, consistent color scheme, responsive design. Common JS utility (app.js) with apiCall helper that attaches Authorization header from sessionStorage, 401 handler that redirects to login.html.
- acceptance: Login form submits credentials and stores auth on success. Register form creates account and auto-logs in. Invalid credentials show error message. Tab toggle switches between forms. Unauthenticated redirect works.
- tests: Manual verification (no JUnit for static HTML). Acceptance verified during Phase 3 by loading pages and testing API integration.

## Item 13: Home and Product Detail frontend pages
- status: TODO
- priority: P1
- complexity: M
- depends_on: [Item 9, Item 12]
- spec: specs/frontend-pages.md
- clarity_ref: CLARITY_LOG.md#Round-1 (categories endpoint, search, unauthenticated cart redirect)
- description: index.html — product grid/list with name, price, category. Category filter sidebar populated from GET /api/products/categories. Search bar (keyword). Pagination controls. "Add to Cart" button per product (checks sessionStorage, redirects to login if unauthenticated, calls POST /api/cart/items if authenticated). product.html — reads id from query param, displays product image/name/description/price/stock status, quantity selector, "Add to Cart" button, back to list link. Both pages use shared style.css and app.js.
- acceptance: Home page loads and displays products from API. Category filter narrows results. Search by keyword works. Pagination navigates pages. Product detail page shows full product info. Add to Cart works for authenticated users and redirects for unauthenticated.
- tests: Manual verification. Acceptance verified during Phase 3.

## Item 14: Cart frontend page
- status: TODO
- priority: P2
- complexity: M
- depends_on: [Item 10, Item 12]
- spec: specs/frontend-pages.md
- clarity_ref: CLARITY_LOG.md#Round-1 (shipping address input, cart with inactive products)
- description: cart.html — requires authentication (redirect if not). Displays cart items table (product name, unit price, quantity input, subtotal, remove button). Shows unavailable styling for INACTIVE products. Cart total. Shipping address text input pre-filled from member profile (GET /api/members/me). "Clear Cart" button. "Proceed to Order" button calls POST /api/orders with shippingAddress. Error messages for stock/inactive issues. Uses shared style.css and app.js.
- acceptance: Cart page displays items with totals. Quantity editable (calls PUT). Remove button works. Clear cart works. Proceed to Order creates order and redirects to orders page. Inactive products shown with unavailable styling.
- tests: Manual verification. Acceptance verified during Phase 3.

## Item 15: Orders frontend page
- status: TODO
- priority: P2
- complexity: M
- depends_on: [Item 11, Item 12]
- spec: specs/frontend-pages.md
- clarity_ref: CLARITY_LOG.md#Round-1 (inline order detail, cancel only PENDING)
- description: orders.html — requires authentication (redirect if not). Displays order list (ID, date, total amount, status badge). Click expands inline to show OrderItem details (product name, quantity, unit price, subtotal). Cancel button visible only for PENDING orders, calls PUT /api/orders/{id}/cancel. Pagination for order list. Uses shared style.css and app.js.
- acceptance: Orders page lists user's orders from API. Click expands to show order items inline. Cancel button works for PENDING orders and confirms before calling API. Pagination works.
- tests: Manual verification. Acceptance verified during Phase 3.

PHASE_1_COMPLETE
