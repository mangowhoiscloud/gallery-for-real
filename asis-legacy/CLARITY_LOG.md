# CLARITY_LOG — Phase 0: Socratic Reasoning

## Spec Files Analyzed
- `specs/employee-crud-api.md` — Employee CRUD REST API (AS-IS Spring 4 Legacy)

---

## Round 1

### R1.1 — Search Endpoint Query Parameters
```
Round: 1
Spec: employee-crud-api.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: CRITICAL
Q: The search endpoint GET /api/employees/search says "Search by name/dept" but does not specify query parameter names. What are the parameter names? Is the search an AND or OR operation? Is the search case-sensitive?
A: The MyBatis mapper section lists `searchByNameOrDepartment` with LIKE, which implies OR logic between name and department. The most conventional REST parameter names for this pattern would be `name` and `department` as separate optional query params, with OR logic (match either). LIKE implies case-sensitive by default in PostgreSQL, but since tests use H2 which has case-insensitive LIKE by default, there's a behavioral gap. For a legacy system, case-insensitive search (using LOWER()) is the safer choice for cross-DB compatibility.
Confidence: 0.8
Remaining_Ambiguity: Are both parameters optional individually (i.e., can you search by name only, department only, or both)?
Resolution: Use query params `name` and `department`, both optional. OR logic: match if name LIKE %value% OR department LIKE %value%. Use case-insensitive matching (LOWER() in SQL). If neither param provided, return empty result or 400.
---
```

### R1.2 — Search Endpoint Pagination
```
Round: 1
Spec: employee-crud-api.md
Category: MISSING_ERROR_HANDLING
Severity: MAJOR
Q: Does the search endpoint support pagination? The spec defines pagination for the list endpoint but doesn't mention it for search.
A: Since search can potentially return many results, it should follow the same pagination pattern as the list endpoint for consistency. The PageResult wrapper is defined generically and can be reused.
Confidence: 0.85
Remaining_Ambiguity: None significant.
Resolution: Search endpoint supports the same pagination params (page, size) as the list endpoint. Uses the same PageResult wrapper response format.
---
```

### R1.3 — Validation Error Response Structure
```
Round: 1
Spec: employee-crud-api.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: CRITICAL
Q: The spec says 400 for validation errors "with field-level detail" but the error response format only shows { status, error, message, timestamp }. How are individual field errors represented?
A: The standard error response format needs extension for validation errors. Two common patterns: (a) a `fieldErrors` array with objects like { "field": "email", "message": "must be valid email" }, or (b) an `errors` map like { "email": "must be valid email" }. For a legacy Spring 4 app, pattern (a) with a list is more conventional and aligns with how MethodArgumentNotValidException is typically handled.
Confidence: 0.75
Remaining_Ambiguity: Exact field error structure.
Resolution: For validation errors (400), extend ErrorResponse with an additional `fieldErrors` field: a list of objects with `field` (String) and `message` (String). The top-level `message` for validation errors should be a generic "Validation failed". Example: { "status": 400, "error": "Bad Request", "message": "Validation failed", "timestamp": "...", "fieldErrors": [{ "field": "email", "message": "must be a valid email" }] }.
---
```

### R1.4 — PUT Semantics
```
Round: 1
Spec: employee-crud-api.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: CRITICAL
Q: Does PUT /api/employees/{id} perform a full replace or a partial update? Can individual fields be omitted in the request body?
A: Per HTTP semantics, PUT is a full replacement of the resource. The spec says "Update existing" which is generic. The spec also defines a single `EmployeeRequest` DTO for both create and update with all fields having NOT NULL constraints. A full replacement with the same validation as creation is the most consistent interpretation for a legacy REST API.
Confidence: 0.9
Remaining_Ambiguity: Should `id`, `createdAt`, `updatedAt` be accepted in the PUT body or ignored?
Resolution: PUT is a full replacement. All fields required by EmployeeRequest (name, email, department, salary, hireDate) must be provided. The `id` in the path takes precedence; `createdAt` is preserved from the original record; `updatedAt` is auto-set. If the employee doesn't exist, return 404 (not upsert).
---
```

