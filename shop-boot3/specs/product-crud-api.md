# Product CRUD REST API

## Entity: Product
| Field         | Type       | Constraints                       |
|---------------|------------|-----------------------------------|
| id            | Long       | PK, auto-increment                |
| name          | String     | NOT NULL, 1–100 chars             |
| description   | String     | nullable, max 2000 chars          |
| price         | BigDecimal | NOT NULL, >= 0                    |
| stockQuantity | Integer    | NOT NULL, >= 0                    |
| category      | String     | NOT NULL, 1–50 chars              |
| imageUrl      | String     | nullable, valid URL               |
| status        | Enum       | ACTIVE / INACTIVE, default ACTIVE |
| createdAt     | Timestamp  | auto-set on insert                |
| updatedAt     | Timestamp  | auto-set on insert/update         |

## REST Endpoints
| Method | Path                        | Description              | Auth Required |
|--------|-----------------------------|--------------------------|---------------|
| GET    | /api/products               | List all (paginated)     | None          |
| GET    | /api/products/{id}          | Get by ID                | None          |
| POST   | /api/products               | Create new               | ADMIN         |
| PUT    | /api/products/{id}          | Update existing          | ADMIN         |
| DELETE | /api/products/{id}          | Delete (soft/hard)       | ADMIN         |
| GET    | /api/products/search        | Search by name/category  | None          |

## Pagination & Search
- Query params: `page` (0-based), `size` (default 10, max 100)
- Search params: `keyword` (name LIKE), `category` (exact match), `minPrice`, `maxPrice`
- Sort: `sortBy` (name, price, createdAt), `sortDir` (asc, desc)
- Response wraps list with `totalPages`, `totalElements`, `currentPage`

## Stock Management
- Decrease stock on order creation
- Increase stock on order cancellation
- Return 400 if insufficient stock
