# LEARNINGS — Runtime Discoveries

## Learning: mybatis-spring 1.2.2 has no setConfiguration()
- Context: Configuring MyBatis settings (mapUnderscoreToCamelCase) via SqlSessionFactoryBean
- Discovery: `SqlSessionFactoryBean.setConfiguration(Configuration)` was added in mybatis-spring 1.3.0. Version 1.2.2 (in this project's pom.xml) does not have this method.
- Rule: Always use `factory.setConfigLocation(new ClassPathResource("mybatis-config.xml"))` with an XML config file for MyBatis settings. Do NOT use `setConfiguration()`.

## Learning: H2 table metadata requires matching case
- Context: Verifying schema tables in AppConfigTest via `getMetaData().getTables(null, null, pattern, ...)`
- Discovery: H2 with `DATABASE_TO_LOWER=TRUE` stores table names in lowercase. The `getTables()` pattern match is case-sensitive. Using `.toUpperCase()` on the pattern fails to find tables.
- Rule: When querying `DatabaseMetaData.getTables()` in tests, pass the table name exactly as defined in schema.sql (lowercase). Do NOT call `.toUpperCase()`.

## Learning: MapperScannerConfigurer must be declared static
- Context: Declaring MapperScannerConfigurer as a @Bean in a @Configuration class
- Discovery: MapperScannerConfigurer implements BeanDefinitionRegistryPostProcessor and must be instantiated very early in the Spring lifecycle. If declared as a non-static @Bean method, CGLIB proxying conflicts with early instantiation, causing "cannot enhance @Configuration bean" warning.
- Rule: Always declare `@Bean public static MapperScannerConfigurer mapperScannerConfigurer()` — note the `static` modifier. This prevents CGLIB proxy issues.

## Learning: H2 PostgreSQL mode for schema compatibility
- Context: Reusing the same schema.sql for both PostgreSQL (prod) and H2 (test)
- Discovery: H2 2.x with `MODE=PostgreSQL;DATABASE_TO_LOWER=TRUE` supports `BIGSERIAL`, `TEXT`, CHECK constraints with IN, and `DEFAULT CURRENT_TIMESTAMP` — exactly what the schema.sql uses. No separate test schema needed.
- Rule: Use `jdbc:h2:mem:testdb;MODE=PostgreSQL;DATABASE_TO_LOWER=TRUE;DB_CLOSE_DELAY=-1` for H2 test DataSource URL to maximize schema compatibility.

## Learning: MyBatis <foreach> batch insert uses implicit "list" collection name
- Context: Implementing insertBatch(List<OrderItem>) in OrderItemMapper.xml
- Discovery: When the mapper method takes a plain `List<T>` parameter (no @Param annotation), MyBatis exposes it as `collection="list"` in `<foreach>`. No `parameterType` attribute is required on the `<insert>` element — MyBatis handles it automatically.
- Rule: For batch inserts, write `<insert id="insertBatch"><foreach collection="list" item="item" separator=",">...</foreach></insert>` with no parameterType. If you need a different collection name, use @Param("items") on the mapper method and `collection="items"` in XML.

## Learning: @NotBlank not in javax.validation.constraints for Bean Validation 1.1
- Context: Writing validation test for GlobalExceptionHandler using inner @RestController with validated request body
- Discovery: `javax.validation.constraints.NotBlank` does not exist in `validation-api:1.1.0.Final`. It was introduced in Bean Validation 2.0. In Bean Validation 1.1, `@NotBlank` lives in `org.hibernate.validator.constraints.NotBlank` (Hibernate-specific).
- Rule: For this project (validation-api 1.1.0.Final), use `@NotNull` from `javax.validation.constraints` or `org.hibernate.validator.constraints.NotBlank`. Do NOT import `javax.validation.constraints.NotBlank` — it will cause a compile error.

## Learning: @WithMockUser works cleanly with webAppContextSetup + springSecurity() + @Transactional
- Context: Writing SecurityConfigTest for Spring Security 4.2 with full WebApplicationContext
- Discovery: @WithMockUser (sets mock security context), @Transactional (test transaction), and webAppContextSetup(wac).apply(springSecurity()).build() (security filter chain in MockMvc) coexist without interference. MockMvc @WithMockUser tests skip DB access entirely; @Transactional tests that call @Service beans directly share the same transaction as the mapper inserts.
- Rule: For security config tests, use @WithMockUser for authorization-rule tests (no DB setup needed) and @Transactional + direct service calls for UserDetailsService tests (inserts visible in same transaction). Avoid inserting test users in @Before when using @Transactional at class level — insert inline in the test method instead.

## Learning: Ant matcher order is critical for /api/members/me vs /api/members/*
- Context: Configuring Spring Security HTTP rules where /api/members/me (USER endpoint) and /api/members/{id} (ADMIN endpoint) share the /api/members/* pattern
- Discovery: Spring Security evaluates antMatchers in declaration order (first match wins). If /api/members/* with hasRole("ADMIN") comes before /api/members/me with hasAnyRole("USER","ADMIN"), USER role gets 403 on their own profile endpoint.
- Rule: Always list more-specific path patterns BEFORE wildcard patterns. Put /api/members/me before /api/members/* in the security config.

## Learning: TestWebConfig combining @EnableWebMvc + @ComponentScan + @Import for security integration tests
- Context: Setting up a test WebApplicationContext that includes TestConfig (MyBatis/H2), SecurityConfig (@EnableWebSecurity), and test controllers
- Discovery: Inner static @Configuration class annotated with @EnableWebMvc, @ComponentScan("com.example.shop.security") (to pick up CustomUserDetailsService), and @Import({TestConfig.class, SecurityConfig.class}) works as a self-contained test web config. Explicit @Bean declaration of @RestController inner classes is picked up by RequestMappingHandlerMapping.
- Rule: For Spring Security integration tests, use a static inner @Configuration that combines @EnableWebMvc + @ComponentScan for security package + @Import({TestConfig.class, SecurityConfig.class}). Explicitly declare test controllers as @Bean methods.
