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
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.context.WebApplicationContext;

import java.math.BigDecimal;
import java.sql.Date;

import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.hasSize;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.httpBasic;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Integration tests for EmployeeController CRUD endpoints.
 *
 * Uses a full Spring WebApplicationContext with H2 in-memory database,
 * Spring Security (HTTP Basic auth), and the real service/mapper stack.
 * Each test runs in a transaction that is rolled back on completion,
 * ensuring test isolation without manual cleanup.
 */
@RunWith(SpringJUnit4ClassRunner.class)
@WebAppConfiguration
@ContextConfiguration(classes = EmployeeCrudIntegrationTest.TestConfig.class)
@Transactional
public class EmployeeCrudIntegrationTest {

    /**
     * Composes the full test stack:
     * - TestAppConfig: H2 datasource, MyBatis, transaction manager
     * - SecurityConfig: HTTP Basic auth with admin/user roles
     * - WebConfig: @EnableWebMvc, Jackson ObjectMapper with local TZ
     * - Explicit beans for service layer and controller layer
     */
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

    // Valid POST request JSON — hireDate as epoch ms (2020-01-15 00:00:00 UTC)
    private static final String CREATE_JSON =
            "{\"name\":\"Alice Smith\",\"email\":\"alice@example.com\"," +
            "\"department\":\"Engineering\",\"salary\":50000.00," +
            "\"hireDate\":1579046400000}";

    // Update request — same email, different name/department/salary
    private static final String UPDATE_JSON =
            "{\"name\":\"Alice Updated\",\"email\":\"alice@example.com\"," +
            "\"department\":\"Sales\",\"salary\":65000.00," +
            "\"hireDate\":1579046400000}";

    @Autowired
    private WebApplicationContext wac;

    @Autowired
    private EmployeeMapper employeeMapper;

    private MockMvc mockMvc;

    /** Id of the employee pre-seeded in setUp() for tests that need an existing record. */
    private Long seededId;

    @Before
    public void setUp() {
        mockMvc = MockMvcBuilders.webAppContextSetup(wac)
                .apply(SecurityMockMvcConfigurers.springSecurity())
                .build();

        // Insert one employee directly via mapper so tests that need a pre-existing
        // record can use seededId without going through HTTP POST setup.
        Employee emp = new Employee();
        emp.setName("Pre-seeded Employee");
        emp.setEmail("seeded@example.com");
        emp.setDepartment("HR");
        emp.setSalary(new BigDecimal("40000.00"));
        emp.setHireDate(new Date(1579046400000L)); // 2020-01-15 UTC
        employeeMapper.insert(emp);
        seededId = emp.getId();
    }

    // ─── POST ───────────────────────────────────────────────────────────────

    @Test
    public void createEmployee_returns201WithLocationHeader() throws Exception {
        mockMvc.perform(post("/api/employees")
                        .with(httpBasic("admin", "admin123"))
                        .contentType("application/json")
                        .content(CREATE_JSON))
                .andExpect(status().isCreated())
                .andExpect(header().string("Location", containsString("/api/employees/")));
    }

    @Test
    public void createEmployee_returnsFullEmployeeInBody() throws Exception {
        mockMvc.perform(post("/api/employees")
                        .with(httpBasic("admin", "admin123"))
                        .contentType("application/json")
                        .content(CREATE_JSON))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").isNumber())
                .andExpect(jsonPath("$.name").value("Alice Smith"))
                .andExpect(jsonPath("$.email").value("alice@example.com"))
                .andExpect(jsonPath("$.department").value("Engineering"))
                .andExpect(jsonPath("$.salary").isNumber())
                .andExpect(jsonPath("$.hireDate").isString());
    }

    @Test
    public void createDuplicateEmail_returns409() throws Exception {
        // seededId already has "seeded@example.com" — POST with same email
        String duplicateJson =
                "{\"name\":\"Duplicate\",\"email\":\"seeded@example.com\"," +
                "\"department\":\"IT\",\"salary\":30000.00," +
                "\"hireDate\":1579046400000}";

        mockMvc.perform(post("/api/employees")
                        .with(httpBasic("admin", "admin123"))
                        .contentType("application/json")
                        .content(duplicateJson))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.status").value(409))
                .andExpect(jsonPath("$.message").isString())
                .andExpect(jsonPath("$.timestamp").isString());
    }

    // ─── GET /{id} ──────────────────────────────────────────────────────────

    @Test
    public void getById_returns200WithCorrectEmployee() throws Exception {
        mockMvc.perform(get("/api/employees/{id}", seededId)
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(seededId.intValue()))
                .andExpect(jsonPath("$.name").value("Pre-seeded Employee"))
                .andExpect(jsonPath("$.email").value("seeded@example.com"))
                .andExpect(jsonPath("$.department").value("HR"));
    }

    // ─── GET / ──────────────────────────────────────────────────────────────

    @Test
    public void getAll_returns200WithPageResultStructure() throws Exception {
        mockMvc.perform(get("/api/employees")
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content").isArray())
                .andExpect(jsonPath("$.content", hasSize(1)))  // only seeded employee
                .andExpect(jsonPath("$.totalElements").value(1))
                .andExpect(jsonPath("$.totalPages").value(1))
                .andExpect(jsonPath("$.currentPage").value(0));
    }

    // ─── PUT ──────────────────────────────────────────────────────────────

    @Test
    public void updateEmployee_returns200WithUpdatedFields() throws Exception {
        mockMvc.perform(put("/api/employees/{id}", seededId)
                        .with(httpBasic("admin", "admin123"))
                        .contentType("application/json")
                        .content(UPDATE_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(seededId.intValue()))
                .andExpect(jsonPath("$.name").value("Alice Updated"))
                .andExpect(jsonPath("$.email").value("alice@example.com"))
                .andExpect(jsonPath("$.department").value("Sales"))
                .andExpect(jsonPath("$.salary").isNumber());
    }

    // ─── DELETE ─────────────────────────────────────────────────────────────

    @Test
    public void deleteEmployee_returns204() throws Exception {
        mockMvc.perform(delete("/api/employees/{id}", seededId)
                        .with(httpBasic("admin", "admin123")))
                .andExpect(status().isNoContent());
    }

    @Test
    public void getAfterDelete_returns404() throws Exception {
        // Delete the seeded employee
        mockMvc.perform(delete("/api/employees/{id}", seededId)
                        .with(httpBasic("admin", "admin123")))
                .andExpect(status().isNoContent());

        // Subsequent GET should return 404
        mockMvc.perform(get("/api/employees/{id}", seededId)
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.status").value(404))
                .andExpect(jsonPath("$.message").isString())
                .andExpect(jsonPath("$.timestamp").isString());
    }
}
