# Shopping Mall Frontend — Shopify-Grade E-Commerce UI

## Overview
Next.js 15 App Router 기반의 프리미엄 이커머스 프론트엔드.
Shopify, Vercel Commerce 수준의 비주얼 퀄리티를 목표로 한다.
백엔드 API(`shop-boot3`)와 HTTP Basic Auth로 연결.

## Tech Stack
- **Next.js 15** (App Router, Server Components)
- **TypeScript**
- **Tailwind CSS 4** + custom design tokens
- **shadcn/ui** components (Radix UI primitives)
- **next/image** for optimized images
- **Vercel** deployment target

## Backend API
Base URL: `http://localhost:8080` (dev) / 환경변수 `NEXT_PUBLIC_API_URL`

### Endpoints (shop-boot3 REST API)
- `POST /api/members` — 회원가입
- `POST /api/members/login` — 로그인 검증
- `GET /api/members/me` — 내 프로필
- `PUT /api/members/me` — 프로필 수정
- `GET /api/products` — 상품 목록 (paginated, searchable)
- `GET /api/products/{id}` — 상품 상세
- `GET /api/products/search?keyword=&category=&minPrice=&maxPrice=&sortBy=&sortDir=` — 검색
- `GET /api/cart` — 장바구니 조회
- `POST /api/cart/items` — 장바구니 추가
- `PUT /api/cart/items/{id}` — 수량 변경
- `DELETE /api/cart/items/{id}` — 항목 삭제
- `DELETE /api/cart` — 장바구니 비우기
- `POST /api/orders` — 주문 생성 (장바구니 → 주문)
- `GET /api/orders` — 내 주문 목록
- `GET /api/orders/{id}` — 주문 상세
- `PUT /api/orders/{id}/cancel` — 주문 취소

Auth: HTTP Basic (`Authorization: Basic base64(email:password)`)

## Pages & Routes

### 1. Home `/`
- Hero banner with featured products (rotating carousel)
- Category navigation bar
- Product grid (6~12 items per row responsive)
- "New Arrivals" / "Best Sellers" sections
- Footer with links

### 2. Product Listing `/products`
- Filter sidebar: category, price range (slider), sort options
- Product grid with hover effects (quick-add, image zoom)
- Pagination or infinite scroll
- Search bar with real-time filtering
- Active filter chips with clear-all

### 3. Product Detail `/products/[id]`
- Large product image with zoom-on-hover
- Product info: name, price, description, stock status
- Quantity selector + "Add to Cart" button (animated feedback)
- Related products section
- Breadcrumb navigation

### 4. Cart `/cart`
- Cart items with product thumbnail, name, price, quantity stepper, subtotal
- Remove item with undo option
- Order summary sidebar: subtotal, shipping estimate, total
- "Continue Shopping" + "Proceed to Checkout" CTAs
- Empty cart state with illustration

### 5. Checkout `/checkout`
- Shipping address form (name, phone, address)
- Order summary review
- "Place Order" button
- Order confirmation with order ID and status

### 6. Orders `/orders`
- Order history list: order ID, date, items count, total, status badge
- Expandable order detail (inline or separate page)
- Status flow visualization (PENDING → CONFIRMED → SHIPPED → DELIVERED)
- Cancel button for PENDING orders

### 7. Auth `/login`, `/register`
- Clean login form (email + password)
- Register form (email, password, name, phone, address)
- Form validation with inline errors
- "Remember me" option (persist credentials)
- Redirect to previous page after login

### 8. Profile `/profile`
- View/edit profile information
- Order history shortcut
- Logout button

## Design Requirements

### Visual Direction (Shopify/Vercel Commerce Reference)
- Clean, spacious layout with generous whitespace
- High-contrast typography hierarchy (large headings, readable body)
- Subtle micro-interactions (hover states, transitions, loading skeletons)
- Card-based product display with shadow and border-radius
- Consistent 4px/8px spacing grid
- Dark/light mode support

### Color Palette
- Primary: Deep charcoal (#1a1a2e) or brand accent
- Secondary: Warm neutral (#e8e4df)
- Accent: Bold action color (for CTAs)
- Success/Warning/Error semantic colors
- Background: Clean white with subtle gray sections

### Typography
- Headings: Inter or similar geometric sans-serif
- Body: System font stack for performance
- Monospace for prices/codes

### Components
- Product Card: image, name, price, rating placeholder, quick-add
- Cart Badge: animated counter in header
- Toast notifications for cart actions
- Loading skeletons (Shopify-style shimmer)
- Responsive mobile menu (hamburger → slide-out)

### Responsive Breakpoints
- Mobile: < 640px (1 column products)
- Tablet: 640–1024px (2–3 columns)
- Desktop: > 1024px (4–6 columns)

## API Client Architecture
- `lib/api.ts` — centralized fetch wrapper with auth header injection
- `lib/auth.ts` — credential storage (localStorage), login/logout helpers
- `lib/types.ts` — TypeScript interfaces matching backend DTOs
- Server Components for product listing (SSR with revalidation)
- Client Components for cart, auth, interactive elements

## Testing
- Component tests with Jest + React Testing Library
- API client unit tests
- E2E smoke test with Playwright (optional)
- Target: at least 30 test methods

## Build & Deploy
```bash
npm run dev      # local dev server
npm run build    # production build
npm run test     # run tests
vercel deploy    # deploy to Vercel
```