### R1.5 — Pagination Response JSON Structure
```
Round: 1
Spec: employee-crud-api.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: The PageResult wrapper includes totalPages, totalElements, currentPage — but what key holds the actual list of employees?
A: The spec defines `PageResult.java` as a "Pagination wrapper" and mentions these three fields. The most conventional key for the data list in a Spring-style paginated response is `content` (mirroring Spring Data's Page interface). Since this is a legacy project mimicking Spring patterns, `content` is the natural choice.
Confidence: 0.9
Remaining_Ambiguity: None.
Resolution: PageResult JSON structure: { "content": [...employees...], "totalPages": N, "totalElements": N, "currentPage": N }. The `content` key holds the employee array.
---
```

### R1.6 — POST Response Code and Body
```
Round: 1
Spec: employee-crud-api.md
Category: MISSING_ERROR_HANDLING
Severity: MAJOR
Q: What HTTP status code and response body does POST /api/employees return on success? Does it include a Location header?
A: Standard REST practice for resource creation is 201 Created with the created resource in the body and a Location header pointing to the new resource URL. The spec says the mapper uses `useGeneratedKeys` which means the ID is available after insert.
Confidence: 0.9
Remaining_Ambiguity: None.
Resolution: POST returns 201 Created with the full Employee object in the response body (including generated id, createdAt, updatedAt). Include `Location` header: `/api/employees/{id}`.
---
```

### R1.7 — PUT Response Code and Body
```
Round: 1
Spec: employee-crud-api.md
Category: MISSING_ERROR_HANDLING
Severity: MAJOR
Q: What HTTP status code and response body does PUT /api/employees/{id} return on success?
A: Standard REST practice for update is 200 OK with the updated resource in the body.
Confidence: 0.95
Remaining_Ambiguity: None.
Resolution: PUT returns 200 OK with the full updated Employee object in the response body.
---
```

### R1.8 — DELETE Response Code and Body
```
Round: 1
Spec: employee-crud-api.md
Category: MISSING_ERROR_HANDLING
Severity: MAJOR
Q: What HTTP status code does DELETE /api/employees/{id} return? What happens when deleting a non-existent employee?
A: Two common patterns: 204 No Content (no body) or 200 OK with a message. For a legacy REST API, 204 No Content is the most standard approach. Deleting a non-existent ID should return 404.
Confidence: 0.9
Remaining_Ambiguity: None.
Resolution: DELETE returns 204 No Content on success (no response body). Returns 404 if the employee doesn't exist.
---
```

### R1.9 — Date/Timestamp JSON Serialization Format
```
Round: 1
Spec: employee-crud-api.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: What format should hireDate (Date) and createdAt/updatedAt (Timestamp) use in JSON serialization?
A: The pom.xml includes Jackson 2.9.x. By default, Jackson serializes java.util.Date as epoch milliseconds. For a REST API, ISO 8601 string format is far more practical. hireDate should be "yyyy-MM-dd" (date only), while createdAt/updatedAt should be "yyyy-MM-dd'T'HH:mm:ss" (datetime). This requires configuring Jackson's ObjectMapper in WebConfig.
Confidence: 0.85
Remaining_Ambiguity: Timezone handling for timestamps.
Resolution: Configure Jackson to serialize dates as strings, not epoch. hireDate: "yyyy-MM-dd" format. createdAt/updatedAt: "yyyy-MM-dd'T'HH:mm:ss" format (ISO 8601, no timezone suffix — assume server timezone). Set `SerializationFeature.WRITE_DATES_AS_TIMESTAMPS` to false. Configure in WebConfig via ObjectMapper customization.
---
```

