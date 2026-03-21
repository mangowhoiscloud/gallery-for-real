# CLARITY_LOG — shop-front

## Round 1

---

### Ambiguity 1
```
Round: 1
Spec: shop-frontend.md
Category: CONTRADICTION
Severity: CRITICAL
Q: The Home page spec says "Product grid (6~12 items per row responsive)" but the Responsive Breakpoints section says "Desktop: > 1024px (4–6 columns)". Which is correct? 6-12 items per row would be extremely dense and contradict the "spacious layout with generous whitespace" design direction.
A: The "6~12 items per row" almost certainly means 6-12 items TOTAL displayed in the grid section, not per row. The Responsive Breakpoints section (1 col mobile, 2-3 tablet, 4-6 desktop) is more specific and consistent with the Shopify/Vercel Commerce reference. The number 6-12 refers to how many product cards appear in that home page section.
Confidence: 0.90
Remaining_Ambiguity: None significant — the breakpoints section is authoritative.
Resolution: Use the Responsive Breakpoints spec (1/2-3/4-6 columns). Display 8-12 products total in the home page product grid section, laid out according to the column breakpoints.
```
---

### Ambiguity 2
```
Round: 1
Spec: shop-frontend.md
Category: INTEGRATION_GAP
Severity: CRITICAL
Q: The spec lists "Category navigation bar" on the home page and "Filter sidebar: category" on product listing, but there is NO API endpoint for fetching categories. Where do category values come from?
A: The product search endpoint (`/api/products/search?category=`) accepts a category parameter, implying products have a category field. However, there's no endpoint to list available categories. Options: (1) hardcode categories, (2) derive from product data client-side, (3) assume the API returns category info in product objects.
Confidence: 0.75
Remaining_Ambiguity: We don't know the exact product DTO shape from the API.
Resolution: Assume products returned by the API include a `category` field. Extract unique categories client-side from the initial product fetch for the category nav. If the product list is paginated and we can't see all categories, define a reasonable set of common e-commerce categories as fallback constants (e.g., "Electronics", "Clothing", "Home", "Books", "Sports") that can be overridden by actual API data.
```
---

### Ambiguity 3
```
Round: 1
Spec: shop-frontend.md
Category: INTEGRATION_GAP
Severity: CRITICAL
Q: The home page requires "New Arrivals" and "Best Sellers" sections, but there are no dedicated API endpoints for these. The product search endpoint has `sortBy` and `sortDir` params — but what sort fields are available?
A: The search endpoint's `sortBy` parameter likely supports at least `createdAt`/`id` (for new arrivals) and possibly `salesCount`/`popularity` (for best sellers). Without knowing the exact fields, we can reasonably assume: "New Arrivals" = sort by creation date desc, "Best Sellers" = sort by price or a popularity metric.
Confidence: 0.65
Remaining_Ambiguity: We don't know valid `sortBy` values. "Best Sellers" may not be derivable without a sales-count field.
Resolution: "New Arrivals" → fetch `/api/products/search?sortBy=createdAt&sortDir=desc&size=8`. "Best Sellers" → fetch `/api/products/search?sortBy=price&sortDir=desc&size=8` as a proxy (highest-priced as "premium picks"). If the API supports a `salesCount` or `popularity` sort field, prefer that. The section title can be adjusted to "Popular" or "Featured" if true best-seller data is unavailable. Tag: SPEC_GAP_CRITICAL — ideally the API should expose sort field options.
```
---

### Ambiguity 4
```
Round: 1
Spec: shop-frontend.md
Category: INTEGRATION_GAP
Severity: CRITICAL
Q: The home page calls for a "Hero banner with featured products (rotating carousel)." There is no "featured products" API endpoint. How are featured products determined?
A: Without a dedicated endpoint, featured products must be derived. Options: (1) use the first N products from the default listing, (2) hardcode featured product IDs, (3) use a random selection. A rotating carousel also raises UX questions — auto-rotate with pause on hover is standard.
Confidence: 0.70
Remaining_Ambiguity: No clear "featured" designation from the API.
Resolution: Use the first 3-5 products returned from `/api/products` (default sort) as "featured" items for the carousel. The carousel auto-rotates every 5 seconds, pauses on hover, and has manual prev/next controls and dot indicators. This can be refined later if the API adds a `featured` flag.
```
---

