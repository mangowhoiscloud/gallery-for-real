package com.example.legacy.controller;

import com.example.legacy.config.SecurityConfig;
import com.example.legacy.config.TestAppConfig;
import com.example.legacy.config.WebConfig;
import com.example.legacy.mapper.EmployeeMapper;
import com.example.legacy.model.Employee;
import com.example.legacy.service.EmployeeService;
import com.example.legacy.service.EmployeeServiceImpl;
import com.example.legacy.validation.EmployeeValidator;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.security.test.web.servlet.setup.SecurityMockMvcConfigurers;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;
import org.springframework.test.context.web.WebAppConfiguration;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.context.WebApplicationContext;

import java.math.BigDecimal;
import java.sql.Date;

import static org.hamcrest.Matchers.hasSize;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.httpBasic;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Integration tests for EmployeeController search and pagination endpoints.
 *
 * Seeds multiple employees in setUp() to exercise:
 *   - GET /api/employees/search?name=X  (name-only, case-insensitive)
 *   - GET /api/employees/search?department=Y  (department-only, case-insensitive)
 *   - GET /api/employees/search?name=X&department=Y  (OR logic — either match)
 *   - GET /api/employees/search  (no params → 400)
 *   - GET /api/employees?page=0&size=2  (first page)
 *   - GET /api/employees?page=1&size=2  (second page)
 *   - GET /api/employees/search?name=NOMATCH  (empty result)
 *
 * All tests are @Transactional — H2 state is rolled back after each method.
 */
@RunWith(SpringJUnit4ClassRunner.class)
@WebAppConfiguration
@ContextConfiguration(classes = EmployeeSearchPaginationIntegrationTest.TestConfig.class)
@Transactional
public class EmployeeSearchPaginationIntegrationTest {

    @Configuration
    @Import({TestAppConfig.class, SecurityConfig.class, WebConfig.class})
    static class TestConfig {

        @Bean
        public EmployeeValidator employeeValidator(EmployeeMapper employeeMapper) {
            return new EmployeeValidator(employeeMapper);
        }

        @Bean
        public EmployeeServiceImpl employeeService(EmployeeMapper employeeMapper,
                                                    EmployeeValidator employeeValidator) {
            return new EmployeeServiceImpl(employeeMapper, employeeValidator);
        }

        @Bean
        public EmployeeController employeeController(EmployeeService employeeService) {
            return new EmployeeController(employeeService);
        }

        @Bean
        public GlobalExceptionHandler globalExceptionHandler() {
            return new GlobalExceptionHandler();
        }
    }

    @Autowired
    private WebApplicationContext wac;

    @Autowired
    private EmployeeMapper employeeMapper;

    private MockMvc mockMvc;

    // Employee IDs seeded in setUp(); available for assertions if needed.
    private Long aliceId;
    private Long bobId;
    private Long carolId;

    @Before
    public void setUp() {
        mockMvc = MockMvcBuilders.webAppContextSetup(wac)
                .apply(SecurityMockMvcConfigurers.springSecurity())
                .build();

        // Alice — Engineering
        Employee alice = new Employee();
        alice.setName("Alice Smith");
        alice.setEmail("alice@example.com");
        alice.setDepartment("Engineering");
        alice.setSalary(new BigDecimal("50000.00"));
        alice.setHireDate(new Date(1579046400000L)); // 2020-01-15 UTC
        employeeMapper.insert(alice);
        aliceId = alice.getId();

        // Bob — Engineering (same dept as Alice, different name)
        Employee bob = new Employee();
        bob.setName("Bob Jones");
        bob.setEmail("bob@example.com");
        bob.setDepartment("Engineering");
        bob.setSalary(new BigDecimal("60000.00"));
        bob.setHireDate(new Date(1579046400000L));
        employeeMapper.insert(bob);
        bobId = bob.getId();

        // Carol — HR (different dept; name contains no overlap with Alice/Bob)
        Employee carol = new Employee();
        carol.setName("Carol HR");
        carol.setEmail("carol@example.com");
        carol.setDepartment("HR");
        carol.setSalary(new BigDecimal("45000.00"));
        carol.setHireDate(new Date(1579046400000L));
        employeeMapper.insert(carol);
        carolId = carol.getId();
    }

