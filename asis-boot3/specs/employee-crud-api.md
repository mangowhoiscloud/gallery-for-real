# Employee CRUD REST API — AS-IS Spring Boot 3 Stack

## Overview
A Spring Boot REST API for employee management.
This is an **AS-IS legacy project** to be used as migration tool input.

- **Java 21** (source/target 21, virtual threads enabled)
- **Spring Boot 3.3.7** (auto-configuration, embedded Tomcat)
- **Spring Security 6.x** (bundled with Boot 3.3.7, HTTP Basic)
- **MyBatis Spring Boot Starter 3.0.4** (annotation + XML hybrid)
- **PostgreSQL** (HikariCP connection pool, auto-configured)
- **Maven** build system
- **JUnit 5** + Spring Boot Test for testing

## Functional Requirements

### Entity: Employee
| Field       | Type          | Constraints                       |
|-------------|---------------|-----------------------------------|
| id          | Long          | PK, auto-increment                |
| name        | String        | NOT NULL, 1–100 chars             |
| email       | String        | NOT NULL, unique, valid email     |
| department  | String        | NOT NULL, 1–50 chars              |
| salary      | BigDecimal    | NOT NULL, >= 0                    |
| hireDate    | LocalDate     | NOT NULL                          |
| createdAt   | LocalDateTime | auto-set on insert                |
| updatedAt   | LocalDateTime | auto-set on insert/update         |

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
- Spring Security 6.x with HTTP Basic Auth
- In-memory user store (for demo):
  - `admin` / `admin123` → role ADMIN
  - `user` / `user123` → role USER
- CSRF disabled for REST API
- Stateless session management

### Error Handling
- 400 for validation errors (with field-level detail via `@Valid`)
- 404 for not-found
- 409 for duplicate email
- 401/403 for auth failures
- Standard error response using `ProblemDetail` (RFC 7807):
  `{ "type": "...", "title": "Bad Request", "status": 400, "detail": "...", "instance": "..." }`

## Architecture

```
com.example.employee/
├── EmployeeApplication.java        # @SpringBootApplication main class
├── config/
│   └── SecurityConfig.java         # SecurityFilterChain bean
├── model/
│   └── Employee.java               # Entity with Java records or class
├── mapper/
│   └── EmployeeMapper.java         # MyBatis @Mapper with annotations + XML fallback
├── service/
│   └── EmployeeService.java        # Service class
├── controller/
│   └── EmployeeController.java     # @RestController
├── dto/
│   ├── EmployeeRequest.java        # record with jakarta.validation
│   ├── EmployeeResponse.java       # record for API response
│   └── PageResponse.java           # Generic pagination wrapper record
└── exception/
    ├── EmployeeNotFoundException.java
    ├── DuplicateEmailException.java
    └── GlobalExceptionHandler.java  # @RestControllerAdvice with ProblemDetail
```

### MyBatis Configuration
- `mybatis-spring-boot-starter 3.0.4` auto-configures SqlSessionFactory
- `src/main/resources/mapper/EmployeeMapper.xml` for complex queries
- Simple CRUD uses `@Select`, `@Insert`, `@Update`, `@Delete` annotations
- `@Options(useGeneratedKeys = true)` for auto-increment

### Configuration Files
- `src/main/resources/application.yml` — datasource, mybatis, server config
- `src/main/resources/schema.sql` — DDL for employees table
- `src/main/resources/data.sql` — seed data (5 sample employees)

## Non-Functional Requirements
- **Java 21 features**: records, text blocks, pattern matching, sealed classes where appropriate
- Spring Boot auto-configuration — minimal explicit config
- `jakarta.validation` for bean validation (not `javax`)
- Log with SLF4J (Spring Boot default Logback)
- Unit tests with JUnit 5 + Mockito
- Integration tests with `@SpringBootTest` + H2 in-memory DB
- Virtual threads enabled via `spring.threads.virtual.enabled=true`

## Testing Requirements
- Unit tests for Service layer (mock mapper with `@MockitoExtension`)
- Unit tests for Controller layer (`@WebMvcTest` + `MockMvc`)
- Integration tests with `@SpringBootTest` + `@AutoConfigureMockMvc` + H2
- Target: at least 15 test methods across test classes

## Build & Run
```bash
# Build
mvn clean compile

# Test (uses H2 in-memory)
mvn test

# Package
mvn clean package

# Run
java -jar target/employee-api-1.0.0.jar
# or
mvn spring-boot:run
```
