# Implementation Plan
Generated: 2026-03-19T00:00:00Z
Total_Items: 19
Completed: 15
Test_Items: 9 (target: ≥70% of implementation items → 9/11 = 82%)

## Dependency Graph
```
Independent_Groups:
  - group_1: [Item 1, Item 2, Item 3]                         # models, DTOs, schema — no dependencies
  - group_2: [Item 4, Item 5, Item 6, Item 7, Item 8]         # config, mapper, validator, test infra — depends on group_1
  - group_3: [Item 9, Item 10, Item 11, Item 12, Item 13, Item 14]  # service, exception handler, early tests — depends on group_2
  - group_4: [Item 15, Item 16]                                # service tests, controller — depends on group_3
  - group_5: [Item 17, Item 18, Item 19]                       # controller integration tests — depends on group_4
Build_Order: group_1 → group_2 → group_3 → group_4 → group_5
```

---

## Item 1: Employee model class
- status: DONE
- priority: P0
- complexity: S
- depends_on: []
- spec: specs/employee-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1 (R1.9 date format, R1.20 timestamp format)
- description: Create the Employee entity in `com.example.legacy.model` with fields: id (Long), name (String), email (String), department (String), salary (BigDecimal), hireDate (Date), createdAt (Timestamp), updatedAt (Timestamp). Add Jackson annotations for date serialization — hireDate as "yyyy-MM-dd", timestamps as "yyyy-MM-dd'T'HH:mm:ss". Standard getters/setters, Java 1.8 style.
- acceptance: Class compiles. Fields match spec types. Jackson annotations produce correct date formats when serialized.
- tests: Covered by Item 11 (Model & DTO unit tests)

## Item 2: Request/Response DTOs
- status: DONE
- priority: P0
- complexity: S
- depends_on: []
- spec: specs/employee-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1 (R1.3 fieldErrors, R1.13 email validation, R1.20 error timestamp)
- description: Create EmployeeRequest DTO in `com.example.legacy.dto` with javax.validation annotations — name (@NotBlank, @Size max=100), email (@NotBlank, @Email), department (@NotBlank, @Size max=50), salary (@NotNull, @DecimalMin("0")), hireDate (@NotNull). Create ErrorResponse DTO with fields: status (int), message (String), timestamp (String, ISO 8601), fieldErrors (List of FieldError inner class with field + message).
- acceptance: Classes compile. Validation annotations are present and correct. ErrorResponse includes fieldErrors list.
- tests: Covered by Item 11 (Model & DTO unit tests)

## Item 3: Database schema and test resources
- status: DONE
- priority: P0
- complexity: S
- depends_on: []
- spec: specs/employee-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1 (R1.11 H2 compatibility, R1.12 test profile)
- description: Create `src/main/resources/schema.sql` with PostgreSQL-compatible DDL for the employees table (id BIGSERIAL PK, name VARCHAR(100) NOT NULL, email VARCHAR(255) NOT NULL UNIQUE, department VARCHAR(50) NOT NULL, salary DECIMAL(19,2) NOT NULL CHECK >= 0, hire_date DATE NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP). Create `src/test/resources/schema.sql` (H2-compatible version) and `src/test/resources/application-test.properties` with H2 MODE=PostgreSQL config.
- acceptance: Schema files exist. H2 test schema uses compatible syntax (BIGINT AUTO_INCREMENT instead of BIGSERIAL). Test properties configure H2 with PostgreSQL mode.
- tests: Validated indirectly by Item 12 (EmployeeMapper integration tests use H2)

## Item 4: Spring application and database configuration
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 1, Item 3]
- spec: specs/employee-crud-api.md
- description: Create AppConfig (@Configuration, @ComponentScan for com.example.legacy, @PropertySource) and DatabaseConfig (@Configuration with DataSource bean using Commons DBCP2, PlatformTransactionManager, SqlSessionFactoryBean with mapper locations and type aliases, MapperScannerConfigurer for com.example.legacy.mapper). Both in `com.example.legacy.config`. Production properties in `src/main/resources/application.properties` with PostgreSQL defaults.
- acceptance: Compiles. AppConfig scans all packages. DatabaseConfig creates DataSource, SqlSessionFactory with Employee type alias, and MapperScannerConfigurer targeting mapper package. Transaction manager configured.
- tests: Validated indirectly by integration tests (Items 12, 17-19)