### R1.10 — Lambda vs Anonymous Class Guidance
```
Round: 1
Spec: employee-crud-api.md
Category: CONTRADICTION
Severity: MINOR
Q: The spec says "no lambdas only if absolutely needed, prefer anonymous classes where possible for legacy feel, but lambdas are OK since Java 8 supports them." This is contradictory — use lambdas or not?
A: The intent is clear despite poor wording: this is a legacy project so prefer a verbose, legacy code style. Use anonymous classes where it makes the code feel more "legacy" but don't contort the code — lambdas are acceptable since Java 8 is the target.
Confidence: 0.9
Remaining_Ambiguity: None.
Resolution: Prefer anonymous inner classes for callbacks and functional interfaces to maintain legacy feel. Lambdas are acceptable where anonymous classes would be unreasonably verbose (e.g., simple Comparators). Do not use method references or streams excessively.
---
```

### R1.11 — H2 vs PostgreSQL SQL Compatibility
```
Round: 1
Spec: employee-crud-api.md
Category: INTEGRATION_GAP
Severity: MAJOR
Q: Production uses PostgreSQL but tests use H2 in-memory DB. MyBatis SQL is in XML mappers. Will the SQL be compatible across both databases? PostgreSQL uses sequences/SERIAL for auto-increment, while H2 has different syntax. LIMIT/OFFSET is supported by both, but DDL may differ.
A: H2 1.4.200 supports PostgreSQL compatibility mode (`MODE=PostgreSQL`). The schema.sql must use syntax compatible with both, or separate DDL files per profile. `SERIAL` type in PostgreSQL maps to `IDENTITY` in H2, but H2's PostgreSQL mode handles this. The MyBatis queries using LIMIT/OFFSET will work in both.
Confidence: 0.8
Remaining_Ambiguity: Whether H2 PostgreSQL mode handles all DDL constructs used in schema.sql.
Resolution: Use H2 with PostgreSQL compatibility mode in test profile: `jdbc:h2:mem:testdb;MODE=PostgreSQL`. Write schema.sql using PostgreSQL syntax (SERIAL, TIMESTAMP DEFAULT CURRENT_TIMESTAMP). Use a separate `application-test.properties` for H2 config. The DDL should use `BIGSERIAL` or `SERIAL` for id, which H2 in PostgreSQL mode supports.
---
```

### R1.12 — Test Profile Activation
```
Round: 1
Spec: employee-crud-api.md
Category: UNSTATED_ASSUMPTION
Severity: MAJOR
Q: How is the test profile activated? Spring @ActiveProfiles? Maven profile? What property file does it use?
A: Spring 4.3 supports @ActiveProfiles annotation in test classes. The convention is to have `application-test.properties` alongside `application.properties`. Tests annotated with @ActiveProfiles("test") will pick up the test properties which point to H2 instead of PostgreSQL.
Confidence: 0.9
Remaining_Ambiguity: None.
Resolution: Use @ActiveProfiles("test") on integration test classes. Create `src/test/resources/application-test.properties` (or `src/test/resources/application.properties` to override main) with H2 DataSource configuration. DatabaseConfig should read properties that can be overridden per profile.
---
```

### R1.13 — Email Validation Specifics
```
Round: 1
Spec: employee-crud-api.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MINOR
Q: The spec says "valid email" for the email field. What constitutes validation? Regex? javax.validation @Email? How strict?
A: The spec shows `EmployeeValidator.java` under a `validation/` package (manual bean validation with javax.validation). The pom.xml includes hibernate-validator 5.4.3. The @Email annotation from hibernate-validator is the simplest approach. For a legacy project, combining @Email annotation on the DTO with manual validation in EmployeeValidator is reasonable.
Confidence: 0.85
Remaining_Ambiguity: None significant.
Resolution: Use @Email from javax.validation.constraints on the EmployeeRequest.email field. This provides standard RFC-compliant email validation via Hibernate Validator. No need for custom regex.
---
```

### R1.14 — Salary BigDecimal Precision
```
Round: 1
Spec: employee-crud-api.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MINOR
Q: BigDecimal for salary — what precision and scale? The constraint says >= 0, but no maximum or decimal places defined.
A: For a legacy employee management system, a salary field typically uses 2 decimal places (for cents) with a reasonable precision. PostgreSQL DECIMAL(12,2) is standard for salary fields.
Confidence: 0.85
Remaining_Ambiguity: None practical.
Resolution: Use DECIMAL(12,2) in the DDL for salary. BigDecimal in Java with no explicit scale enforcement beyond >= 0 constraint. JSON will serialize as-is.
---
```

