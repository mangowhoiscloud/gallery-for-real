# Implementation Plan
Generated: 2026-03-21T00:00:00Z
Total_Items: 15
Completed: 3
Test_Items: 15 (target: ≥70% of implementation items, tests embedded in each item)

## Dependency Graph
```
Independent_Groups:
  - group_1: [Item 1, Item 2]                                                    # scaffolding, no dependencies
  - group_2: [Item 3, Item 4, Item 6, Item 7]                                    # core utilities + shared components, depends on group_1
  - group_3: [Item 5, Item 8, Item 9, Item 10, Item 11, Item 12, Item 13, Item 14, Item 15]  # layout + all pages, depends on group_2
Build_Order: group_1 → group_2 → group_3
```

---

## Item 1: Project scaffolding and configuration
- status: DONE
- priority: P0
- complexity: S
- depends_on: []
- spec: specs/shop-frontend.md
- clarity_ref: CLARITY_LOG.md#Round-1 (Tailwind v4 CSS tokens, primary #1a1a2e, accent #2563eb)
- description: Create Next.js 15 app directory structure (app/layout.tsx placeholder, app/page.tsx placeholder), configure Tailwind CSS v4 with CSS-based @theme in app/globals.css (color palette, dark mode variables, spacing, typography tokens), set up Jest (jest.config.ts with ts-jest and jsdom, jest.setup.ts importing @testing-library/jest-dom), verify tsconfig.json has strict mode and path aliases (@/ → ./), add postcss.config.mjs for Tailwind v4. Create lib/ directory structure.
- acceptance: `npm run build` succeeds. `npm test` runs with zero errors (no tests yet is OK). Tailwind CSS tokens defined in globals.css. Path alias @/ resolves correctly.
- tests: Verify Jest config initializes without errors. Verify a minimal component snapshot test can run.

## Item 2: TypeScript types and interfaces
- status: DONE
- priority: P0
- complexity: S
- depends_on: []
- spec: specs/shop-frontend.md
- clarity_ref: CLARITY_LOG.md#Round-1 (Product DTO shape, Order statuses)
- description: Define all TypeScript interfaces in lib/types.ts. Product {id, name, price, description, imageUrl, category, stockQuantity, createdAt}. CartItem {id, product: Product, quantity}. CartResponse {id, items: CartItem[], totalPrice}. Order {id, items: OrderItem[], totalAmount, status: OrderStatus, shippingAddress, createdAt}. OrderItem {id, productId, productName, quantity, price}. OrderStatus enum (PENDING, CONFIRMED, SHIPPED, DELIVERED, CANCELLED). Member {id, email, name, phone?, address?}. PageResponse<T> {content: T[], totalElements, totalPages, size, number}. ApiError {status, message}. AuthCredentials {email, password}. ShippingAddress {name, addressLine1, addressLine2?, city, state, zipCode, country}. Include test factory functions in __tests__/factories.ts for creating mock data.
- acceptance: All types compile under strict mode. No `any` types. All API response shapes covered. Factory functions create valid mock data.
- tests: Type-level compilation tests. Factory functions return correctly shaped objects. Verify no `any` leaks with a lint rule.

## Item 3: API client with auth and error handling
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 2]
- spec: specs/shop-frontend.md
- clarity_ref: CLARITY_LOG.md#Round-1 (error handling strategy, pagination format, Base64 auth)
- description: Create lib/api.ts with centralized fetch wrapper. Inject HTTP Basic Auth header (Base64 email:password from auth utils) on every authenticated request. Handle errors: 401→throw AuthError (callers redirect to login), 404→throw NotFoundError, 500/network→throw ApiError. Use NEXT_PUBLIC_API_URL env var as base URL. Typed methods for all 16 endpoints — Products: searchProducts(params), getProductById(id); Cart: getCart(), addToCart(productId, quantity), updateCartItemQuantity(cartItemId, quantity), removeCartItem(cartItemId), clearCart(); Orders: createOrder(shippingAddress), getOrders(page, size), getOrderById(id), cancelOrder(id); Auth: login(email, password), register(name, email, password); Members: getProfile(), updateProfile(data). Parse Spring Boot PageResponse format (content, totalElements, totalPages, size, number).
- acceptance: All 16 endpoint methods exist with correct TypeScript return types. Auth header injected when credentials exist, omitted when not. Error responses throw typed errors. Fetch is called with correct URL, method, headers, body.
- tests: Test auth header injection (present when authed, absent when not). Test each endpoint method constructs correct request (URL, method, body). Test error handling for 401, 404, 500 status codes. Test PageResponse parsing. Mock fetch globally in tests.