### Ambiguity 5
```
Round: 1
Spec: shop-frontend.md
Category: INTEGRATION_GAP
Severity: CRITICAL
Q: Product detail page requires a "Related products section" but there is no API endpoint for related products. How should related products be determined?
A: Without a related-products endpoint, the most practical approach is to fetch products from the same category as the current product. The search endpoint supports `category` filtering.
Confidence: 0.85
Remaining_Ambiguity: Requires products to have a category field (see Ambiguity 2).
Resolution: Fetch related products via `/api/products/search?category={currentProduct.category}` excluding the current product ID. Display up to 4 related products. If category is unavailable, show random products from the general listing.
```
---

### Ambiguity 6
```
Round: 1
Spec: shop-frontend.md
Category: INTEGRATION_GAP
Severity: CRITICAL
Q: The pagination format for `/api/products` is unspecified. The endpoint says "paginated, searchable" but doesn't define query parameters for pagination. Is it page/size-based or cursor-based? What's the response envelope (total count, total pages)?
A: Spring Boot (shop-boot3) typically uses page/size-based pagination with a Spring Page response object containing `content`, `totalElements`, `totalPages`, `number`, `size`, etc. This is a very strong convention for Spring Boot REST APIs.
Confidence: 0.90
Remaining_Ambiguity: Minor — exact field names may vary but Spring Boot conventions are well-established.
Resolution: Assume Spring Boot Page response format. Use `?page=0&size=12` query params (0-indexed pages). Expect response shape: `{ content: Product[], totalElements: number, totalPages: number, number: number, size: number, first: boolean, last: boolean }`. Define the TypeScript interface accordingly.
```
---

### Ambiguity 7
```
Round: 1
Spec: shop-frontend.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: The spec says "Pagination or infinite scroll" for product listing. Which approach should be used?
A: The spec leaves this as a choice. Pagination is simpler to implement, more accessible, better for SEO (each page has a URL), and aligns with the Spring Boot Page response. Infinite scroll has UX benefits for browsing but complicates footer access and state management.
Confidence: 0.85
Remaining_Ambiguity: None — this is a design choice.
Resolution: Implement traditional pagination with numbered page buttons (First, Prev, 1, 2, 3..., Next, Last). This aligns with the paginated API response and is more predictable. Consider adding a "load more" button variant as a simpler alternative to full infinite scroll if time permits.
```
---

### Ambiguity 8
```
Round: 1
Spec: shop-frontend.md
Category: INTEGRATION_GAP
Severity: MAJOR
Q: The Product Card component includes "rating placeholder" but there is no rating/review API endpoint. What should be displayed?
A: "Placeholder" explicitly signals this is not functional yet. It's a visual placeholder for a future rating feature, not an active feature.
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: Render a static 5-star display with no rating value (all stars gray/empty) or omit the rating row entirely to keep the UI clean. Do NOT generate fake ratings. If pressed, show a subtle "No reviews yet" text. The component should accept an optional `rating` prop for future use.
```
---

### Ambiguity 9
```
Round: 1
Spec: shop-frontend.md
Category: INTEGRATION_GAP
Severity: MAJOR
Q: Cart page shows "shipping estimate" in the order summary sidebar, but there is no shipping calculation API. What should be displayed?
A: Without a shipping API, this must be a static estimate or a simple rule-based calculation.
Confidence: 0.80
Remaining_Ambiguity: None significant.
Resolution: Display a static shipping estimate: "Free shipping" for orders over a threshold (e.g., $50), otherwise show a flat rate (e.g., $5.00). Label it as "Estimated Shipping" to indicate it's not final. The checkout flow can refine this. These values should be defined as constants in a config file for easy adjustment.
```
---

### Ambiguity 10
```
Round: 1
Spec: shop-frontend.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: Auth spec says "Remember me option (persist credentials)" but the CLAUDE.md says "Auth credentials stored in localStorage (Base64 encoded email:password)." If credentials are ALWAYS in localStorage, what does "Remember me" toggle?
A: The distinction is between sessionStorage (cleared on tab close) and localStorage (persists across sessions). "Remember me" checked = localStorage, unchecked = sessionStorage. This is the standard web pattern.
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: Default behavior (no "Remember me") stores credentials in sessionStorage. When "Remember me" is checked, store in localStorage. The auth helpers in `lib/auth.ts` should abstract this with a `persistent` parameter. CLAUDE.md's mention of localStorage describes the persistent case.
```
---