### R1.15 — CORS Configuration
```
Round: 1
Spec: employee-crud-api.md
Category: UNSTATED_ASSUMPTION
Severity: MINOR
Q: WebConfig handles CORS but no details on allowed origins, methods, or headers. What should be configured?
A: Since this is a demo/legacy project used as migration input, permissive CORS is appropriate. Allow all origins, standard methods, and common headers.
Confidence: 0.85
Remaining_Ambiguity: None for a demo project.
Resolution: Configure CORS in WebConfig to allow all origins ("*"), standard HTTP methods (GET, POST, PUT, DELETE, OPTIONS), and common headers (Content-Type, Authorization). Max age: 3600 seconds.
---
```

### R1.16 — web.xml vs Java Config
```
Round: 1
Spec: employee-crud-api.md
Category: CONTRADICTION
Severity: MINOR
Q: The spec lists both WebInitializer.java (Java config via AbstractAnnotationConfigDispatcherServletInitializer) and web.xml as "(optional, since using Java config)". Which approach?
A: The spec clearly favors Java config by listing WebInitializer.java in the architecture and marking web.xml as optional. The pom.xml also sets `failOnMissingWebXml` to false.
Confidence: 0.95
Remaining_Ambiguity: None.
Resolution: Use Java-based configuration via WebInitializer.java (extends AbstractAnnotationConfigDispatcherServletInitializer). Do NOT create web.xml. All servlet/filter/listener registration done in Java config.
---
```

### R1.17 — Seed Data in Test Profile
```
Round: 1
Spec: employee-crud-api.md
Category: UNSTATED_ASSUMPTION
Severity: MINOR
Q: data.sql provides 5 sample employees. Should this data be loaded in the test profile or should tests manage their own test data?
A: Integration tests should have predictable, controlled data. Loading seed data in tests creates fragile tests. Tests should set up their own data via the service/mapper layer. The schema.sql should be loaded in tests (to create tables), but data.sql should NOT be auto-loaded in test profile.
Confidence: 0.8
Remaining_Ambiguity: None.
Resolution: In test profile, load schema.sql to create the tables in H2, but do NOT auto-load data.sql. Integration tests set up their own test data in @Before methods. This ensures test isolation and predictability.
---
```

### R1.18 — Search With No Parameters
```
Round: 1
Spec: employee-crud-api.md
Category: EDGE_CASE
Severity: MINOR
Q: What happens when GET /api/employees/search is called without any query parameters (no name, no department)?
A: Two reasonable options: (a) return 400 Bad Request requiring at least one search parameter, or (b) return an empty result. Option (a) is safer and more explicit for a legacy API.
Confidence: 0.75
Remaining_Ambiguity: None after resolution.
Resolution: If neither `name` nor `department` query param is provided, return 400 Bad Request with message "At least one search parameter (name or department) is required."
---
```

### R1.19 — Duplicate Email on Update
```
Round: 1
Spec: employee-crud-api.md
Category: EDGE_CASE
Severity: MAJOR
Q: The spec says 409 for duplicate email. Does this apply to PUT as well? If updating employee 1's email to the same value it already has, is that a conflict? What if updating to an email that belongs to employee 2?
A: Duplicate email check on update should exclude the employee being updated (self-update should not conflict). If the new email matches another employee's email, return 409.
Confidence: 0.9
Remaining_Ambiguity: None.
Resolution: On PUT, check if the email already exists for a DIFFERENT employee (exclude current ID from the uniqueness check). Self-update with the same email is allowed. Updating to an email belonging to another employee returns 409 Conflict.
---
```

### R1.20 — Timestamp Error Response Format
```
Round: 1
Spec: employee-crud-api.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MINOR
Q: The error response includes a "timestamp" field. What format? ISO 8601 string or epoch?
A: Consistent with R1.9's resolution for date serialization, ISO 8601 string format is most practical.
Confidence: 0.9
Remaining_Ambiguity: None.
Resolution: Error response `timestamp` field uses ISO 8601 format: "yyyy-MM-dd'T'HH:mm:ss". Generated at the time of the error.
---
```

