package com.example.shop;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.core.env.Environment;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.ActiveProfiles;

import java.util.Arrays;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
@ActiveProfiles("test")
class ApplicationContextTest {

    @Autowired
    private Environment environment;

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Test
    void contextLoads() {
        // Spring context starts successfully — verified implicitly by test setup
        assertThat(environment).isNotNull();
    }

    @Test
    void h2ProfileIsActiveInTest() {
        assertThat(Arrays.asList(environment.getActiveProfiles())).contains("test");
        // Verify H2 is being used by checking datasource URL
        String url = environment.getProperty("spring.datasource.url");
        assertThat(url).containsIgnoringCase("h2");
    }

    @Test
    void adminMemberSeeded() {
        Integer count = jdbcTemplate.queryForObject(
            "SELECT COUNT(*) FROM member WHERE email = 'admin@shop.com' AND role = 'ADMIN' AND active = TRUE",
            Integer.class
        );
        assertThat(count).isEqualTo(1);
    }

    @Test
    void allSixTablesExist() {
        for (String table : new String[]{"member", "product", "cart", "cart_item", "orders", "order_item"}) {
            Integer count = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM information_schema.tables WHERE LOWER(table_name) = LOWER(?)",
                Integer.class, table
            );
            assertThat(count).as("Table '%s' should exist", table).isGreaterThan(0);
        }
    }
}
