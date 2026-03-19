# Employee CRUD REST API — AS-IS Spring 4 Legacy Stack

## Overview
A traditional Spring MVC REST API for employee management.
This is an **AS-IS legacy project** to be used as migration tool input.

- **Java 1.8** (source/target compatibility 1.8)
- **Spring Framework 4.3.4.RELEASE** (NOT Spring Boot — uses XML/Java config)
- **Spring Security 4.2.4.RELEASE** (form-based + basic auth)
- **MyBatis 3.2.2** (XML mapper files)
- **PostgreSQL** (JDBC via commons-dbcp2 connection pool)
- **Maven** build system
- **Embedded Tomcat 8.5** for integration tests (maven-tomcat7-plugin or embedded server)
- **JUnit 4** + Mockito for testing

## Functional Requirements

### Entity: Employee
| Field       | Type      | Constraints                       |
|-------------|-----------|-----------------------------------|
| id          | Long      | PK, auto-increment                |
| name        | String    | NOT NULL, 1–100 chars             |
| email       | String    | NOT NULL, unique, valid email     |
| department  | String    | NOT NULL, 1–50 chars              |
| salary      | BigDecimal| NOT NULL, >= 0                    |
| hireDate    | Date      | NOT NULL                          |
| createdAt   | Timestamp | auto-set on insert                |
| updatedAt   | Timestamp | auto-set on insert/update         |

### REST Endpoints
| Method | Path                   | Description           | Auth Required |
|--------|------------------------|-----------------------|---------------|
| GET    | /api/employees         | List all (paginated)  | USER role     |
| GET    | /api/employees/{id}    | Get by ID             | USER role     |
| POST   | /api/employees         | Create new            | ADMIN role    |
| PUT    | /api/employees/{id}    | Update existing       | ADMIN role    |
| DELETE | /api/employees/{id}    | Delete                | ADMIN role    |
| GET    | /api/employees/search  | Search by name/dept   | USER role     |

### Pagination
- Query params: `page` (0-based), `size` (default 10, max 100)
- Response wraps list with `totalPages`, `totalElements`, `currentPage`

### Authentication & Authorization
- Spring Security 4.2.4 with HTTP Basic Auth for API endpoints
- In-memory user store (for demo purposes):
  - `admin` / `admin123` → role ADMIN
  - `user` / `user123` → role USER
- CSRF disabled for REST API
- Stateless session (no cookies)

### Error Handling
- 400 for validation errors (with field-level detail)
- 404 for not-found
- 409 for duplicate email
- 401/403 for auth failures
- Standard error response: `{ "status": 400, "error": "Bad Request", "message": "...", "timestamp": "..." }`

## Architecture

```
com.example.legacy/
├── config/
│   ├── AppConfig.java          # Root Spring config (component scan, property source)
│   ├── WebConfig.java          # Spring MVC config (message converters, CORS)
│   ├── SecurityConfig.java     # Spring Security config
│   ├── DatabaseConfig.java     # DataSource + SqlSessionFactory + Transaction
│   └── WebInitializer.java     # AbstractAnnotationConfigDispatcherServletInitializer
├── model/
│   ├── Employee.java           # Entity POJO
│   └── PageResult.java         # Pagination wrapper
├── mapper/
│   └── EmployeeMapper.java     # MyBatis mapper interface
├── service/
│   ├── EmployeeService.java    # Interface
│   └── EmployeeServiceImpl.java # Implementation
├── controller/
│   ├── EmployeeController.java # REST controller
│   └── GlobalExceptionHandler.java # @ControllerAdvice
├── dto/
│   ├── EmployeeRequest.java    # Input DTO with validation
│   └── ErrorResponse.java      # Error response DTO
└── validation/
    └── EmployeeValidator.java  # Manual bean validation (javax.validation)
```

### MyBatis XML Mappers
`src/main/resources/mapper/EmployeeMapper.xml` — all SQL in XML:
- `findAll` with LIMIT/OFFSET
- `findById`
- `insert` with `useGeneratedKeys`
- `update`
- `delete`
- `countAll`
- `searchByNameOrDepartment` with LIKE
- `findByEmail`

### Configuration Files
- `src/main/resources/application.properties` — DB connection, MyBatis settings
- `src/main/resources/schema.sql` — DDL for employees table
- `src/main/resources/data.sql` — seed data (5 sample employees)
- `src/main/webapp/WEB-INF/web.xml` — (optional, since using Java config)

## Non-Functional Requirements
- **Java 1.8 compatible** — no lambdas only if absolutely needed, prefer anonymous classes where possible for legacy feel, but lambdas are OK since Java 8 supports them
- All dependencies managed in `pom.xml` with explicit versions
- No Spring Boot auto-configuration — everything manually configured
- Log with SLF4J + Logback
- Unit tests with JUnit 4 + Mockito
- Integration tests using Spring Test with H2 in-memory DB (test profile)

## Testing Requirements
- `tests/` mapped to `src/test/java/com/example/legacy/`
- Unit tests for Service layer (mock mapper)
- Unit tests for Controller layer (MockMvc)
- Integration tests with Spring TestContext + H2
- Target: at least 15 test methods across test classes

## Build & Run
```bash
# Build
mvn clean compile

# Test (uses H2 in-memory)
mvn test

# Package
mvn clean package

# Run with embedded Tomcat (if configured) or deploy WAR to Tomcat
mvn tomcat7:run    # or use exec-maven-plugin with embedded server
```
