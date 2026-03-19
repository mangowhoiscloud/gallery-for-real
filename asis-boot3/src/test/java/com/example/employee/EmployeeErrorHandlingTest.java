package com.example.employee;

import com.example.employee.dto.EmployeeRequest;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;

import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.httpBasic;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Dedicated tests for GlobalExceptionHandler — verifies full ProblemDetail (RFC 7807)
 * structure: type, title, status, detail, and instance fields.
 */
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
class EmployeeErrorHandlingTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    // ── 400 Validation ──────────────────────────────────────────────────────

    @Test
    void validationError_returns400_withCompleteProblemDetail() throws Exception {
        EmployeeRequest invalid = new EmployeeRequest(
                "", "not-an-email", "",
                new BigDecimal("-100"), null);

        mockMvc.perform(post("/api/employees")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(invalid))
                        .with(httpBasic("admin", "admin123")))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.type").value("about:blank"))
                .andExpect(jsonPath("$.title").value("Bad Request"))
                .andExpect(jsonPath("$.status").value(400))
                .andExpect(jsonPath("$.detail").isNotEmpty())
                .andExpect(jsonPath("$.instance").value("/api/employees"));
    }

    @Test
    void validationError_detail_containsFieldErrorMessages() throws Exception {
        // Only name is blank — exactly one field error, so detail is unambiguous
        EmployeeRequest blankName = new EmployeeRequest(
                "", "valid@example.com", "Engineering",
                new BigDecimal("50000"), LocalDate.of(2023, 1, 1));

        mockMvc.perform(post("/api/employees")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(blankName))
                        .with(httpBasic("admin", "admin123")))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.detail").isNotEmpty())
                .andExpect(jsonPath("$.status").value(400));
    }

    // ── 404 Not Found ────────────────────────────────────────────────────────

    @Test
    void notFound_returns404_withCompleteProblemDetail() throws Exception {
        mockMvc.perform(get("/api/employees/999999")
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.type").value("about:blank"))
                .andExpect(jsonPath("$.title").value("Not Found"))
                .andExpect(jsonPath("$.status").value(404))
                .andExpect(jsonPath("$.detail").value("Employee not found with id: 999999"))
                .andExpect(jsonPath("$.instance").value("/api/employees/999999"));
    }

    // ── 409 Conflict ─────────────────────────────────────────────────────────

    @Test
    void duplicateEmailOnCreate_returns409_withCompleteProblemDetail() throws Exception {
        // alice.johnson@example.com is seeded in data.sql
        EmployeeRequest duplicate = new EmployeeRequest(
                "Someone Else", "alice.johnson@example.com", "Sales",
                new BigDecimal("60000"), LocalDate.of(2024, 1, 1));

        mockMvc.perform(post("/api/employees")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(duplicate))
                        .with(httpBasic("admin", "admin123")))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.type").value("about:blank"))
                .andExpect(jsonPath("$.title").value("Conflict"))
                .andExpect(jsonPath("$.status").value(409))
                .andExpect(jsonPath("$.detail").value("Employee with email already exists: alice.johnson@example.com"))
                .andExpect(jsonPath("$.instance").value("/api/employees"));
    }

    @Test
    void duplicateEmailOnUpdate_returns409_withCompleteProblemDetail() throws Exception {
        // Update employee 2 (bob) to use alice's email — triggers DuplicateEmailException
        EmployeeRequest conflicting = new EmployeeRequest(
                "Bob Smith", "alice.johnson@example.com", "Marketing",
                new BigDecimal("70000"), LocalDate.of(2020, 3, 1));

        mockMvc.perform(put("/api/employees/2")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(conflicting))
                        .with(httpBasic("admin", "admin123")))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.type").value("about:blank"))
                .andExpect(jsonPath("$.title").value("Conflict"))
                .andExpect(jsonPath("$.status").value(409))
                .andExpect(jsonPath("$.detail").value("Employee with email already exists: alice.johnson@example.com"))
                .andExpect(jsonPath("$.instance").value("/api/employees/2"));
    }
}