    // ─── Search: name-only ───────────────────────────────────────────────────

    @Test
    public void searchByName_returnsMatchingEmployee() throws Exception {
        mockMvc.perform(get("/api/employees/search")
                        .param("name", "alice")           // lowercase — tests case-insensitivity
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content", hasSize(1)))
                .andExpect(jsonPath("$.content[0].name").value("Alice Smith"))
                .andExpect(jsonPath("$.totalElements").value(1));
    }

    @Test
    public void searchByName_caseInsensitive_returnsMatch() throws Exception {
        mockMvc.perform(get("/api/employees/search")
                        .param("name", "ALICE")           // all caps
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content", hasSize(1)))
                .andExpect(jsonPath("$.content[0].email").value("alice@example.com"));
    }

    // ─── Search: department-only ─────────────────────────────────────────────

    @Test
    public void searchByDepartment_returnsAllMatchingEmployees() throws Exception {
        mockMvc.perform(get("/api/employees/search")
                        .param("department", "engineering") // lowercase
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content", hasSize(2)))
                .andExpect(jsonPath("$.totalElements").value(2));
    }

    // ─── Search: name AND department (OR logic) ──────────────────────────────

    @Test
    public void searchByNameAndDepartment_returnsUnionOfMatches() throws Exception {
        // name "Carol" matches Carol; department "Engineering" matches Alice+Bob
        // OR logic → 3 results total
        mockMvc.perform(get("/api/employees/search")
                        .param("name", "Carol")
                        .param("department", "Engineering")
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content", hasSize(3)))
                .andExpect(jsonPath("$.totalElements").value(3));
    }

    // ─── Search: no params → 400 ─────────────────────────────────────────────

    @Test
    public void searchWithNoParams_returns400() throws Exception {
        mockMvc.perform(get("/api/employees/search")
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400))
                .andExpect(jsonPath("$.message").isString())
                .andExpect(jsonPath("$.timestamp").isString());
    }

    // ─── Search: no match → empty result ────────────────────────────────────

    @Test
    public void searchByName_noMatch_returnsEmptyPageResult() throws Exception {
        mockMvc.perform(get("/api/employees/search")
                        .param("name", "XYZNOTFOUND")
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content", hasSize(0)))
                .andExpect(jsonPath("$.totalElements").value(0))
                .andExpect(jsonPath("$.totalPages").value(0))
                .andExpect(jsonPath("$.currentPage").value(0));
    }

    // ─── Pagination: GET /api/employees?page=0&size=2 ───────────────────────

    @Test
    public void getAllPage0Size2_returnsFirstPageOfTwo() throws Exception {
        // 3 employees seeded → page 0, size 2 → 2 results, totalPages = 2
        mockMvc.perform(get("/api/employees")
                        .param("page", "0")
                        .param("size", "2")
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content", hasSize(2)))
                .andExpect(jsonPath("$.totalElements").value(3))
                .andExpect(jsonPath("$.totalPages").value(2))
                .andExpect(jsonPath("$.currentPage").value(0));
    }

    // ─── Pagination: GET /api/employees?page=1&size=2 ───────────────────────

    @Test
    public void getAllPage1Size2_returnsSecondPageWithOneEmployee() throws Exception {
        // 3 employees seeded → page 1, size 2 → 1 result (the remainder), totalPages = 2
        mockMvc.perform(get("/api/employees")
                        .param("page", "1")
                        .param("size", "2")
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content", hasSize(1)))
                .andExpect(jsonPath("$.totalElements").value(3))
                .andExpect(jsonPath("$.totalPages").value(2))
                .andExpect(jsonPath("$.currentPage").value(1));
    }
}