## Item 4: Auth utilities
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 2]
- spec: specs/shop-frontend.md
- clarity_ref: CLARITY_LOG.md#Round-1 (Remember Me: sessionStorage default → localStorage on check)
- description: Create lib/auth.ts with functions: saveCredentials(email, password, rememberMe) — stores Base64(email:password) in sessionStorage by default, localStorage if rememberMe=true; also stores a flag indicating which storage is used. getCredentials() — reads from the active storage, returns {email, password} or null. clearCredentials() — removes from both storages. isAuthenticated() — returns boolean. getAuthHeader() — returns "Basic <base64>" string or null. Create a useAuth() React hook (client-side) that provides auth state and methods with re-render on login/logout via useSyncExternalStore or state.
- acceptance: Credentials persist in sessionStorage by default. With rememberMe, persist in localStorage across tabs. clearCredentials removes from both. getAuthHeader returns correct Base64-encoded string. useAuth hook triggers re-render on auth changes.
- tests: Test saveCredentials stores in correct storage. Test getCredentials retrieves correctly. Test clearCredentials removes from both. Test Base64 encoding correctness. Test isAuthenticated returns true/false appropriately. Test rememberMe flag behavior.

## Item 5: Root layout, Header, and Footer
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 3, Item 4]
- spec: specs/shop-frontend.md
- clarity_ref: CLARITY_LOG.md#Round-1 (dark mode toggle, color palette, cart badge)
- description: Create app/layout.tsx — root layout with <html lang="en"> (dark class toggle), body with font, metadata (title, description), ThemeProvider wrapper, ToastProvider. Create components/Header.tsx (client component) — logo/brand link, nav links (Home, Products), conditional auth links (Cart + badge with count, Orders, Profile when authed; Login, Register when not), dark mode toggle button (sun/moon icon), responsive hamburger menu on mobile. Create components/Footer.tsx — brand name, nav links (Products, About, Contact), copyright year. ThemeProvider: detect system preference via matchMedia, toggle with button, persist choice in localStorage, apply "dark" class to <html>.
- acceptance: Layout renders with header and footer on all pages. Nav shows correct links based on auth state. Dark mode toggles between light/dark and persists across reloads. Cart badge shows item count (0 when empty, fetched from API when authed). Mobile hamburger menu opens/closes. Responsive layout at all breakpoints.
- tests: Test Header renders correct nav links for authenticated user. Test Header renders correct links for unauthenticated user. Test dark mode toggle changes theme. Test cart badge displays count. Test mobile menu toggle. Test Footer renders links and copyright.

## Item 6: Shared UI components
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 2]
- spec: specs/shop-frontend.md
- clarity_ref: CLARITY_LOG.md#Round-1 (responsive grid 1/2-3/4-6 cols, out-of-stock badge, pagination format)
- description: Create reusable components in components/ui/. ProductCard: next/image for product photo, name, formatted price ($XX.XX), category badge, stock indicator ("Out of Stock" red badge if stockQuantity=0, "Only X left" amber text if stockQuantity≤5, no indicator otherwise), link to /products/[id], hover shadow/scale transition. ProductGrid: responsive CSS grid (1 col mobile, 2 cols sm, 3 cols md, 4 cols lg), accepts children or product array. LoadingSkeleton: animated pulse placeholder matching ProductCard dimensions (image rect, text lines, price line). Pagination: page number buttons, Previous/Next with disabled states, ellipsis for large ranges, current page highlight. Breadcrumb: ordered list of {label, href} with separator chevrons, last item non-linked.
- acceptance: ProductCard renders all product fields with proper formatting. Out-of-stock badge shows for zero stock. "Only X left" shows for low stock. Grid responds to viewport breakpoints. Skeleton matches card proportions. Pagination disables prev on first page, next on last page. Breadcrumb renders correct links.
- tests: Test ProductCard renders name, price, image. Test out-of-stock badge when stockQuantity=0. Test "Only X left" when stockQuantity≤5. Test grid responsive classes. Test Pagination disabled states for first/last page. Test Breadcrumb renders links with correct hrefs.

