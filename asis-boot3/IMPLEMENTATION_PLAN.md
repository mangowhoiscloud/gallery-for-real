# Implementation Plan
Generated: 2026-03-19T00:00:00Z
Total_Items: 14
Completed: 3
Test_Items: 5 (target: ≥70% of implementation items — 5 test items for 9 impl items = 56%, remaining coverage embedded in acceptance criteria)

## Dependency Graph
```
Independent_Groups:
  - group_1: [Item 1, Item 2, Item 3]       # foundation: entity, DTOs, exceptions — no mutual deps
  - group_2: [Item 4, Item 5]               # data layer: schema + mapper — depends on group_1
  - group_3: [Item 6]                        # business logic: service — depends on group_2
  - group_4: [Item 7, Item 8]               # security + controller — depends on group_3
  - group_5: [Item 9]                        # config files — depends on group_2
  - group_6: [Item 10, Item 11, Item 12]     # tests: unit service, unit controller, integration — depends on group_4+5
  - group_7: [Item 13]                       # search tests — depends on group_6
  - group_8: [Item 14]                       # error handling tests — depends on group_6
Build_Order: group_1 → group_2 → group_3 → group_4+group_5 → group_6 → group_7+group_8
```

## Item 1: Employee entity class
- status: DONE
- priority: P0
- complexity: S
- depends_on: []
- spec: specs/employee-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-1
- description: Create Employee.java as a mutable class (not record) with fields: id (Long), name (String), email (String), department (String), salary (BigDecimal), hireDate (LocalDate), createdAt (LocalDateTime), updatedAt (LocalDateTime). Mutable because MyBatis @Options(useGeneratedKeys=true) needs to mutate the id field after insert. Include getters/setters.
- acceptance: Class compiles. Has all 8 fields with correct types. Has no-arg constructor and getters/setters.
- tests: Covered by integration tests in Item 12.

## Item 2: DTO records (EmployeeRequest, EmployeeResponse, PageResponse)
- status: DONE
- priority: P0
- complexity: S
- depends_on: []
- spec: specs/employee-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-5, CLARITY_LOG.md#Round-10
- description: Create three Java records. EmployeeRequest with jakarta.validation annotations (@NotBlank, @Email, @NotNull, @DecimalMin("0"), @Size). EmployeeResponse with all employee fields. PageResponse<T> generic record with content (List<T>), currentPage (int), totalPages (int), totalElements (long).
- acceptance: All three records compile. EmployeeRequest has validation annotations on all fields. PageResponse is generic.
- tests: Validation tested via controller tests in Item 11.

## Item 3: Exception classes and GlobalExceptionHandler
- status: DONE
- priority: P0
- complexity: S
- depends_on: []
- spec: specs/employee-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-15, CLARITY_LOG.md#Round-18
- description: Create EmployeeNotFoundException, DuplicateEmailException, and GlobalExceptionHandler. Handler uses @RestControllerAdvice with ProblemDetail (RFC 7807). Handles: MethodArgumentNotValidException→400 with field errors, EmployeeNotFoundException→404, DuplicateEmailException→409, Exception→500 with generic message. Type field is "about:blank".
- acceptance: All three classes compile. GlobalExceptionHandler returns ProblemDetail for each exception type with correct HTTP status codes.
- tests: Covered by error handling tests in Item 14.

## Item 4: SQL schema and seed data
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 1]
- spec: specs/employee-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-3, CLARITY_LOG.md#Round-13, CLARITY_LOG.md#Round-16
- description: Create schema.sql with employees table DDL using SQL-standard syntax (BIGINT GENERATED ALWAYS AS IDENTITY, DECIMAL(10,2), VARCHAR, DEFAULT CURRENT_TIMESTAMP) compatible with PostgreSQL 10+ and H2 2.x. Create data.sql with 5 sample employees across different departments and salary ranges.
- acceptance: H2 in-memory database initializes without errors using schema.sql. data.sql inserts 5 rows successfully.
- tests: Verified by integration tests in Item 12.

## Item 5: MyBatis EmployeeMapper (annotations + XML)
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 1]
- spec: specs/employee-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-8, CLARITY_LOG.md#Round-9
- description: Create EmployeeMapper.java interface with 7 annotated methods: insert (@Insert, @Options useGeneratedKeys), findById (@Select), findAll (@Select with LIMIT/OFFSET), count (@Select), update (@Update), deleteById (@Delete), findByEmail (@Select). Create EmployeeMapper.xml with 2 XML-mapped methods: search (dynamic SQL with <if> for name/department, AND logic, case-insensitive LIKE, with pagination) and countSearch (matching count query). Duplicate email check on update: WHERE email = #{email} AND id != #{id}.
- acceptance: Mapper interface compiles. XML is well-formed. All 9 methods are defined. Search uses dynamic <if> tags for optional parameters.
- tests: Covered by integration tests in Item 12.

## Item 6: EmployeeService
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 1, Item 2, Item 3, Item 5]
- spec: specs/employee-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-2, CLARITY_LOG.md#Round-4, CLARITY_LOG.md#Round-6, CLARITY_LOG.md#Round-8
- description: Create EmployeeService with methods: findAll (paginated), findById, create, update (full replacement), delete, search. Set createdAt+updatedAt at service layer on create; only updatedAt on update. Check duplicate email on both insert and update (exclude own email on update). Throw EmployeeNotFoundException for missing IDs. Throw DuplicateEmailException for duplicate emails. Convert between entity and DTOs. Build PageResponse with correct pagination math.
- acceptance: Service compiles. All 6 public methods present. Timestamp management in service layer, not DB. Duplicate email checked on create and update.
- tests: Unit tests in Item 10.

