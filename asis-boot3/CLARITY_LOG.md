# CLARITY_LOG — Employee CRUD REST API (AS-IS Spring Boot 3)

## Spec Files Analyzed
- `specs/employee-crud-api.md` — Single spec covering entity, REST endpoints, auth, error handling, architecture, testing

---

## Round: 1

### Ambiguity 1
```
Spec: employee-crud-api.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: Should Employee.java be a Java record or a mutable class? The spec says "Entity with Java records or class" (line 67) — which one?
A: Use a mutable class for Employee.java; use records for DTOs (EmployeeRequest, EmployeeResponse, PageResponse). MyBatis's @Options(useGeneratedKeys=true) mutates the parameter object after INSERT to populate the generated id. Java records are immutable with final fields, making this mechanism fail. Additionally, createdAt/updatedAt are "auto-set" (lines 27-28), implying mutation after construction. The spec explicitly labels DTOs as "record" (lines 75-77) but hedges with "records or class" for the entity, signaling awareness of this tension. The spec also says "where appropriate" for Java 21 features (line 96).
Confidence: 0.95
Remaining_Ambiguity: None
Resolution: Employee.java is a plain class with private fields, getters/setters, no-arg constructor. EmployeeRequest, EmployeeResponse, PageResponse are Java records.
```
---

### Ambiguity 2
```
Spec: employee-crud-api.md
Category: UNSTATED_ASSUMPTION
Severity: MAJOR
Q: How should createdAt and updatedAt timestamps be managed? MyBatis lacks JPA's @PrePersist/@PreUpdate. Options: SQL defaults, service layer, MyBatis interceptors?
A: Set both timestamps at the application service layer. SQL DEFAULT CURRENT_TIMESTAMP is insufficient for updatedAt on UPDATE (no portable auto-update mechanism across PostgreSQL and H2). MyBatis interceptors are heavy machinery not mentioned in the spec. Service-layer timestamps are explicit, testable, and portable: before insert, set both createdAt and updatedAt; before update, set only updatedAt.
Confidence: 0.95
Remaining_Ambiguity: None
Resolution: EmployeeService sets createdAt + updatedAt before mapper.insert(), and only updatedAt before mapper.update(). The @Insert annotation includes both columns explicitly. DDL may still declare DEFAULT CURRENT_TIMESTAMP as a safety net but the app does not rely on it.
```
---

### Ambiguity 3
```
Spec: employee-crud-api.md
Category: INTEGRATION_GAP
Severity: MAJOR
Q: The spec says PostgreSQL for production (line 11) but H2 for tests (line 101). What DDL syntax in schema.sql works for both?
A: Use SQL-standard syntax compatible with both H2 2.x and PostgreSQL 10+:
  - Auto-increment: BIGINT GENERATED ALWAYS AS IDENTITY (not SERIAL, not AUTO_INCREMENT)
  - Timestamp defaults: DEFAULT CURRENT_TIMESTAMP (not NOW())
  - String types: VARCHAR(n)
  - Decimal: DECIMAL(10,2)
  - Date: DATE for hireDate, TIMESTAMP for createdAt/updatedAt
  - Column naming: snake_case (hire_date, created_at) with mybatis.configuration.map-underscore-to-camel-case=true
  - H2 test URL: jdbc:h2:mem:testdb;MODE=PostgreSQL;DB_CLOSE_DELAY=-1
Confidence: 0.95
Remaining_Ambiguity: None
Resolution: Use the DDL pattern above. Configure map-underscore-to-camel-case=true in application.yml. Use H2 MODE=PostgreSQL in test profile.
```
---

### Ambiguity 4
```
Spec: employee-crud-api.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: The search endpoint says "Search by name/dept" (line 37). Is filtering AND or OR? Partial or exact match? Case sensitive?
A: AND logic, case-insensitive partial match (LIKE), both parameters optional. "Search" implies fuzzy matching (not "filter" or "find exact"). AND is the standard REST API filtering convention — filters narrow results. Both name and department are optional query params; if only one is provided, filter by that alone. Implementation uses LOWER() on both sides for case-insensitivity (ILIKE is PostgreSQL-only, not H2-compatible).
Confidence: 0.90
Remaining_Ambiguity: None
Resolution: GET /api/employees/search?name=john&department=eng&page=0&size=10. Both params optional, AND logic, case-insensitive LIKE partial match. This is the "complex query" that belongs in XML (MyBatis <if> tags for optional WHERE clauses).
```
---

### Ambiguity 5
```
Spec: employee-crud-api.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: Does PUT /api/employees/{id} use full replacement or partial update semantics? Can id, createdAt, updatedAt be changed by the client?
A: Full replacement. PUT is full replacement per RFC 9110. The spec chose PUT (not PATCH). A single EmployeeRequest DTO is used for both POST and PUT (line 75-76), meaning the same validation constraints apply — all fields mandatory. The id comes from the URL path, not the body. createdAt is immutable (auto-set on insert only). updatedAt is system-managed.
Confidence: 0.95
Remaining_Ambiguity: None
Resolution: PUT requires all mutable fields (name, email, department, salary, hireDate) in the request body. EmployeeRequest does not contain id, createdAt, or updatedAt. Validation rules identical to POST.
```
---