## Item 7: Toast notification system and Error boundary
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 1]
- spec: specs/shop-frontend.md
- clarity_ref: CLARITY_LOG.md#Round-1 (undo toast 5s, error handling with error boundaries)
- description: Create toast system using Radix UI Toast primitive. components/ui/Toast.tsx — styled toast with variants (success green, error red, info blue), title, description, optional action button (for undo use case). lib/toast.ts — useToast() hook returning {toast, toasts, dismiss} with auto-dismiss after 5 seconds. ToastProvider wrapping app in layout. Create components/ErrorBoundary.tsx — catches render errors, shows fallback UI with error message and "Try Again" button that resets state. Create app/not-found.tsx — 404 page with "Page not found" message and link to home. Create app/error.tsx — client error boundary page with retry.
- acceptance: toast() function triggers visible toast notification. Toasts auto-dismiss after 5 seconds. Action button in toast triggers callback (for undo). Error boundary catches thrown errors and shows fallback. "Try Again" resets error. 404 page renders for unknown routes.
- tests: Test toast appears with correct variant styling. Test toast auto-dismisses after timeout. Test action button triggers callback. Test ErrorBoundary catches error and renders fallback. Test retry button resets error state.

## Item 8: Home page
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 5, Item 6]
- spec: specs/shop-frontend.md
- clarity_ref: CLARITY_LOG.md#Round-1 (hero carousel 5s rotate, categories from API, new arrivals sort, best sellers)
- description: Create app/page.tsx as Server Component that fetches initial data. Hero section as Client Component — carousel of 3-5 featured products (first results from API), auto-rotates every 5 seconds, pauses on hover, prev/next arrow buttons, dot indicators for current slide, each slide links to product detail. Category navigation — horizontal scrollable bar of category buttons (derived from fetched products' categories, fallback constants: Electronics, Clothing, Home, Books, Sports), each links to /products?category=X. New Arrivals section — heading + ProductGrid showing 6 products sorted by createdAt desc. Best Sellers section — heading + ProductGrid showing 6 products sorted by price desc (proxy for popularity). All sections use Suspense + LoadingSkeleton for streaming.
- acceptance: Hero carousel auto-rotates every 5 seconds, pauses on hover, arrows and dots work. Category buttons link to correct filtered listing. New Arrivals shows newest 6 products. Best Sellers shows 6 products. Page loads with skeletons then populates. Responsive layout.
- tests: Test hero carousel renders slides and navigation. Test auto-rotation timer. Test category links have correct href params. Test New Arrivals section renders ProductCards. Test Best Sellers section renders ProductCards. Test loading skeletons show during fetch.

## Item 9: Auth pages — Login and Register
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 3, Item 4, Item 7]
- spec: specs/shop-frontend.md
- clarity_ref: CLARITY_LOG.md#Round-1 (register validation rules, remember me behavior)
- description: Create app/login/page.tsx (Client Component) — email input, password input, "Remember me" checkbox, "Sign In" submit button, "Don't have an account? Register" link. Inline validation (email format, password required). On submit, call login API; on success, save credentials (with rememberMe flag) and redirect to previous page (from ?redirect= param) or home. Show error toast on invalid credentials. Create app/register/page.tsx (Client Component) — name input (min 2 chars), email input (valid format), password input (min 8 chars), confirm password (must match), optional phone and address fields, "Create Account" button, "Already have an account? Login" link. On success, auto-login (save credentials) and redirect to home. Show inline validation errors and error toast for API failures.
- acceptance: Login form validates email format and password presence. Successful login saves credentials and redirects. Remember me toggles storage type. Invalid credentials show error toast. Register validates all fields with correct rules. Successful register auto-logs in. Confirm password must match. Link between login/register works.
- tests: Test login form validation (invalid email, empty password). Test login success saves credentials and redirects. Test remember me checkbox changes storage. Test login failure shows error toast. Test register form validation (short name, invalid email, short password, mismatch). Test register success auto-logs in. Test navigation links between pages.

