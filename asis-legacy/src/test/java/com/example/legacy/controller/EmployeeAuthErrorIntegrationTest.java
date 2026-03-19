package com.example.legacy.controller;

import com.example.legacy.config.SecurityConfig;
import com.example.legacy.config.TestAppConfig;
import com.example.legacy.config.WebConfig;
import com.example.legacy.mapper.EmployeeMapper;
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

import static org.hamcrest.Matchers.greaterThanOrEqualTo;
import static org.hamcrest.Matchers.hasSize;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.httpBasic;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Integration tests for authentication, authorization, validation errors, and 404 handling.
 *
 * Verifies:
 * - Unauthenticated requests → 401 JSON ErrorResponse
 * - Insufficient-role requests → 403 JSON ErrorResponse
 * - Invalid request bodies → 400 with populated fieldErrors array
 * - Operations on non-existent resources → 404 JSON ErrorResponse
 * - All error responses include status, message, and timestamp fields
 */
@RunWith(SpringJUnit4ClassRunner.class)
@WebAppConfiguration
@ContextConfiguration(classes = EmployeeAuthErrorIntegrationTest.TestConfig.class)
@Transactional
public class EmployeeAuthErrorIntegrationTest {

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

    // Guaranteed non-existent id — large enough to never collide with H2 auto-increment ids
    private static final long NON_EXISTENT_ID = 999999L;

    @Autowired
    private WebApplicationContext wac;

    private MockMvc mockMvc;

    @Before
    public void setUp() {
        mockMvc = MockMvcBuilders.webAppContextSetup(wac)
                .apply(SecurityMockMvcConfigurers.springSecurity())
                .build();
    }

    // ─── Unauthenticated / Authorization errors ───────────────────────────────

    @Test
    public void unauthenticatedGet_returns401Json() throws Exception {
        mockMvc.perform(get("/api/employees"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.status").value(401))
                .andExpect(jsonPath("$.message").isString())
                .andExpect(jsonPath("$.timestamp").isString());
    }

    @Test
    public void userRolePost_returns403Json() throws Exception {
        String validJson = "{\"name\":\"Test\",\"email\":\"test@example.com\"," +
                "\"department\":\"IT\",\"salary\":30000.00," +
                "\"hireDate\":1579046400000}";

        mockMvc.perform(post("/api/employees")
                        .with(httpBasic("user", "user123"))
                        .contentType("application/json")
                        .content(validJson))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.status").value(403))
                .andExpect(jsonPath("$.message").isString())
                .andExpect(jsonPath("$.timestamp").isString());
    }

    // ─── 404 — non-existent resources ────────────────────────────────────────

    @Test
    public void putNonExistentEmployee_returns404() throws Exception {
        String json = "{\"name\":\"Ghost\",\"email\":\"ghost@example.com\"," +
                "\"department\":\"IT\",\"salary\":40000.00," +
                "\"hireDate\":1579046400000}";

        mockMvc.perform(put("/api/employees/{id}", NON_EXISTENT_ID)
                        .with(httpBasic("admin", "admin123"))
                        .contentType("application/json")
                        .content(json))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.status").value(404))
                .andExpect(jsonPath("$.message").isString())
                .andExpect(jsonPath("$.timestamp").isString());
    }

    @Test
    public void deleteNonExistentEmployee_returns404() throws Exception {
        mockMvc.perform(delete("/api/employees/{id}", NON_EXISTENT_ID)
                        .with(httpBasic("admin", "admin123")))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.status").value(404))
                .andExpect(jsonPath("$.message").isString())
                .andExpect(jsonPath("$.timestamp").isString());
    }

    // ─── Validation errors (400 + fieldErrors) ───────────────────────────────

    @Test
    public void postWithBlankName_returns400WithNameFieldError() throws Exception {
        String json = "{\"name\":\"\",\"email\":\"valid@example.com\"," +
                "\"department\":\"HR\",\"salary\":30000.00," +
                "\"hireDate\":1579046400000}";

        mockMvc.perform(post("/api/employees")
                        .with(httpBasic("admin", "admin123"))
                        .contentType("application/json")
                        .content(json))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400))
                .andExpect(jsonPath("$.message").isString())
                .andExpect(jsonPath("$.timestamp").isString())
                .andExpect(jsonPath("$.fieldErrors").isArray())
                .andExpect(jsonPath("$.fieldErrors", hasSize(1)))
                .andExpect(jsonPath("$.fieldErrors[0].field").value("name"))
                .andExpect(jsonPath("$.fieldErrors[0].message").isString());
    }

    @Test
    public void postWithInvalidEmail_returns400WithEmailFieldError() throws Exception {
        String json = "{\"name\":\"John Doe\",\"email\":\"not-an-email\"," +
                "\"department\":\"HR\",\"salary\":30000.00," +
                "\"hireDate\":1579046400000}";

        mockMvc.perform(post("/api/employees")
                        .with(httpBasic("admin", "admin123"))
                        .contentType("application/json")
                        .content(json))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400))
                .andExpect(jsonPath("$.message").isString())
                .andExpect(jsonPath("$.timestamp").isString())
                .andExpect(jsonPath("$.fieldErrors").isArray())
                .andExpect(jsonPath("$.fieldErrors", hasSize(1)))
                .andExpect(jsonPath("$.fieldErrors[0].field").value("email"))
                .andExpect(jsonPath("$.fieldErrors[0].message").isString());
    }

    @Test
    public void postWithNegativeSalary_returns400WithSalaryFieldError() throws Exception {
        String json = "{\"name\":\"John Doe\",\"email\":\"john@example.com\"," +
                "\"department\":\"HR\",\"salary\":-500.00," +
                "\"hireDate\":1579046400000}";

        mockMvc.perform(post("/api/employees")
                        .with(httpBasic("admin", "admin123"))
                        .contentType("application/json")
                        .content(json))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400))
                .andExpect(jsonPath("$.message").isString())
                .andExpect(jsonPath("$.timestamp").isString())
                .andExpect(jsonPath("$.fieldErrors").isArray())
                .andExpect(jsonPath("$.fieldErrors", hasSize(1)))
                .andExpect(jsonPath("$.fieldErrors[0].field").value("salary"))
                .andExpect(jsonPath("$.fieldErrors[0].message").isString());
    }

    @Test
    public void postWithMultipleViolations_returns400WithMultipleFieldErrors() throws Exception {
        // blank name + invalid email + negative salary → at least 3 fieldErrors
        String json = "{\"name\":\"\",\"email\":\"bad\"," +
                "\"department\":\"HR\",\"salary\":-1.00," +
                "\"hireDate\":1579046400000}";

        mockMvc.perform(post("/api/employees")
                        .with(httpBasic("admin", "admin123"))
                        .contentType("application/json")
                        .content(json))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400))
                .andExpect(jsonPath("$.message").isString())
                .andExpect(jsonPath("$.timestamp").isString())
                .andExpect(jsonPath("$.fieldErrors").isArray())
                .andExpect(jsonPath("$.fieldErrors", hasSize(greaterThanOrEqualTo(3))))
                .andExpect(jsonPath("$.fieldErrors[0].field").isString())
                .andExpect(jsonPath("$.fieldErrors[0].message").isString());
    }
}