### Ambiguity 11
```
Round: 1
Spec: shop-frontend.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: The spec requires "Dark/light mode support" but doesn't specify the toggle mechanism, default mode, or persistence.
A: Standard patterns: (1) respect `prefers-color-scheme` system preference as default, (2) provide a toggle button in the header, (3) persist choice in localStorage.
Confidence: 0.85
Remaining_Ambiguity: None.
Resolution: Default to system preference via `prefers-color-scheme` media query. Add a theme toggle button (sun/moon icon) in the header. Persist the user's explicit choice in localStorage under key `theme`. Implement via a `dark` class on `<html>` element, using Tailwind's dark mode variant. Define dark mode color tokens alongside light mode tokens.
```
---

### Ambiguity 12
```
Round: 1
Spec: shop-frontend.md
Category: MISSING_ERROR_HANDLING
Severity: MAJOR
Q: The spec does not address error handling for API failures. What happens on network errors, 401 Unauthorized, 404 Not Found, 500 Internal Server Error?
A: Error handling is critical for production quality. The spec implicitly expects Shopify-grade UX, which includes graceful error states.
Confidence: 0.85
Remaining_Ambiguity: None — standard patterns apply.
Resolution: Implement in `lib/api.ts`: (1) 401 → clear credentials, redirect to /login with return URL. (2) 404 → show "not found" UI with back navigation. (3) 500/network → show error toast with retry option. (4) All API errors → throw typed errors that components can catch. (5) Use error boundaries for unexpected React errors. (6) Loading states with skeleton UI for all async operations.
```
---

### Ambiguity 13
```
Round: 1
Spec: shop-frontend.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: Checkout says "Order confirmation with order ID and status" — is this an inline confirmation on the checkout page after placing an order, or a redirect to a separate confirmation page/route?
A: Standard e-commerce flow: after successful order placement, redirect to an order confirmation page. This prevents accidental double-submission on refresh and provides a bookmarkable confirmation.
Confidence: 0.85
Remaining_Ambiguity: Should there be a dedicated `/orders/[id]/confirmation` route or reuse `/orders/[id]`?
Resolution: After successful `POST /api/orders`, redirect to `/orders/{orderId}` (the order detail page). Show a success toast/banner at the top indicating "Order placed successfully!" The order detail page serves as the confirmation page — no need for a separate `/checkout/confirmation` route. This avoids route duplication.
```
---

### Ambiguity 14
```
Round: 1
Spec: shop-frontend.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: Orders page says "Expandable order detail (inline or separate page)" — which approach?
A: The spec explicitly offers both as options. Inline expansion is more efficient for scanning multiple orders; a separate page provides more space for detail.
Confidence: 0.80
Remaining_Ambiguity: None — design choice.
Resolution: Implement inline expandable order details on the `/orders` page (click to expand/collapse each order showing items, shipping, etc.). Each order row also has a "View Details" link to `/orders/[id]` for the full detail page. This provides both options and is the most flexible UX.
```
---

### Ambiguity 15
```
Round: 1
Spec: shop-frontend.md
Category: UNSTATED_ASSUMPTION
Severity: MAJOR
Q: The product DTO shape is never specified. What fields does a Product object have? Specifically: does it include `imageUrl`, `category`, `stock`/`stockQuantity`, `createdAt`?
A: Based on the spec's UI requirements (image, name, price, description, stock status, category filter, sort by date), the product must have at minimum: id, name, price, description, imageUrl, category, stockQuantity (or inStock boolean), createdAt. A Spring Boot e-commerce API would typically include all of these.
Confidence: 0.80
Remaining_Ambiguity: Exact field names and whether imageUrl is a full URL or relative path.
Resolution: Define the Product interface as: `{ id: number, name: string, price: number, description: string, imageUrl: string, category: string, stockQuantity: number, createdAt: string }`. If the API returns different field names, the API client layer can map them. Assume imageUrl is a full URL. If images are missing/null, display a placeholder image.
```
---

