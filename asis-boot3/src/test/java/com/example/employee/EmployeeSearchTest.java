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

import static org.hamcrest.Matchers.hasSize;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.httpBasic;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
class EmployeeSearchTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    private void createEmployee(String name, String email, String department) throws Exception {
        EmployeeRequest req = new EmployeeRequest(
                name, email, department,
                new BigDecimal("60000.00"), LocalDate.of(2023, 1, 1));
        mockMvc.perform(post("/api/employees")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req))
                        .with(httpBasic("admin", "admin123")))
                .andExpect(status().isCreated());
    }

    @Test
    void search_byNameOnly_returnsMatchingEmployee() throws Exception {
        mockMvc.perform(get("/api/employees/search")
                        .param("name", "alice")
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(1))
                .andExpect(jsonPath("$.content[0].name").value("Alice Johnson"));
    }

    @Test
    void search_byDepartmentOnly_returnsMatchingEmployee() throws Exception {
        mockMvc.perform(get("/api/employees/search")
                        .param("department", "Marketing")
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(1))
                .andExpect(jsonPath("$.content[0].name").value("Bob Smith"))
                .andExpect(jsonPath("$.content[0].department").value("Marketing"));
    }

    @Test
    void search_byNameAndDepartment_andLogic_bothMatch() throws Exception {
        // Bob Smith is in Marketing — both conditions satisfied
        mockMvc.perform(get("/api/employees/search")
                        .param("name", "bob")
                        .param("department", "Marketing")
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(1))
                .andExpect(jsonPath("$.content[0].name").value("Bob Smith"));
    }

    @Test
    void search_byNameAndDepartment_andLogic_noMatch() throws Exception {
        // Alice is in Engineering, not Marketing — AND means 0 results
        mockMvc.perform(get("/api/employees/search")
                        .param("name", "alice")
                        .param("department", "Marketing")
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(0))
                .andExpect(jsonPath("$.content", hasSize(0)));
    }

    @Test
    void search_partialNameMatch_caseInsensitive() throws Exception {
        // "JOHN" is a case-insensitive partial match for "Alice Johnson"
        mockMvc.perform(get("/api/employees/search")
                        .param("name", "JOHN")
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(1))
                .andExpect(jsonPath("$.content[0].name").value("Alice Johnson"));
    }

    @Test
    void search_noMatchingName_returnsEmptyPage() throws Exception {
        mockMvc.perform(get("/api/employees/search")
                        .param("name", "zzznomatch")
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(0))
                .andExpect(jsonPath("$.totalPages").value(0))
                .andExpect(jsonPath("$.currentPage").value(0))
                .andExpect(jsonPath("$.content", hasSize(0)));
    }

    @Test
    void search_paginatedResults_returnsMultiplePages() throws Exception {
        // Create 3 employees in a unique department to test pagination
        createEmployee("Search Alpha", "search.alpha@example.com", "SearchDept");
        createEmployee("Search Beta",  "search.beta@example.com",  "SearchDept");
        createEmployee("Search Gamma", "search.gamma@example.com", "SearchDept");

        // Page 0, size 2 → 2 results in content, 3 total, 2 pages
        mockMvc.perform(get("/api/employees/search")
                        .param("department", "SearchDept")
                        .param("page", "0")
                        .param("size", "2")
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(3))
                .andExpect(jsonPath("$.totalPages").value(2))
                .andExpect(jsonPath("$.currentPage").value(0))
                .andExpect(jsonPath("$.content", hasSize(2)));

        // Page 1, size 2 → 1 remaining result
        mockMvc.perform(get("/api/employees/search")
                        .param("department", "SearchDept")
                        .param("page", "1")
                        .param("size", "2")
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(3))
                .andExpect(jsonPath("$.currentPage").value(1))
                .andExpect(jsonPath("$.content", hasSize(1)));
    }

    @Test
    void search_partialDepartmentMatch_returnsResults() throws Exception {
        // "neer" is a partial match for "Engineering"
        mockMvc.perform(get("/api/employees/search")
                        .param("department", "neer")
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(1))
                .andExpect(jsonPath("$.content[0].department").value("Engineering"));
    }
}
