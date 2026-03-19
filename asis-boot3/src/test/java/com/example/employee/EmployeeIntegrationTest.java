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
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;

import static org.hamcrest.Matchers.hasSize;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.httpBasic;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
class EmployeeIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    private EmployeeRequest newEmployeeRequest() {
        return new EmployeeRequest(
                "Test User", "test.user@example.com", "Engineering",
                new BigDecimal("80000.00"), LocalDate.of(2023, 6, 1));
    }

    @Test
    void contextLoads() {
        // Verifies the full application context starts with H2 test profile
    }

    @Test
    void findAll_returnsSeededEmployees() throws Exception {
        mockMvc.perform(get("/api/employees")
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(5))
                .andExpect(jsonPath("$.content", hasSize(5)))
                .andExpect(jsonPath("$.currentPage").value(0))
                .andExpect(jsonPath("$.totalPages").value(1));
    }

    @Test
    void findAll_withPagination_returnsCorrectPages() throws Exception {
        mockMvc.perform(get("/api/employees")
                        .param("page", "0")
                        .param("size", "2")
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content", hasSize(2)))
                .andExpect(jsonPath("$.totalElements").value(5))
                .andExpect(jsonPath("$.totalPages").value(3))
                .andExpect(jsonPath("$.currentPage").value(0));

        mockMvc.perform(get("/api/employees")
                        .param("page", "2")
                        .param("size", "2")
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content", hasSize(1)))
                .andExpect(jsonPath("$.currentPage").value(2));
    }

    @Test
    void findById_seedEmployee_returnsData() throws Exception {
        mockMvc.perform(get("/api/employees/1")
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(1))
                .andExpect(jsonPath("$.name").value("Alice Johnson"))
                .andExpect(jsonPath("$.email").value("alice.johnson@example.com"))
                .andExpect(jsonPath("$.department").value("Engineering"));
    }

    @Test
    void findById_nonExistent_returns404() throws Exception {
        mockMvc.perform(get("/api/employees/999")
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.status").value(404))
                .andExpect(jsonPath("$.title").value("Not Found"));
    }

    @Test
    void crudLifecycle_createReadUpdateDelete() throws Exception {
        // CREATE
        MvcResult createResult = mockMvc.perform(post("/api/employees")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(newEmployeeRequest()))
                        .with(httpBasic("admin", "admin123")))
                .andExpect(status().isCreated())
                .andExpect(header().exists("Location"))
                .andExpect(jsonPath("$.name").value("Test User"))
                .andExpect(jsonPath("$.email").value("test.user@example.com"))
                .andExpect(jsonPath("$.id").isNumber())
                .andExpect(jsonPath("$.createdAt").isNotEmpty())
                .andExpect(jsonPath("$.updatedAt").isNotEmpty())
                .andReturn();

        Long createdId = objectMapper.readTree(
                createResult.getResponse().getContentAsString()).get("id").asLong();

        // READ back
        mockMvc.perform(get("/api/employees/" + createdId)
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(createdId))
                .andExpect(jsonPath("$.name").value("Test User"));

        // UPDATE
        EmployeeRequest updateRequest = new EmployeeRequest(
                "Updated User", "test.user@example.com", "Marketing",
                new BigDecimal("95000.00"), LocalDate.of(2023, 6, 1));

        mockMvc.perform(put("/api/employees/" + createdId)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(updateRequest))
                        .with(httpBasic("admin", "admin123")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name").value("Updated User"))
                .andExpect(jsonPath("$.department").value("Marketing"))
                .andExpect(jsonPath("$.salary").value(95000.00));

        // Verify update persisted
        mockMvc.perform(get("/api/employees/" + createdId)
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name").value("Updated User"));

        // DELETE
        mockMvc.perform(delete("/api/employees/" + createdId)
                        .with(httpBasic("admin", "admin123")))
                .andExpect(status().isNoContent());

        // Verify deleted
        mockMvc.perform(get("/api/employees/" + createdId)
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isNotFound());
    }

    @Test
    void create_duplicateEmailWithSeedData_returns409() throws Exception {
        EmployeeRequest duplicate = new EmployeeRequest(
                "Another Alice", "alice.johnson@example.com", "Sales",
                new BigDecimal("60000.00"), LocalDate.of(2024, 1, 1));

        mockMvc.perform(post("/api/employees")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(duplicate))
                        .with(httpBasic("admin", "admin123")))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.status").value(409))
                .andExpect(jsonPath("$.title").value("Conflict"));
    }

    @Test
    void update_duplicateEmailOfAnotherEmployee_returns409() throws Exception {
        EmployeeRequest badUpdate = new EmployeeRequest(
                "Bob Smith", "alice.johnson@example.com", "Marketing",
                new BigDecimal("65000.00"), LocalDate.of(2019, 6, 1));

        mockMvc.perform(put("/api/employees/2")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(badUpdate))
                        .with(httpBasic("admin", "admin123")))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.status").value(409));
    }

    @Test
    void search_byName_caseInsensitivePartialMatch() throws Exception {
        mockMvc.perform(get("/api/employees/search")
                        .param("name", "alice")
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(1))
                .andExpect(jsonPath("$.content[0].name").value("Alice Johnson"));
    }

    @Test
    void search_byDepartment_returnsMatchingResults() throws Exception {
        mockMvc.perform(get("/api/employees/search")
                        .param("department", "Engineering")
                        .with(httpBasic("user", "user123")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(1))
                .andExpect(jsonPath("$.content[0].department").value("Engineering"));
    }

    @Test
    void totalElementCount_afterCreateAndDelete_isCorrect() throws Exception {
        mockMvc.perform(get("/api/employees")
                        .with(httpBasic("user", "user123")))
                .andExpect(jsonPath("$.totalElements").value(5));

        MvcResult result = mockMvc.perform(post("/api/employees")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(newEmployeeRequest()))
                        .with(httpBasic("admin", "admin123")))
                .andExpect(status().isCreated())
                .andReturn();

        Long newId = objectMapper.readTree(
                result.getResponse().getContentAsString()).get("id").asLong();

        mockMvc.perform(get("/api/employees")
                        .with(httpBasic("user", "user123")))
                .andExpect(jsonPath("$.totalElements").value(6));

        mockMvc.perform(delete("/api/employees/" + newId)
                        .with(httpBasic("admin", "admin123")))
                .andExpect(status().isNoContent());

        mockMvc.perform(get("/api/employees")
                        .with(httpBasic("user", "user123")))
                .andExpect(jsonPath("$.totalElements").value(5));
    }

    @Test
    void create_invalidRequest_returns400() throws Exception {
        EmployeeRequest invalid = new EmployeeRequest(
                "", "not-an-email", "",
                new BigDecimal("-1"), null);

        mockMvc.perform(post("/api/employees")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(invalid))
                        .with(httpBasic("admin", "admin123")))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400))
                .andExpect(jsonPath("$.title").value("Bad Request"))
                .andExpect(jsonPath("$.detail").isNotEmpty());
    }
}