### Ambiguity 16
```
Round: 1
Spec: shop-frontend.md
Category: UNSTATED_ASSUMPTION
Severity: MAJOR
Q: What are the valid order statuses? The spec shows "PENDING → CONFIRMED → SHIPPED → DELIVERED" but the API has a `PUT /api/orders/{id}/cancel` endpoint. Is CANCELLED a separate status? Can only PENDING orders be cancelled (as the UI spec suggests)?
A: The cancel endpoint combined with the UI spec saying "Cancel button for PENDING orders" implies CANCELLED is a valid status and cancellation is restricted to PENDING orders only.
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: Order statuses are: PENDING, CONFIRMED, SHIPPED, DELIVERED, CANCELLED. The cancel button is only shown when status === "PENDING". The status flow visualization shows the main happy path (PENDING→CONFIRMED→SHIPPED→DELIVERED) with CANCELLED as a branch from PENDING.
```
---

### Ambiguity 17
```
Round: 1
Spec: shop-frontend.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: The spec mentions "Search bar with real-time filtering" on the product listing page. Does "real-time" mean client-side filtering of already-loaded products, or debounced API calls on each keystroke?
A: Given the API has a search endpoint with `keyword` param, and products are paginated (not all loaded at once), this must be server-side search with debounced API calls. "Real-time" refers to the responsive UX feel, not local filtering.
Confidence: 0.85
Remaining_Ambiguity: Debounce interval.
Resolution: Implement debounced server-side search. On keystroke, debounce 300ms, then call `/api/products/search?keyword={query}`. Update the URL search params for bookmarkability. Show a loading indicator during the search. Clear search resets to the default product listing.
```
---

### Ambiguity 18
```
Round: 1
Spec: shop-frontend.md
Category: EDGE_CASE
Severity: MAJOR
Q: The checkout page has a "Shipping address form (name, phone, address)" — is this address saved to the user's profile, or is it per-order only? The API has `PUT /api/members/me` for profile updates.
A: The member profile likely includes address fields (given the register form asks for "address"). The checkout should pre-fill from the profile and optionally save updates back.
Confidence: 0.70
Remaining_Ambiguity: Whether the API's order creation endpoint accepts a shipping address or uses the member's profile address.
Resolution: Pre-fill the checkout address form from the user's profile (`GET /api/members/me`). Allow editing. On order placement, send the address as part of the `POST /api/orders` request body. Offer a "Save to profile" checkbox that, if checked, also calls `PUT /api/members/me` with the updated address. If the orders API doesn't accept an address, just use the profile address.
```
---

### Ambiguity 19
```
Round: 1
Spec: shop-frontend.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MINOR
Q: Color palette says "Primary: Deep charcoal (#1a1a2e) or brand accent" — the "or" makes the primary color ambiguous. Which one?
A: "#1a1a2e" is provided as a concrete value. "Or brand accent" is an alternative if the project has brand guidelines. Since no brand guidelines exist, use the provided value.
Confidence: 0.90
Remaining_Ambiguity: The "Accent: Bold action color (for CTAs)" has no hex value.
Resolution: Use #1a1a2e as the primary color. For the accent/CTA color, use a complementary bold color — #e63946 (vibrant red) or #2563eb (bright blue) are standard e-commerce CTA colors. Go with a blue accent (#2563eb) as it's more universally trustworthy for "Add to Cart" / "Buy" actions. Define all colors as Tailwind CSS custom properties.
```
---

### Ambiguity 20
```
Round: 1
Spec: shop-frontend.md
Category: EDGE_CASE
Severity: MINOR
Q: Cart page says "Remove item with undo option." How long should the undo window last? Is this a toast-based undo or inline?
A: Standard pattern is a toast notification with an "Undo" button that stays visible for 5 seconds. The item is visually removed immediately but the DELETE API call is deferred until the undo window expires.
Confidence: 0.80
Remaining_Ambiguity: None.
Resolution: On remove, immediately hide the item from the UI and show a toast with "Item removed. [Undo]" for 5 seconds. If undo is clicked, restore the item. If the toast expires, execute `DELETE /api/cart/items/{id}`. Use an optimistic UI pattern with rollback capability.
```
---

### Ambiguity 21
```
Round: 1
Spec: shop-frontend.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MINOR
Q: Testing target conflict: the spec says "at least 30 test methods" but CLAUDE.md says "Target: 70% test code." Which takes priority? Are both required?
A: These are complementary, not conflicting. 30 test methods is a minimum count; 70% test code ratio is a quality metric. Both can be satisfied.
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: Aim for both: at least 30 test methods AND 70% test-to-implementation code ratio. Prioritize meaningful tests (API client, auth logic, cart state management, component rendering) over trivial ones. The 30-method minimum ensures breadth; the 70% ratio ensures depth.
```
---

