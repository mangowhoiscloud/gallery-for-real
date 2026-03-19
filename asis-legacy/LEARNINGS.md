# LEARNINGS — Runtime Discoveries

### Learning: jackson-databind 2.9.11.1 does not exist
- Context: Initial pom.xml had `<jackson.version>2.9.11.1</jackson.version>`
- Discovery: Maven Central has no such artifact; the 2.9.x branch ends at 2.9.10.8
- Rule: Use `2.9.10.8` as the Jackson version for this project.

### Learning: @JsonFormat inherits ObjectMapper timezone
- Context: Employee model uses `@JsonFormat(pattern = "yyyy-MM-dd")` without explicit timezone
- Discovery: Jackson defaults @JsonFormat without timezone to UTC, not the JVM local timezone. Tests creating dates with `Timestamp.valueOf(...)` (local TZ) would fail unless ObjectMapper is configured with `setTimeZone(TimeZone.getDefault())`
- Rule: Always call `objectMapper.setTimeZone(TimeZone.getDefault())` in tests (and in production WebConfig) when using @JsonFormat patterns that should reflect server local time.

### Learning: javax.validation 1.1 lacks @NotBlank and @Email
- Context: EmployeeRequest DTO needed @NotBlank and @Email annotations
- Discovery: `javax.validation` 1.1.0.Final does not include `@NotBlank` or `@Email` (those were added in Bean Validation 2.0). Hibernate Validator 5.x provides them at `org.hibernate.validator.constraints.NotBlank` and `org.hibernate.validator.constraints.Email`.
- Rule: For this project, use `org.hibernate.validator.constraints.NotBlank` and `org.hibernate.validator.constraints.Email`. Standard `javax.validation.constraints` annotations (@NotNull, @Size, @DecimalMin, etc.) work as normal.

### Learning: Spring 4.3.x CGLIB fails on Java 17+ without --add-opens
- Context: First integration test using @ContextConfiguration(classes = TestAppConfig.class) on Java 25
- Discovery: Spring 4.3.x bundles CGLIB 3.2.5/ASM 5.x which uses reflection to call `ClassLoader.defineClass()` (a protected method) when generating @Configuration proxy subclasses. Java 9+ module system blocks this by default, causing `ExceptionInInitializerError: null` in `org.springframework.cglib.proxy.Enhancer`.
- Rule: Add `--add-opens java.base/java.lang=ALL-UNNAMED --add-opens java.base/java.lang.reflect=ALL-UNNAMED --add-opens java.base/java.io=ALL-UNNAMED` to maven-surefire-plugin `<argLine>` in pom.xml. This is required for ANY test that loads a Spring application context (via @ContextConfiguration) with Spring 4.x on Java 9+.