### Ambiguity 6
```
Spec: employee-crud-api.md
Category: MISSING_ERROR_HANDLING
Severity: MAJOR
Q: What HTTP status does DELETE return on success? What if the employee doesn't exist?
A: 204 No Content on success; 404 if employee not found. 204 is the REST convention for DELETE when there's no meaningful body to return. The spec lists 404 as a standard error (line 53) and defines EmployeeNotFoundException (line 79), indicating 404 is expected for missing resources across all operations. The service checks existence before deletion.
Confidence: 0.95
Remaining_Ambiguity: None
Resolution: DELETE returns 204 No Content on success. If employee not found, throw EmployeeNotFoundException which GlobalExceptionHandler maps to 404 ProblemDetail.
```
---

### Ambiguity 7
```
Spec: employee-crud-api.md
Category: UNSTATED_ASSUMPTION
Severity: MAJOR
Q: Does ADMIN role inherit USER role access? The spec assigns one role per user: admin→ADMIN, user→USER. If ADMIN doesn't inherit USER, the admin cannot list/search employees.
A: Yes, ADMIN inherits USER. An administrator must be able to view data they manage. The spec defines exactly two users with one role each (lines 46-47), so a hierarchy is assumed. Spring Security supports this via RoleHierarchyImpl.
Confidence: 0.90
Remaining_Ambiguity: None
Resolution: Define RoleHierarchy bean in SecurityConfig: RoleHierarchyImpl.fromHierarchy("ROLE_ADMIN > ROLE_USER"). The admin user is configured with role ADMIN only; the hierarchy grants implicit USER access.
```
---

### Ambiguity 8
```
Spec: employee-crud-api.md
Category: MISSING_ERROR_HANDLING
Severity: MAJOR
Q: Does the 409 duplicate email check apply only to POST (create), or also to PUT (update)?
A: Both. The spec says "409 for duplicate email" (line 54) in the general Error Handling section without scoping to a specific operation. DuplicateEmailException (line 80) is a dedicated exception for all cases. On UPDATE, the uniqueness check must exclude the current employee's own email (so submitting PUT with unchanged email doesn't falsely trigger 409).
Confidence: 0.95
Remaining_Ambiguity: None
Resolution: Service checks email uniqueness before both insert and update. For update: SELECT COUNT(*) FROM employees WHERE email = #{email} AND id != #{id}. For insert: SELECT COUNT(*) FROM employees WHERE email = #{email}. Also rely on DB UNIQUE constraint as a fallback safety net; catch DataIntegrityViolationException and translate to DuplicateEmailException.
```
---

### Ambiguity 9
```
Spec: employee-crud-api.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: Which MyBatis operations use annotations vs XML? The spec says "annotation + XML hybrid" and "XML for complex queries."
A: Annotations for all simple single-table CRUD (7 methods); XML for search + countSearch (2 methods). The search query has dynamic WHERE clauses with optional parameters requiring MyBatis <if> tags, which only work in XML. Simple operations: insert, findById, findAll (paginated), count, update, deleteById, findByEmail — all use @Select/@Insert/@Update/@Delete annotations.
Confidence: 0.95
Remaining_Ambiguity: None
Resolution: EmployeeMapper.java has 7 annotated methods. EmployeeMapper.xml defines search and countSearch with <where>/<if> dynamic SQL. Namespace must match the mapper interface fully qualified name.
```
---

### Ambiguity 10
```
Spec: employee-crud-api.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: What fields does PageResponse contain? Does the search endpoint also use pagination?
A: PageResponse<T> has 4 fields: content (List<T>), currentPage (int), totalPages (int), totalElements (long) — all explicitly named in the spec (line 41). Search also uses pagination for consistency and to prevent unbounded result sets. totalPages = ceil(totalElements / size).
Confidence: 0.95
Remaining_Ambiguity: None
Resolution: public record PageResponse<T>(List<T> content, int currentPage, int totalPages, long totalElements). Both GET /api/employees and GET /api/employees/search return PageResponse<EmployeeResponse>. Same page/size query params apply to search.
```
---

### Ambiguity 11
```
Spec: employee-crud-api.md
Category: UNSTATED_ASSUMPTION
Severity: MINOR
Q: What are the Maven artifact coordinates (groupId, artifactId, version)?
A: The spec shows the jar name as employee-api-1.0.0.jar (line 122) and the base package as com.example.employee (line 62). This gives us: groupId=com.example, artifactId=employee-api, version=1.0.0.
Confidence: 0.95
Remaining_Ambiguity: None
Resolution: groupId=com.example, artifactId=employee-api, version=1.0.0, package=com.example.employee.
```
---

### Ambiguity 12
```
Spec: employee-crud-api.md
Category: UNSTATED_ASSUMPTION
Severity: MINOR
Q: What port does the application run on?
A: Not specified. Spring Boot defaults to port 8080. No reason to override.
Confidence: 0.95
Remaining_Ambiguity: None
Resolution: Use Spring Boot default port 8080. No explicit server.port configuration needed.
```
---

