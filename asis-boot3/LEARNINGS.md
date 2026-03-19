# LEARNINGS — Runtime Discoveries

### Learning: @JdbcTest requires @SpringBootConfiguration
- Context: Writing schema verification test (Item 4) before EmployeeApplication.java exists
- Discovery: @JdbcTest (and all Spring Boot test slice annotations) search for a @SpringBootApplication/@SpringBootConfiguration in the classpath. If none exists, the test fails with IllegalStateException even if no app config is actually needed.
- Rule: Before EmployeeApplication.java is created (Item 9), use plain JUnit 5 + Spring's ResourceDatabasePopulator or EmbeddedDatabaseBuilder for DB tests. After Item 9, @JdbcTest and @SpringBootTest become available.

### Learning: ResourceDatabasePopulator for script-based DB testing without Spring context
- Context: Needed to test schema.sql and data.sql initialization
- Discovery: `ResourceDatabasePopulator` + `DataSourceBuilder` (with H2 JDBC URL) lets you load SQL scripts against an embedded H2 DB without any Spring application context. Works cleanly in plain JUnit 5 tests.
- Rule: Use `DataSourceBuilder.create().url("jdbc:h2:mem:X;MODE=PostgreSQL;DB_CLOSE_DELAY=-1").build()` + `ResourceDatabasePopulator` when you need SQL script testing without a Spring context.

### Learning: BIGINT GENERATED ALWAYS AS IDENTITY works in standard H2 mode
- Context: Choosing DDL syntax compatible with both PostgreSQL and H2 (Ambiguity 3 in CLARITY_LOG)
- Discovery: `BIGINT GENERATED ALWAYS AS IDENTITY` is SQL-standard and supported by H2 2.x even without MODE=PostgreSQL. Both PostgreSQL 10+ and H2 2.x accept this syntax natively.
- Rule: Prefer `BIGINT GENERATED ALWAYS AS IDENTITY` over `SERIAL` (PostgreSQL-only) or `AUTO_INCREMENT` (MySQL/H2-specific) for portable DDL.

### Learning: XMLMapperBuilder auto-registers the mapper interface
- Context: Setting up standalone MyBatis test for EmployeeMapper (no Spring context)
- Discovery: Calling `new XMLMapperBuilder(is, config, ...).parse()` automatically invokes `bindMapperForNamespace()`, which calls `config.addMapper(EmployeeMapper.class)`. This registers both the XML statements AND all annotation-based statements on the interface. No need to call `config.addMapper()` separately.
- Rule: When loading a MyBatis XML mapper manually, call `XMLMapperBuilder.parse()` first — it handles interface registration. Do NOT also call `config.addMapper()` separately, or you may get duplicate statement exceptions.

### Learning: generateUniqueName(true) for EmbeddedDatabaseBuilder
- Context: Creating isolated H2 databases for each EmployeeMapperTest test method
- Discovery: `EmbeddedDatabaseBuilder.generateUniqueName(true)` gives each embedded database a unique name, preventing collisions when multiple tests run in the same JVM (each @BeforeEach gets its own named in-memory H2 instance).
- Rule: Always use `.generateUniqueName(true)` on EmbeddedDatabaseBuilder in test setup to avoid cross-test pollution with shared H2 database names.

### Learning: mapUnderscoreToCamelCase eliminates @Results boilerplate
- Context: Mapping DB columns (hire_date, created_at, updated_at) to Java fields (hireDate, createdAt, updatedAt)
- Discovery: Setting `config.setMapUnderscoreToCamelCase(true)` on the MyBatis Configuration handles underscore-to-camelCase mapping for `SELECT *` queries automatically. No @Results/@Result annotations needed.
- Rule: Enable mapUnderscoreToCamelCase in MyBatis configuration (both standalone test and application.yml) and use SELECT * to avoid verbose result mapping annotations.

### Learning: expressionHandler() removed from authorizeHttpRequests in Spring Security 6.x
- Context: Configuring RoleHierarchy for SecurityFilterChain (Item 7)
- Discovery: `expressionHandler()` method only exists on the deprecated `authorizeRequests()` DSL (SpEL-based). The modern `authorizeHttpRequests()` (AuthorizationManager-based) has no `expressionHandler()` method. In Spring Security 6.3+ (bundled with Spring Boot 3.3.x), registering `RoleHierarchy` as a `@Bean` is sufficient — it is auto-detected by the framework.
- Rule: For role hierarchy in Spring Security 6.x, simply expose `RoleHierarchyImpl.fromHierarchy(...)` as a `@Bean`. Never call `.expressionHandler()` on `authorizeHttpRequests` — it does not exist.

### Learning: @MockBean in @WebMvcTest fails on Java 25 without Byte Buddy experimental mode
- Context: Writing EmployeeControllerTest with @WebMvcTest + @MockBean EmployeeService on a machine where Maven uses Java 25 (Homebrew) but Byte Buddy 1.14.19 supports up to Java 23
- Discovery: @MockBean triggers Byte Buddy subclass instrumentation at Spring context startup. This fails with "Java 25 (69) is not supported" unless net.bytebuddy.experimental=true is set. Plain @Mock with @ExtendWith(MockitoExtension.class) uses a different instrumentation path (dynamic agent via byte-buddy-agent.jar) that works around the version check.
- Rule: If Maven's JDK is newer than the Byte Buddy version's officially supported max, add `-Dnet.bytebuddy.experimental=true` to maven-surefire-plugin argLine. Maven's JAVA_HOME can differ from the shell's java -version — check with `mvn -version`.

### Learning: @WebMvcTest + @Import(SecurityConfig.class) for real security testing
- Context: Testing role-based authorization (ADMIN vs USER) in EmployeeControllerTest
- Discovery: @WebMvcTest loads the security filter chain by default, but the real SecurityConfig (with role hierarchy ADMIN > USER) must be imported explicitly via @Import(SecurityConfig.class). Without it, Spring Boot falls back to a default permit-all security config and auth tests would not reflect real behavior. @WithMockUser(roles="USER") injects a pre-authenticated user; the actual authorization rules from SecurityConfig then apply.
- Rule: For @WebMvcTest tests that need to verify real authorization rules, use @Import(SecurityConfig.class). @WithMockUser sets the security context; the filter chain enforces the real rules.