## Item 10: Product listing page with filters and search
- status: DONE
- priority: P1
- complexity: L
- depends_on: [Item 5, Item 6]
- spec: specs/shop-frontend.md
- clarity_ref: CLARITY_LOG.md#Round-1 (debounced 300ms search, URL params, traditional pagination, filter chips)
- description: Create app/products/page.tsx (mix of Server/Client Components). Search bar — text input with debounced (300ms) onChange that updates URL ?keyword= param and triggers re-fetch. Category filter — dropdown or button group, sets ?category= URL param. Price range filter — min/max number inputs, sets ?minPrice= and ?maxPrice= URL params. Sort dropdown — options: Name A-Z, Name Z-A, Price Low-High, Price High-Low, Newest; sets ?sortBy= and ?sortDir= URL params. Active filter chips — displayed below filters showing each active filter (e.g., "Category: Electronics ×"), clicking × removes that filter. Results area — ProductGrid populated from API search results, LoadingSkeleton while fetching. Pagination — at bottom, uses totalPages from API response, clicking updates ?page= URL param. All filter state synced bidirectionally with URL search params for bookmarkability (direct URL access restores filters).
- acceptance: Search input debounces and triggers API call with keyword. All filters update URL params and API query. Filter chips show for active filters and remove on click. Pagination navigates pages. Direct URL with params (e.g., /products?category=Electronics&page=2) loads with correct filters applied. Loading skeleton shows during transitions. Empty state shows when no results match.
- tests: Test search input debounces at 300ms. Test filter changes update URL params. Test filter chips render for active filters. Test chip removal clears the filter. Test pagination updates page param. Test URL params restore filters on load. Test empty state renders when no results. Test sort options change API query.

## Item 11: Product detail page
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 3, Item 6, Item 7]
- spec: specs/shop-frontend.md
- clarity_ref: CLARITY_LOG.md#Round-1 (image zoom, related products same category, out-of-stock, rating placeholder)
- description: Create app/products/[id]/page.tsx (Server Component with Client interactive parts). Large product image with CSS hover zoom effect (scale transform on hover). Product info: name (h1), formatted price, description paragraph, category badge. Stock status: "In Stock" green text, "Only X left" amber if ≤5, "Out of Stock" red badge if 0. Quantity selector: number input with +/- buttons, min 1, max stockQuantity, disabled if out of stock. "Add to Cart" button: calls addToCart API, shows success toast with product name, disabled with "Out of Stock" text if stockQuantity=0. Static 5-star rating display (all stars filled, decorative only, optional rating prop for future). Breadcrumb: Home > Products > [Product Name]. Related Products section: fetch products from same category excluding current product, show max 4 in ProductGrid. Use generateMetadata for dynamic page title and description.
- acceptance: Product info renders correctly from API data. Image zooms on hover. Quantity selector respects stock bounds (1 to stockQuantity). Add to cart calls API and shows success toast. Button disabled when out of stock. Breadcrumb links to correct pages. Related products show same-category items excluding current. Meta title/description set dynamically.
- tests: Test product info renders (name, price, description, category). Test quantity selector min/max bounds. Test add-to-cart button calls API with correct productId and quantity. Test button disabled when stockQuantity=0. Test breadcrumb renders correct links. Test related products exclude current product. Test image zoom class on hover.

## Item 12: Cart page
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 3, Item 4, Item 7]
- spec: specs/shop-frontend.md
- clarity_ref: CLARITY_LOG.md#Round-1 (undo remove 5s toast, shipping free >$50 else $5, quantity stepper)
- description: Create app/cart/page.tsx (Client Component). Redirect to /login?redirect=/cart if not authenticated. Cart items list: each row shows product thumbnail (next/image), name (links to product detail), unit price, quantity stepper (+/- buttons with API calls to updateCartItemQuantity), line total (price × quantity), remove button (× icon). Remove with undo: optimistic UI — immediately remove item from display, show toast with "Undo" action button, if undo clicked within 5 seconds restore item (re-add via API), if timeout then removal is finalized. Order summary sidebar: subtotal (sum of line totals), shipping (free if subtotal > $50, else flat $5.00, labeled "Estimated Shipping"), total (subtotal + shipping). "Proceed to Checkout" button linking to /checkout. "Continue Shopping" link to /products. Empty cart state: illustration/icon, "Your cart is empty" text, "Start Shopping" button.
- acceptance: Cart items display with correct data. Quantity stepper updates quantity via API. Remove shows undo toast, item restored if undo clicked within 5s. Order summary calculates subtotal, shipping ($5 or free), and total correctly. Checkout button links to /checkout. Empty state shows when cart has no items. Redirect to login when not authenticated.
- tests: Test cart items render with product info. Test quantity stepper calls update API. Test remove triggers undo toast. Test undo restores item. Test order summary math (subtotal, free shipping threshold, total). Test empty cart state. Test auth redirect for unauthenticated user.

