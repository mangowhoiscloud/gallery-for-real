package com.example.legacy.config;

import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.http.ResponseEntity;
import org.springframework.security.test.web.servlet.setup.SecurityMockMvcConfigurers;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;
import org.springframework.test.context.web.WebAppConfiguration;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.context.WebApplicationContext;
import org.springframework.web.servlet.config.annotation.EnableWebMvc;

import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.httpBasic;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Security integration tests verifying role-based access control and
 * JSON error response format for 401/403 responses.
 * <p>
 * Uses a stub EmployeeController so these tests remain valid before
 * Item 16 (real EmployeeController) is implemented.
 */
@RunWith(SpringJUnit4ClassRunner.class)
@WebAppConfiguration
@ContextConfiguration(classes = SecurityIntegrationTest.TestConfig.class)
public class SecurityIntegrationTest {

    /**
     * Minimal web config that pulls in SecurityConfig and registers a stub controller
     * at /api/employees so security rules can be exercised end-to-end.
     */
    @Configuration
    @Import(SecurityConfig.class)
    @EnableWebMvc
    static class TestConfig {
        @Bean
        public StubEmployeeController stubEmployeeController() {
            return new StubEmployeeController();
        }
    }

    /** Minimal controller that satisfies routing without a real service layer. */
    @RestController
    @RequestMapping("/api/employees")
    static class StubEmployeeController {
        @GetMapping
        public ResponseEntity<String> list() {
            return ResponseEntity.ok("[]");
        }

        @PostMapping
        public ResponseEntity<String> create() {
            return ResponseEntity.ok("{}");
        }
    }

    @Autowired
    private WebApplicationContext wac;

    private MockMvc mockMvc;

    @Before
    public void setUp() {
        mockMvc = MockMvcBuilders.webAppContextSetup(wac)
                .apply(SecurityMockMvcConfigurers.springSecurity())
                .build();
    }

    // --- Unauthenticated access ---

    @Test
    public void unauthenticatedGet_returns401WithJsonBody() throws Exception {
        mockMvc.perform(get("/api/employees"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.status").value(401))
                .andExpect(jsonPath("$.message").value("Unauthorized"))
                .andExpect(jsonPath("$.timestamp").isString());
    }

    @Test
    public void unauthenticatedPost_returns401WithJsonBody() throws Exception {
        mockMvc.perform(post("/api/employees")
                        .contentType("application/json")
                        .content("{}"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.status").value(401))
                .andExpect(jsonPath("$.message").value("Unauthorized"))
                .andExpect(jsonPath("$.timestamp").isString());
    }

    // --- USER role ---

    @Test
    public void userGet_isAllowed() throws Exception {
        mockMvc.perform(get("/api/employees")
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isOk());
    }

    @Test
    public void userPost_returns403WithJsonBody() throws Exception {
        mockMvc.perform(post("/api/employees")
                        .with(httpBasic("user", "user123"))
                        .contentType("application/json")
                        .content("{}"))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.status").value(403))
                .andExpect(jsonPath("$.message").value("Forbidden"))
                .andExpect(jsonPath("$.timestamp").isString());
    }

    // --- ADMIN role ---

    @Test
    public void adminGet_isAllowed() throws Exception {
        mockMvc.perform(get("/api/employees")
                        .with(httpBasic("admin", "admin123")))
                .andExpect(status().isOk());
    }

    @Test
    public void adminPost_isAllowed() throws Exception {
        mockMvc.perform(post("/api/employees")
                        .with(httpBasic("admin", "admin123"))
                        .contentType("application/json")
                        .content("{}"))
                .andExpect(status().isOk());
    }
}
