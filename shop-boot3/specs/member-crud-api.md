# Member CRUD REST API

## Entity: Member
| Field       | Type      | Constraints                          |
|-------------|-----------|--------------------------------------|
| id          | Long      | PK, auto-increment                   |
| email       | String    | NOT NULL, unique, valid email        |
| password    | String    | NOT NULL, min 8 chars (BCrypt hash)  |
| name        | String    | NOT NULL, 1–50 chars                 |
| phone       | String    | nullable, 10–15 chars                |
| address     | String    | nullable, max 200 chars              |
| role        | Enum      | USER / ADMIN, default USER           |
| createdAt   | Timestamp | auto-set on insert                   |
| updatedAt   | Timestamp | auto-set on insert/update            |

## REST Endpoints
| Method | Path                    | Description        | Auth Required   |
|--------|-------------------------|--------------------|-----------------|
| POST   | /api/members            | Register new       | None            |
| POST   | /api/members/login      | Login (returns JWT or session) | None  |
| GET    | /api/members/me         | Get my profile     | USER            |
| PUT    | /api/members/me         | Update my profile  | USER            |
| DELETE | /api/members/me         | Deactivate account | USER            |
| GET    | /api/members            | List all (paginated)| ADMIN          |
| GET    | /api/members/{id}       | Get by ID          | ADMIN           |

## Password Handling
- Store BCrypt-hashed passwords (Spring Security PasswordEncoder)
- Never return password in any response
- Login returns HTTP Basic credentials acceptance (stateless, same as employee example)

## Validation
- Email: valid format, unique (409 on duplicate)
- Password: min 8 chars
- Name: 1–50 chars, not blank