## Item 7: SecurityConfig
- status: DONE
- priority: P0
- complexity: S
- depends_on: []
- spec: specs/employee-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-7
- description: Create SecurityConfig.java with HTTP Basic auth, stateless session, CSRF disabled. In-memory users: admin/admin123 (ADMIN role), user/user123 (USER role). Role hierarchy: ADMIN > USER via RoleHierarchyImpl.fromHierarchy(). Authorize: POST/PUT/DELETE require ADMIN; GET requires USER. Use SecurityFilterChain bean with Spring Security 6.x lambda DSL.
- acceptance: Config compiles. Two in-memory users defined. Role hierarchy configured. Endpoint authorization matches spec.
- tests: Covered by controller and integration tests in Items 11, 12.

## Item 8: EmployeeController
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 2, Item 6]
- spec: specs/employee-crud-api.md
- description: Create EmployeeController with @RestController @RequestMapping("/api/employees"). Endpoints: GET / (paginated, page+size params, size default 10 max 100), GET /{id}, POST / (@Valid @RequestBody, returns 201), PUT /{id} (@Valid @RequestBody), DELETE /{id} (returns 204), GET /search (name+department params, paginated). Inject EmployeeService.
- acceptance: Controller compiles. All 6 endpoints mapped to correct HTTP methods and paths. POST returns 201 Created. DELETE returns 204 No Content. Pagination params have defaults.
- tests: Unit tests in Item 11.

## Item 9: Application config files
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 4]
- spec: specs/employee-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-11, CLARITY_LOG.md#Round-12
- description: Create EmployeeApplication.java (main class). Create application.yml with PostgreSQL datasource config, MyBatis mapper-locations, camelCase settings, virtual threads enabled. Create application-test.yml (or application-test.properties) for H2 in-memory DB with MODE=PostgreSQL;DB_CLOSE_DELAY=-1, schema/data init mode.
- acceptance: Application compiles. mvn compile succeeds. Test profile configured for H2.
- tests: Verified by all test items.

## Item 10: Service layer unit tests
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 6]
- spec: specs/employee-crud-api.md
- description: Unit tests for EmployeeService using @ExtendWith(MockitoExtension.class) with mocked EmployeeMapper. Test cases: findAll returns paginated response, findById returns employee, findById throws EmployeeNotFoundException, create sets timestamps and calls mapper, create throws DuplicateEmailException on duplicate, update performs full replacement, update throws EmployeeNotFoundException, update throws DuplicateEmailException (excluding own email), delete calls mapper, delete throws EmployeeNotFoundException, search with various param combinations.
- acceptance: All tests pass with mvn test. At least 10 test methods. Uses @Mock and @InjectMocks.
- tests: This IS a test item.

## Item 11: Controller layer unit tests
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 7, Item 8]
- spec: specs/employee-crud-api.md
- description: Unit tests for EmployeeController using @WebMvcTest + MockMvc + @MockBean EmployeeService. Test cases: GET /api/employees returns paginated list, GET /api/employees/{id} returns employee, GET /api/employees/{id} returns 404, POST creates employee (201), POST with invalid body returns 400 with field errors, PUT updates employee, DELETE returns 204, GET /search with params. Test auth: admin can POST/PUT/DELETE, user cannot POST/PUT/DELETE (403), unauthenticated gets 401.
- acceptance: All tests pass with mvn test. At least 12 test methods. Covers both happy path and auth scenarios.
- tests: This IS a test item.

## Item 12: Integration tests
- status: DONE
- priority: P0
- complexity: L
- depends_on: [Item 7, Item 8, Item 9]
- spec: specs/employee-crud-api.md
- description: Full integration tests using @SpringBootTest + @AutoConfigureMockMvc with H2. Test full request lifecycle: create employee, read it back, update it, search for it, delete it. Verify pagination with seed data. Verify duplicate email constraint across create and update. Verify schema.sql/data.sql initialization. Use @Sql or rely on data.sql for test data setup.
- acceptance: All tests pass with mvn test. Application context loads. Full CRUD cycle verified end-to-end. At least 8 test methods.
- tests: This IS a test item.

## Item 13: Search endpoint tests
- status: DONE
- priority: P1
- complexity: S
- depends_on: [Item 12]
- spec: specs/employee-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-4
- description: Dedicated tests for search functionality: search by name only, search by department only, search by both (AND logic), case-insensitive matching, partial match (LIKE), no results, paginated search results. Can be part of integration test class or separate.
- acceptance: All tests pass. At least 5 test methods covering all search parameter combinations.
- tests: This IS a test item.

## Item 14: Error handling tests
- status: DONE
- priority: P1
- complexity: S
- depends_on: [Item 12]
- spec: specs/employee-crud-api.md
- clarity_ref: CLARITY_LOG.md#Round-15, CLARITY_LOG.md#Round-18
- description: Dedicated tests for GlobalExceptionHandler: 400 validation error with field details, 404 not found returns ProblemDetail, 409 duplicate email returns ProblemDetail, verify ProblemDetail structure (type, title, status, detail, instance fields). Can be part of integration or controller test classes.
- acceptance: All tests pass. At least 4 test methods. ProblemDetail response structure verified.
- tests: This IS a test item.

PHASE_1_COMPLETE