## Item 13: Checkout page
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 3, Item 4, Item 7]
- spec: specs/shop-frontend.md
- clarity_ref: CLARITY_LOG.md#Round-1 (address pre-fill from profile, redirect to /orders/{id})
- description: Create app/checkout/page.tsx (Client Component). Redirect to /login?redirect=/checkout if not authenticated. Redirect to /cart if cart is empty (fetch cart on mount). Shipping address form: name, address line 1 (required), address line 2 (optional), city (required), state (required), zip code (required), country (required, default "US"). Pre-fill from member profile (fetch on mount). Required field validation with inline error messages. Order summary panel: list of cart items (name, qty, line total), subtotal, shipping ($5 or free if >$50), grand total. "Place Order" button: on click, call createOrder API with shipping address, on success clear cart (clearCart API), then redirect to /orders/{orderId}. Show loading state on button during submission. Show error toast on failure.
- acceptance: Form pre-fills from profile data. Required field validation prevents submission. Place order calls API with correct address. On success, cart clears and redirects to order detail page. Loading state shows during submission. Error toast on API failure. Redirects to login if not authed. Redirects to cart if cart empty.
- tests: Test form pre-fills from profile. Test required field validation (empty fields show errors). Test place order calls createOrder API. Test successful order redirects to /orders/{id}. Test cart clears on success. Test loading state on submit button. Test auth redirect. Test empty cart redirect.

## Item 14: Orders page with order detail
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 3, Item 4, Item 6]
- spec: specs/shop-frontend.md
- clarity_ref: CLARITY_LOG.md#Round-1 (order statuses, expandable details, cancel PENDING only)
- description: Create app/orders/page.tsx (Client Component). Redirect to /login if not authenticated. Paginated order list: each row shows order ID, date (formatted), item count, total amount, status badge (color-coded: PENDING=yellow, CONFIRMED=blue, SHIPPED=purple, DELIVERED=green, CANCELLED=red). Expandable inline details: click row to expand and show items (name, quantity, price), shipping address, created date. Cancel button visible only for PENDING orders, shows confirmation dialog before calling cancelOrder API, updates status to CANCELLED on success. "View Details" link to /orders/[id]. Pagination for order list. Empty state when no orders. Create app/orders/[id]/page.tsx — full order detail page with all order info, status flow visualization (horizontal stepper showing PENDING → CONFIRMED → SHIPPED → DELIVERED with current step highlighted, CANCELLED shown separately), item list, and cancel button if PENDING.
- acceptance: Order list paginates correctly. Status badges show correct colors. Expand reveals full order details. Cancel button only appears for PENDING orders. Cancel confirmation dialog prevents accidental cancellation. Individual order page shows complete details with status stepper. Empty state for no orders. Auth redirect works.
- tests: Test order list renders with correct data. Test status badge color mapping. Test expand/collapse toggle. Test cancel button shows only for PENDING. Test cancel confirmation dialog. Test cancel API call updates status. Test pagination. Test empty state. Test order detail page renders.

## Item 15: Profile page
- status: DONE
- priority: P1
- complexity: S
- depends_on: [Item 3, Item 4]
- spec: specs/shop-frontend.md
- clarity_ref: CLARITY_LOG.md#Round-1
- description: Create app/profile/page.tsx (Client Component). Redirect to /login if not authenticated. Profile display: name, email (read-only), phone, address. Edit mode: "Edit Profile" button toggles inputs to editable fields, "Save" and "Cancel" buttons appear. Save calls updateProfile API and shows success toast. "My Orders" shortcut link to /orders. "Logout" button: clears credentials (clearCredentials), shows toast, redirects to home. Loading state while fetching profile.
- acceptance: Profile displays member info correctly. Edit mode toggles fields to editable. Save updates profile via API and shows success toast. Cancel reverts changes. Logout clears auth and redirects to home. Orders link navigates correctly. Auth redirect for unauthenticated users.
- tests: Test profile info renders correctly. Test edit mode toggles input fields. Test save calls updateProfile API. Test cancel reverts unsaved changes. Test logout clears credentials and redirects. Test auth redirect.

---

## Summary

| Group | Items | Priority | Parallelism |
|-------|-------|----------|-------------|
| group_1 | Item 1, Item 2 | P0 | 2 parallel |
| group_2 | Item 3, Item 4, Item 6, Item 7 | P0 | 4 parallel |
| group_3 | Item 5, Item 8–15 | P0–P1 | 9 parallel |

| Complexity | Count | Items |
|------------|-------|-------|
| S | 5 | 1, 2, 4, 7, 15 |
| M | 9 | 3, 5, 6, 8, 9, 11, 12, 13, 14 |
| L | 1 | 10 |

Estimated test methods: ≥45 (3+ per item × 15 items), target 30+ met.

PHASE_1_COMPLETE
