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
