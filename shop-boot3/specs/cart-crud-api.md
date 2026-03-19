# Cart CRUD REST API

## Entities

### Cart
| Field     | Type      | Constraints              |
|-----------|-----------|--------------------------|
| id        | Long      | PK, auto-increment       |
| memberId  | Long      | FK → Member, unique      |
| createdAt | Timestamp | auto-set on insert       |
| updatedAt | Timestamp | auto-set on insert/update|

### CartItem
| Field     | Type      | Constraints              |
|-----------|-----------|--------------------------|
| id        | Long      | PK, auto-increment       |
| cartId    | Long      | FK → Cart                |
| productId | Long      | FK → Product             |
| quantity  | Integer   | NOT NULL, >= 1           |
| createdAt | Timestamp | auto-set on insert       |

- One cart per member (auto-created on first add)
- Unique constraint: (cartId, productId) — adding same product increases quantity

## REST Endpoints
| Method | Path                       | Description          | Auth Required |
|--------|----------------------------|----------------------|---------------|
| GET    | /api/cart                  | Get my cart + items  | USER          |
| POST   | /api/cart/items            | Add item to cart     | USER          |
| PUT    | /api/cart/items/{itemId}   | Update item quantity | USER          |
| DELETE | /api/cart/items/{itemId}   | Remove item          | USER          |
| DELETE | /api/cart                  | Clear entire cart    | USER          |

## Request/Response
- Add item request: `{ "productId": 1, "quantity": 2 }`
- Cart response includes product name, price, subtotal per item, and cart total
- Validate product exists and is ACTIVE
- Validate requested quantity <= available stock
