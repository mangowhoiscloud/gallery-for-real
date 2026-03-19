# Sample Frontend Pages

Static HTML + CSS + vanilla JavaScript pages served from `src/main/resources/static/`.
All pages call the REST API via `fetch()` with HTTP Basic Auth.

## Pages

### 1. Home (`index.html`)
- Product grid/list with thumbnail, name, price
- Category filter sidebar
- Search bar (keyword)
- Pagination controls
- "Add to Cart" button per product

### 2. Product Detail (`product.html?id={id}`)
- Product image, name, description, price, stock status
- Quantity selector + "Add to Cart" button
- Back to list link

### 3. Cart (`cart.html`)
- Cart items table: product name, unit price, quantity (editable), subtotal
- Remove button per item
- Cart total
- "Clear Cart" and "Proceed to Order" buttons

### 4. Orders (`orders.html`)
- Order list: order ID, date, total amount, status
- Click to view order detail
- Cancel button (for PENDING orders)

### 5. Login / Register (`login.html`)
- Tab or toggle between Login and Register forms
- Login: email + password
- Register: email + password + name + phone + address
- After login, store credentials for subsequent API calls

## Style
- Clean, minimal CSS (no framework required)
- Responsive layout (flexbox/grid)
- Consistent color scheme and spacing
- Loading states and error messages displayed inline

## Auth Flow
- Store Base64-encoded credentials in sessionStorage after login
- Attach `Authorization: Basic {credentials}` header to all API calls
- Redirect to login page if 401 received