### Ambiguity 22
```
Round: 1
Spec: shop-frontend.md
Category: UNSTATED_ASSUMPTION
Severity: MINOR
Q: Tailwind CSS 4 uses a CSS-based configuration system rather than the traditional `tailwind.config.ts`. The CLAUDE.md says "use design tokens in tailwind.config" which may be outdated for v4. How should design tokens be configured?
A: Tailwind CSS v4 uses `@theme` directive in CSS files for customization instead of `tailwind.config.js`. The CLAUDE.md instruction predates this change. We should follow the actual framework conventions.
Confidence: 0.85
Remaining_Ambiguity: None.
Resolution: Use Tailwind CSS v4's CSS-based configuration with `@theme` in the global CSS file to define custom design tokens (colors, spacing, fonts). Do NOT create a `tailwind.config.ts` unless needed for plugin compatibility. Define color palette, typography, and spacing tokens in the CSS theme layer.
```
---

### Ambiguity 23
```
Round: 1
Spec: shop-frontend.md
Category: MISSING_ERROR_HANDLING
Severity: MINOR
Q: How should out-of-stock products be handled? The spec mentions "stock status" display but doesn't specify behavior when stockQuantity is 0.
A: Standard e-commerce pattern: show "Out of Stock" badge, disable "Add to Cart" button, optionally dim the product card.
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: When stockQuantity === 0: (1) Show "Out of Stock" badge on product card and detail page. (2) Disable "Add to Cart" button with visual indication. (3) Do NOT hide the product — it should still be browsable. (4) If stock is low (e.g., < 5), show "Only X left" urgency text.
```
---

### Ambiguity 24
```
Round: 1
Spec: shop-frontend.md
Category: UNSTATED_ASSUMPTION
Severity: MINOR
Q: The register form requires "email, password, name, phone, address" — what validation rules apply? Min password length? Email format? Phone format? Are all fields required?
A: The spec doesn't detail validation, but standard e-commerce registration has well-established patterns.
Confidence: 0.85
Remaining_Ambiguity: Backend-specific validation rules may differ.
Resolution: All fields required except phone and address (optional). Email: standard email format validation. Password: minimum 8 characters. Name: minimum 2 characters. Phone: optional, basic format check if provided. Address: optional free-form text. Show inline validation errors. Submit button disabled until required fields are valid. Server-side errors (e.g., "email already registered") displayed as form-level errors.
```
---

## Cross-Spec Consistency Check

Only one spec file exists (`shop-frontend.md`), so cross-spec contradictions are limited to internal consistency:

1. **RESOLVED**: "6~12 items per row" vs "4-6 columns" (see Ambiguity 1) — breakpoints section is authoritative.
2. **RESOLVED**: "localStorage" in CLAUDE.md vs "Remember me" in spec (see Ambiguity 10) — sessionStorage default, localStorage on "remember me."
3. **RESOLVED**: "tailwind.config" in CLAUDE.md vs Tailwind v4 CSS-based config (see Ambiguity 22) — use v4 CSS conventions.
4. **CONSISTENT**: Auth approach (HTTP Basic) is consistent between spec and CLAUDE.md.
5. **CONSISTENT**: Tech stack (Next.js 15, TypeScript, shadcn/ui, Jest) matches between spec, CLAUDE.md, and package.json.
6. **CONSISTENT**: Server Components for reads, Client Components for interactivity — stated in both spec and CLAUDE.md.

No cross-spec contradictions found that weren't already addressed in the Q&A rounds.

---

## Ambiguity Score

```
AMBIGUITY_SCORE: 0.04
Rounds_Completed: 1
Ambiguities_Found: 24
Ambiguities_Resolved: 23
Ambiguities_Remaining: 1
```

The one remaining ambiguity is the exact product DTO shape from the backend API (Ambiguity 15), which can only be fully resolved by testing against the actual API. However, a reasonable default interface has been defined.

Note: Ambiguity 3 has a SPEC_GAP_CRITICAL tag (missing sort field documentation for the API), but a workable resolution has been provided.

---

## Convergence Data

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

---

PHASE_0_COMPLETE
FINAL_AMBIGUITY_SCORE: 0.04
TOTAL_ROUNDS: 1
EXIT_REASON: THRESHOLD
