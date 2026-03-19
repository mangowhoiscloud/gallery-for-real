package com.example.employee.controller;

import com.example.employee.config.SecurityConfig;
import com.example.employee.dto.EmployeeRequest;
import com.example.employee.dto.EmployeeResponse;
import com.example.employee.dto.PageResponse;
import com.example.employee.exception.DuplicateEmailException;
import com.example.employee.exception.EmployeeNotFoundException;
import com.example.employee.service.EmployeeService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doNothing;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(EmployeeController.class)
@Import(SecurityConfig.class)
class EmployeeControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private EmployeeService service;

    private EmployeeResponse sampleResponse() {
        return new EmployeeResponse(
                1L, "Alice", "alice@example.com", "Engineering",
                new BigDecimal("90000"), LocalDate.of(2022, 1, 15),
                LocalDateTime.of(2022, 1, 15, 9, 0),
                LocalDateTime.of(2022, 1, 15, 9, 0));
    }

    private EmployeeRequest sampleRequest() {
        return new EmployeeRequest(
                "Alice", "alice@example.com", "Engineering",
                new BigDecimal("90000"), LocalDate.of(2022, 1, 15));
    }

    @Test
    @WithMockUser(roles = "USER")
    void findAll_asUser_returnsPagedList() throws Exception {
        PageResponse<EmployeeResponse> page = new PageResponse<>(
                List.of(sampleResponse()), 0, 1, 1L);
        when(service.findAll(0, 10)).thenReturn(page);

        mockMvc.perform(get("/api/employees"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content[0].name").value("Alice"))
                .andExpect(jsonPath("$.currentPage").value(0))
                .andExpect(jsonPath("$.totalElements").value(1));
    }

    @Test
    @WithMockUser(roles = "USER")
    void findById_asUser_returnsEmployee() throws Exception {
        when(service.findById(1L)).thenReturn(sampleResponse());

        mockMvc.perform(get("/api/employees/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(1))
                .andExpect(jsonPath("$.email").value("alice@example.com"));
    }

    @Test
    @WithMockUser(roles = "USER")
    void findById_notFound_returns404WithProblemDetail() throws Exception {
        when(service.findById(999L)).thenThrow(new EmployeeNotFoundException(999L));

        mockMvc.perform(get("/api/employees/999"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.status").value(404))
                .andExpect(jsonPath("$.title").value("Not Found"));
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void create_asAdmin_returns201WithLocation() throws Exception {
        when(service.create(any())).thenReturn(sampleResponse());

        mockMvc.perform(post("/api/employees")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(sampleRequest())))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").value(1))
                .andExpect(header().exists("Location"));
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void create_invalidBody_returns400WithFieldErrors() throws Exception {
        EmployeeRequest invalid = new EmployeeRequest(
                "", "not-an-email", "Engineering",
                new BigDecimal("90000"), LocalDate.of(2022, 1, 15));

        mockMvc.perform(post("/api/employees")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(invalid)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400))
                .andExpect(jsonPath("$.title").value("Bad Request"));
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void create_duplicateEmail_returns409WithProblemDetail() throws Exception {
        when(service.create(any())).thenThrow(new DuplicateEmailException("alice@example.com"));

        mockMvc.perform(post("/api/employees")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(sampleRequest())))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.status").value(409))
                .andExpect(jsonPath("$.title").value("Conflict"));
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void update_asAdmin_returns200() throws Exception {
        when(service.update(eq(1L), any())).thenReturn(sampleResponse());

        mockMvc.perform(put("/api/employees/1")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(sampleRequest())))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name").value("Alice"));
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void delete_asAdmin_returns204() throws Exception {
        doNothing().when(service).delete(1L);

        mockMvc.perform(delete("/api/employees/1"))
                .andExpect(status().isNoContent());
    }

    @Test
    @WithMockUser(roles = "USER")
    void search_asUser_returnsResults() throws Exception {
        PageResponse<EmployeeResponse> page = new PageResponse<>(
                List.of(sampleResponse()), 0, 1, 1L);
        when(service.search("Alice", "Engineering", 0, 10)).thenReturn(page);

        mockMvc.perform(get("/api/employees/search")
                        .param("name", "Alice")
                        .param("department", "Engineering"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content[0].department").value("Engineering"));
    }

    @Test
    void get_unauthenticated_returns401() throws Exception {
        mockMvc.perform(get("/api/employees"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    @WithMockUser(roles = "USER")
    void post_asUser_returns403() throws Exception {
        mockMvc.perform(post("/api/employees")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(sampleRequest())))
                .andExpect(status().isForbidden());
    }

    @Test
    @WithMockUser(roles = "USER")
    void delete_asUser_returns403() throws Exception {
        mockMvc.perform(delete("/api/employees/1"))
                .andExpect(status().isForbidden());
    }
}
