# Order CRUD REST API

## Entities

### Order
| Field           | Type       | Constraints                        |
|-----------------|------------|------------------------------------|
| id              | Long       | PK, auto-increment                 |
| memberId        | Long       | FK → Member                        |
| totalAmount     | BigDecimal | NOT NULL, >= 0                     |
| status          | Enum       | PENDING/CONFIRMED/SHIPPED/DELIVERED/CANCELLED |
| shippingAddress | String     | NOT NULL, max 200 chars            |
| createdAt       | Timestamp  | auto-set on insert                 |
| updatedAt       | Timestamp  | auto-set on insert/update          |

### OrderItem
| Field       | Type       | Constraints              |
|-------------|------------|--------------------------|
| id          | Long       | PK, auto-increment       |
| orderId     | Long       | FK → Order               |
| productId   | Long       | FK → Product             |
| productName | String     | NOT NULL (snapshot)       |
| quantity    | Integer    | NOT NULL, >= 1           |
| unitPrice   | BigDecimal | NOT NULL (snapshot)       |

## Status Flow
```
PENDING → CONFIRMED → SHIPPED → DELIVERED
    ↓
CANCELLED (only from PENDING)
```

## REST Endpoints
| Method | Path                          | Description          | Auth Required |
|--------|-------------------------------|----------------------|---------------|
| POST   | /api/orders                   | Create from cart     | USER          |
| GET    | /api/orders                   | List my orders       | USER          |
| GET    | /api/orders/{id}              | Get order detail     | USER (owner) / ADMIN |
| PUT    | /api/orders/{id}/status       | Update status        | ADMIN         |
| PUT    | /api/orders/{id}/cancel       | Cancel order         | USER (owner)  |
| GET    | /api/admin/orders             | List all orders      | ADMIN         |

## Order Creation Flow
1. Validate cart is not empty
2. Validate all products are ACTIVE and have sufficient stock
3. Snapshot product name and price into OrderItem
4. Decrease product stock
5. Clear the cart
6. Return created order with items

## Cancellation
- Only PENDING orders can be cancelled
- Restore product stock on cancellation