## Item 5: Security configuration
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 1]
- spec: specs/employee-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1 (R1.14 stateless, R1.15 auth entry point, R1.16 role-based access)
- description: Create SecurityConfig in `com.example.legacy.config` extending WebSecurityConfigurerAdapter. Configure HTTP Basic auth, stateless session (SessionCreationPolicy.STATELESS), CSRF disabled. In-memory users: admin/admin123 with ADMIN role, user/user123 with USER role. URL patterns: POST/PUT/DELETE /api/employees/** require ADMIN, GET /api/employees/** require USER or ADMIN. Return 401 JSON for unauthenticated, 403 JSON for unauthorized (custom AuthenticationEntryPoint and AccessDeniedHandler).
- acceptance: Compiles. Admin can access all endpoints. User can only GET. Unauthenticated requests get 401. User attempting POST/PUT/DELETE gets 403. Responses are JSON ErrorResponse format.
- tests: Covered by Item 14 (Security integration tests) and Item 19

## Item 6: EmployeeMapper interface and MyBatis XML
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 1, Item 3]
- spec: specs/employee-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1 (R1.1 search, R1.5 pagination, R1.19 email uniqueness check)
- description: Create EmployeeMapper interface in `com.example.legacy.mapper` with methods: findAll(offset, limit), findById(id), insert(employee) with useGeneratedKeys, update(employee), delete(id), countAll(), searchByNameOrDepartment(name, department, offset, limit), countBySearch(name, department), findByEmail(email). Create corresponding `src/main/resources/mappers/EmployeeMapper.xml` with SQL using #{} parameters. Search uses case-insensitive LIKE with OR logic. Pagination via LIMIT/OFFSET.
- acceptance: Compiles. XML mapper has all 9 SQL statements. Insert uses useGeneratedKeys="true" keyProperty="id". Search SQL uses LOWER() with LIKE for case-insensitive matching. OR logic between name and department filters.
- tests: Covered by Item 12 (EmployeeMapper integration tests)

## Item 7: EmployeeValidator
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 1, Item 2]
- spec: specs/employee-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1 (R1.19 duplicate email on update excludes self)
- description: Create EmployeeValidator in `com.example.legacy.validation`. Provides business validation beyond annotation-based checks: duplicate email detection on create (findByEmail, if exists → 409), duplicate email detection on update (findByEmail, if exists AND id != current → 409). Takes EmployeeMapper dependency for email lookups.
- acceptance: Compiles. Throws appropriate exception for duplicate email on create. Throws exception for duplicate email on update only when email belongs to a different employee.
- tests: Covered by Item 13 (EmployeeValidator unit tests)

## Item 8: Test infrastructure
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 3, Item 4]
- spec: specs/employee-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1 (R1.12 test profile)
- description: Create TestAppConfig in test sources that configures H2 DataSource (MODE=PostgreSQL), SqlSessionFactory, MapperScannerConfigurer, and TransactionManager for test profile. Optionally create a base integration test class with @RunWith(SpringJUnit4ClassRunner.class), @ContextConfiguration, @ActiveProfiles("test"), @Transactional annotations to reduce boilerplate. Ensure H2 schema.sql is loaded automatically.
- acceptance: Test config compiles. H2 datasource connects in PostgreSQL mode. Schema.sql creates employees table in H2. Transactions roll back after each test.
- tests: Validated by all integration test items (12, 14, 17-19)

## Item 9: EmployeeService interface and implementation
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 6, Item 7]
- spec: specs/employee-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1 (R1.4 PUT semantics, R1.5 PageResult, R1.18 search validation)
- description: Create EmployeeService interface and EmployeeServiceImpl (@Service, @Transactional) in `com.example.legacy.service`. Methods: getAllEmployees(page, size) returns PageResult<Employee>, getEmployeeById(id) returns Employee or throws not-found exception, createEmployee(EmployeeRequest) validates uniqueness via EmployeeValidator then inserts and returns Employee, updateEmployee(id, EmployeeRequest) checks existence (404 if not) then validates email uniqueness excluding self then full-replaces all fields, deleteEmployee(id) checks existence (404 if not) then deletes, searchEmployees(name, department, page, size) requires at least one param (400 if both null) and returns PageResult. Pagination: page is 0-based, default size=10.
- acceptance: Compiles. All six methods implemented. Not-found throws exception with 404 semantics. Duplicate email throws exception with 409 semantics. Search with no params throws exception with 400 semantics. PageResult correctly calculated (totalPages, totalElements, currentPage, content).
- tests: Covered by Item 15 (EmployeeService unit tests)

## Item 10: GlobalExceptionHandler
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 2]
- spec: specs/employee-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1 (R1.3 fieldErrors, R1.20 error timestamp)
- description: Create GlobalExceptionHandler in `com.example.legacy.controller` with @ControllerAdvice. Handle: MethodArgumentNotValidException → 400 with fieldErrors populated from BindingResult, custom NotFoundException → 404, custom DuplicateEmailException → 409, custom BadRequestException → 400, generic Exception → 500. All responses use ErrorResponse DTO with ISO 8601 timestamp. Define custom exception classes in a new `com.example.legacy.exception` package (or inline in service).
- acceptance: Compiles. Each exception type maps to correct HTTP status. Validation errors include field-level details. All error responses are JSON with status, message, timestamp fields.
- tests: Covered by Item 16 (GlobalExceptionHandler test)

## Item 11: Model and DTO unit tests
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 1, Item 2, Item 8]
- spec: specs/employee-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1 (R1.9, R1.13, R1.20)
- description: Write JUnit 4 tests for Employee model (Jackson date serialization — hireDate as yyyy-MM-dd, timestamps as yyyy-MM-dd'T'HH:mm:ss), EmployeeRequest (javax.validation annotation tests — valid input passes, blank name fails, invalid email fails, negative salary fails, null hireDate fails), ErrorResponse (fieldErrors list construction and serialization).
- acceptance: All tests pass. Tests verify date format output matches spec. Tests verify each validation constraint. Tests verify ErrorResponse JSON structure.
- tests: This IS a test item

## Item 12: EmployeeMapper integration tests
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 6, Item 8]
- spec: specs/employee-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1 (R1.1, R1.5, R1.19)
- description: Write JUnit 4 integration tests using H2 for all EmployeeMapper methods: insert returns generated id, findById returns correct employee, findAll with offset/limit paginates correctly, update modifies all fields, delete removes record, countAll returns correct count, searchByNameOrDepartment with name-only/department-only/both finds correct results (case-insensitive), findByEmail returns employee or null.
- acceptance: All tests pass against H2. Each mapper method tested with at least one positive and one negative case. Search tests verify case-insensitivity and OR logic.
- tests: This IS a test item

## Item 13: EmployeeValidator unit tests
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 7, Item 8]
- spec: specs/employee-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1 (R1.19)
- description: Write JUnit 4 unit tests for EmployeeValidator using Mockito to mock EmployeeMapper. Test cases: create with unique email succeeds, create with duplicate email throws 409 exception, update with same email (own) succeeds, update with email belonging to different employee throws 409 exception, update with unique new email succeeds.
- acceptance: All tests pass. Mockito verifies findByEmail is called. Both create and update paths tested for duplicate detection.
- tests: This IS a test item

## Item 14: Security integration tests
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 5, Item 8]
- spec: specs/employee-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1 (R1.14, R1.15, R1.16)
- description: Write JUnit 4 integration tests for SecurityConfig using Spring MockMvc with spring-security-test. Test: unauthenticated GET returns 401, user can GET /api/employees, user POST /api/employees returns 403, admin can POST /api/employees, response bodies are JSON ErrorResponse format for 401/403.
- acceptance: All tests pass. Role-based access control verified for each HTTP method. Error responses are well-formed JSON.
- tests: This IS a test item

## Item 15: EmployeeService unit tests
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 9]
- spec: specs/employee-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1 (R1.4, R1.5, R1.18)
- description: Write JUnit 4 unit tests with Mockito for all EmployeeServiceImpl methods. Mock EmployeeMapper and EmployeeValidator. Tests: getAllEmployees returns correct PageResult with calculated totalPages, getEmployeeById returns employee / throws not-found, createEmployee calls validator then inserts then returns with generated id, updateEmployee checks existence / validates / full-replaces, deleteEmployee checks existence / deletes, searchEmployees with no params throws 400, searchEmployees with params returns correct PageResult.
- acceptance: All tests pass. Each service method has at least 2 test cases (happy + error path). PageResult calculation verified (totalPages = ceil(totalElements/size)).
- tests: This IS a test item

## Item 16: EmployeeController
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 9, Item 10]
- spec: specs/employee-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1 (R1.4, R1.5, R1.6, R1.7, R1.8, R1.18)
- description: Create EmployeeController in `com.example.legacy.controller` with @RestController @RequestMapping("/api/employees"). Endpoints: GET "/" with @RequestParam page (default 0) and size (default 10) → 200 + PageResult, GET "/{id}" → 200 + Employee, POST "/" with @Valid @RequestBody EmployeeRequest → 201 + Employee + Location header, PUT "/{id}" with @Valid @RequestBody EmployeeRequest → 200 + Employee, DELETE "/{id}" → 204 no body, GET "/search" with @RequestParam name (optional) and department (optional) plus page/size → 200 + PageResult. Inject EmployeeService.
- acceptance: Compiles. All six endpoints mapped to correct HTTP methods and paths. POST returns 201 with Location header containing /api/employees/{id}. DELETE returns 204. @Valid triggers annotation-based validation before method body.
- tests: Covered by Items 17, 18, 19

## Item 17: Controller integration tests — CRUD operations
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 16, Item 8]
- spec: specs/employee-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1 (R1.6, R1.7, R1.8)
- description: Write JUnit 4 integration tests using MockMvc with full Spring context (WebApplicationContext) and spring-security-test for admin auth. Tests: POST creates employee and returns 201 with Location header and full body, GET by id returns 200 with correct employee, GET all returns 200 with PageResult structure, PUT updates all fields and returns 200, DELETE returns 204, GET after DELETE returns 404, POST with duplicate email returns 409.
- acceptance: All tests pass. Response status codes match spec. POST Location header format is /api/employees/{id}. PUT response contains updated values. PageResult JSON has content, totalPages, totalElements, currentPage.
- tests: This IS a test item

## Item 18: Controller integration tests — Search and pagination
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 16, Item 8]
- spec: specs/employee-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1 (R1.1, R1.5, R1.18)
- description: Write JUnit 4 integration tests for search and pagination. Tests: GET /search?name=X returns matching employees (case-insensitive), GET /search?department=Y returns matching, GET /search?name=X&department=Y returns OR-matched results, GET /search with no params returns 400, GET /api/employees?page=0&size=2 returns first page with correct totalPages, GET /api/employees?page=1&size=2 returns second page, empty result returns PageResult with empty content and totalElements=0.
- acceptance: All tests pass. Search is case-insensitive. OR logic verified. Pagination math correct (totalPages = ceil(total/size)). Empty results handled gracefully.
- tests: This IS a test item

## Item 19: Controller integration tests — Authentication and error handling
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 16, Item 8]
- spec: specs/employee-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1 (R1.3, R1.15, R1.16)
- description: Write JUnit 4 integration tests for auth and validation errors. Tests: POST with invalid body (blank name, bad email, negative salary) returns 400 with fieldErrors in response, PUT non-existent id returns 404, DELETE non-existent id returns 404, user role POST returns 403, unauthenticated GET returns 401, all error responses contain status + message + timestamp fields, validation error response contains fieldErrors array with field and message for each violation.
- acceptance: All tests pass. Validation error response has fieldErrors list with correct field names. Auth errors return JSON (not default Spring HTML). Error timestamp is ISO 8601 format.
- tests: This IS a test item

---

## Summary

| Group | Items | Priority | Can Parallel |
|-------|-------|----------|-------------|
| 1 | 1, 2, 3 | P0 | Yes (3 items) |
| 2 | 4, 5, 6, 7, 8 | P0 | Yes (5 items) |
| 3 | 9, 10, 11, 12, 13, 14 | P0 | Yes (6 items) |
| 4 | 15, 16 | P1 | Yes (2 items) |
| 5 | 17, 18, 19 | P1 | Yes (3 items) |

**Implementation items:** 1–10, 16 = 11
**Test items:** 11–15, 17–19 = 9 (82% of implementation items)

PHASE_1_COMPLETE