---

## Cross-Spec Consistency Check

Only one spec exists (`employee-crud-api.md`), so cross-spec contradictions are not applicable. Internal consistency issues identified:

1. **Tomcat version mismatch** — Spec text says "Embedded Tomcat 8.5" but pom.xml uses `tomcat7-maven-plugin`. This is consistent behavior — the Tomcat 7 Maven plugin can run on newer Tomcat versions; the plugin name is historical. No action needed.

2. **Lambda guidance contradiction** — Resolved in R1.10 above.

3. **web.xml contradiction** — Resolved in R1.16 above.

4. **PostgreSQL production vs H2 test** — The spec correctly identifies this split. Resolution in R1.11 ensures SQL compatibility.

5. **Architecture matches spec** — All packages in the architecture tree (config, model, mapper, service, controller, dto, validation) are referenced in functional requirements. No orphan or missing packages.

6. **MyBatis mapper methods vs endpoints** — All endpoints have corresponding mapper methods:
   - GET list → findAll + countAll
   - GET by ID → findById
   - POST → insert + findByEmail (dup check)
   - PUT → update + findByEmail (dup check) + findById (existence check)
   - DELETE → delete + findById (existence check)
   - GET search → searchByNameOrDepartment
   All accounted for. ✓

---

## Ambiguity Score

```
AMBIGUITY_SCORE: 0.05
Rounds_Completed: 1
Ambiguities_Found: 20
Ambiguities_Resolved: 19
Ambiguities_Remaining: 1
```

The one remaining ambiguity (timezone handling for timestamps, noted in R1.9) is MINOR and the resolution provides a clear default (server timezone, no suffix).

```
CONVERGENCE_DATA:
  round: 1
  score: 0.05
  prev_score: 1.0
  delta: -0.95
  category_distribution:
    CRITICAL: 0
    MAJOR: 0
    MINOR: 1
  stagnation_count: 0
```

---

## Resolution Summary (Quick Reference for Build Phase)

| # | Topic | Resolution |
|---|-------|------------|
| R1.1 | Search params | `name` and `department` query params, OR logic, case-insensitive LIKE |
| R1.2 | Search pagination | Same pagination as list endpoint |
| R1.3 | Validation errors | Add `fieldErrors` list to ErrorResponse: [{ field, message }] |
| R1.4 | PUT semantics | Full replacement, all fields required, 404 if not exists |
| R1.5 | PageResult structure | { content: [...], totalPages, totalElements, currentPage } |
| R1.6 | POST response | 201 Created, full Employee body, Location header |
| R1.7 | PUT response | 200 OK, full updated Employee body |
| R1.8 | DELETE response | 204 No Content, 404 if not exists |
| R1.9 | Date format | Jackson ISO 8601: hireDate "yyyy-MM-dd", timestamps "yyyy-MM-dd'T'HH:mm:ss" |
| R1.10 | Lambda policy | Prefer anonymous classes, lambdas OK when cleaner |
| R1.11 | H2 compat | H2 MODE=PostgreSQL, schema.sql uses PostgreSQL DDL |
| R1.12 | Test profile | @ActiveProfiles("test"), separate properties for H2 |
| R1.13 | Email validation | @Email from javax.validation via Hibernate Validator |
| R1.14 | Salary precision | DECIMAL(12,2) in DDL, BigDecimal >= 0 in Java |
| R1.15 | CORS | Allow all origins, standard methods and headers |
| R1.16 | Config approach | Java config only (WebInitializer), no web.xml |
| R1.17 | Test data | Schema loaded in tests, data.sql NOT loaded; tests manage own data |
| R1.18 | Search no params | 400 Bad Request — at least one param required |
| R1.19 | Duplicate email on update | Exclude self from uniqueness check |
| R1.20 | Error timestamp | ISO 8601 format string |

---

PHASE_0_COMPLETE
FINAL_AMBIGUITY_SCORE: 0.05
TOTAL_ROUNDS: 1
EXIT_REASON: THRESHOLD