### Ambiguity 13
```
Spec: employee-crud-api.md
Category: UNSTATED_ASSUMPTION
Severity: MINOR
Q: What precision/scale should BigDecimal salary use?
A: The spec says "BigDecimal, >= 0" (line 24). For salary, DECIMAL(10,2) is industry standard — up to 99,999,999.99 with 2 decimal places.
Confidence: 0.90
Remaining_Ambiguity: None
Resolution: DDL uses DECIMAL(10,2). Validation: @DecimalMin("0") on EmployeeRequest salary field.
```
---

### Ambiguity 14
```
Spec: employee-crud-api.md
Category: EDGE_CASE
Severity: MINOR
Q: Can hireDate be in the future? The spec says "NOT NULL" but no temporal constraint.
A: No constraint is specified, so allow any valid LocalDate. This is a legacy AS-IS system — adding unspecified constraints would be over-engineering.
Confidence: 0.90
Remaining_Ambiguity: None
Resolution: hireDate is validated only as @NotNull. No past/future constraint. Use @JsonFormat or rely on Spring's default LocalDate deserialization (ISO 8601: yyyy-MM-dd).
```
---

### Ambiguity 15
```
Spec: employee-crud-api.md
Category: UNSTATED_ASSUMPTION
Severity: MINOR
Q: What URI should ProblemDetail's "type" field contain?
A: The spec shows the ProblemDetail structure (line 57) with "type": "..." placeholder. RFC 7807 specifies "about:blank" as the default type URI when no specific problem type URI is defined.
Confidence: 0.90
Remaining_Ambiguity: None
Resolution: Use "about:blank" for the type field (RFC 7807 default). Spring's ProblemDetail uses this by default when no custom type is set.
```
---

### Ambiguity 16
```
Spec: employee-crud-api.md
Category: UNSTATED_ASSUMPTION
Severity: MINOR
Q: What should the 5 sample employees in data.sql contain?
A: The spec says "seed data (5 sample employees)" (line 93) without specifying content. Create varied, realistic test data spanning different departments and salary ranges.
Confidence: 0.95
Remaining_Ambiguity: None
Resolution: Create 5 employees with varied names, unique emails, different departments (Engineering, Marketing, HR, Finance, Sales), salaries ranging from 45000.00 to 95000.00, and different hire dates.
```
---

### Ambiguity 17
```
Spec: employee-crud-api.md
Category: UNSTATED_ASSUMPTION
Severity: MINOR
Q: What email validation is expected? Strict RFC 5322 or basic format check?
A: The spec says "valid email" (line 21) and uses jakarta.validation (line 98). The standard approach is @Email annotation from jakarta.validation, which performs a reasonable format check without being overly strict.
Confidence: 0.95
Remaining_Ambiguity: None
Resolution: Use @Email annotation from jakarta.validation.constraints on the email field in EmployeeRequest. This validates basic email format (contains @, has domain part).
```
---

### Ambiguity 18
```
Spec: employee-crud-api.md
Category: MISSING_ERROR_HANDLING
Severity: MINOR
Q: How should unhandled 500 Internal Server Errors be treated? The spec lists 400, 401, 403, 404, 409 but not 500.
A: GlobalExceptionHandler (line 81) should include a catch-all for unexpected exceptions, returning a 500 ProblemDetail without leaking internal details. This is standard defensive error handling.
Confidence: 0.90
Remaining_Ambiguity: None
Resolution: GlobalExceptionHandler includes a catch-all @ExceptionHandler(Exception.class) that returns 500 ProblemDetail with a generic "Internal Server Error" message. Stack traces are logged but not exposed in the response.
```
---

## Cross-Spec Consistency Check

Only one spec file exists (`employee-crud-api.md`), so there are no cross-spec contradictions or integration gaps. Internal consistency issues found and resolved:

1. **PostgreSQL vs H2**: Spec requires PostgreSQL (line 11) for production but H2 for tests (line 101). Resolved via SQL-standard DDL syntax compatible with both (Ambiguity 3).
2. **Record vs Class**: Spec encourages Java 21 records (line 96) but MyBatis needs mutable objects. Resolved by using class for entity, records for DTOs (Ambiguity 1).
3. **Timestamp management**: Spec says "auto-set" for createdAt/updatedAt but MyBatis has no auto-timestamp mechanism. Resolved via service-layer timestamps (Ambiguity 2).

No contradictions remain. All integration points are addressed.

---

## Ambiguity Score

```
AMBIGUITY_SCORE: 0.00
Rounds_Completed: 1
Ambiguities_Found: 18
Ambiguities_Resolved: 18
Ambiguities_Remaining: 0
```

## Convergence Data

```
CONVERGENCE_DATA:
  round: 1
  score: 0.00
  prev_score: 1.0
  delta: -1.0
  category_distribution:
    CRITICAL: 0
    MAJOR: 0
    MINOR: 0
  stagnation_count: 0
```

---

PHASE_0_COMPLETE
FINAL_AMBIGUITY_SCORE: 0.00
TOTAL_ROUNDS: 1
EXIT_REASON: THRESHOLD
