package com.example.employee;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.boot.jdbc.DataSourceBuilder;
import org.springframework.core.io.ClassPathResource;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.init.ResourceDatabasePopulator;

import javax.sql.DataSource;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.assertThrows;

/**
 * Verifies schema.sql and data.sql without requiring a full Spring Boot context.
 * Uses H2 with MODE=PostgreSQL to match production compatibility requirements.
 */
class SchemaInitTest {

    private DataSource dataSource;
    private JdbcTemplate jdbcTemplate;

    @BeforeEach
    void setUp() {
        dataSource = DataSourceBuilder.create()
                .driverClassName("org.h2.Driver")
                .url("jdbc:h2:mem:schematest;MODE=PostgreSQL;DB_CLOSE_DELAY=-1;DB_CLOSE_ON_EXIT=FALSE")
                .username("sa")
                .password("")
                .build();
        jdbcTemplate = new JdbcTemplate(dataSource);

        ResourceDatabasePopulator populator = new ResourceDatabasePopulator();
        populator.addScript(new ClassPathResource("schema.sql"));
        populator.addScript(new ClassPathResource("data.sql"));
        populator.execute(dataSource);
    }

    @AfterEach
    void tearDown() {
        jdbcTemplate.execute("DROP TABLE IF EXISTS employees");
    }

    @Test
    void seedDataLoadsFiveRows() {
        Integer count = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM employees", Integer.class);
        assertThat(count).isEqualTo(5);
    }

    @Test
    void seedDataCoversAllFiveDepartments() {
        var departments = jdbcTemplate.queryForList(
                "SELECT DISTINCT department FROM employees ORDER BY department",
                String.class);
        assertThat(departments).containsExactly(
                "Engineering", "Finance", "HR", "Marketing", "Sales");
    }

    @Test
    void allSeedSalariesAreNonNegative() {
        Integer invalidCount = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM employees WHERE salary < 0", Integer.class);
        assertThat(invalidCount).isZero();
    }

    @Test
    void uniqueEmailConstraintIsEnforced() {
        assertThrows(Exception.class, () ->
                jdbcTemplate.update(
                        "INSERT INTO employees (name, email, department, salary, hire_date) "
                        + "VALUES ('Dup', 'alice.johnson@example.com', 'Engineering', 50000.00, '2023-01-01')")
        );
    }
}
