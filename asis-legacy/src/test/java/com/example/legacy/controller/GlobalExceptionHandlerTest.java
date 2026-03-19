package com.example.legacy.controller;

import com.example.legacy.dto.EmployeeRequest;
import com.example.legacy.exception.BadRequestException;
import com.example.legacy.exception.DuplicateEmailException;
import com.example.legacy.exception.NotFoundException;
import org.junit.Before;
import org.junit.Test;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.validation.Valid;

import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

public class GlobalExceptionHandlerTest {

    private MockMvc mockMvc;

    @RestController
    @RequestMapping("/test")
    static class TestController {

        @RequestMapping("/not-found")
        public String notFound() {
            throw new NotFoundException("Employee not found: 999");
        }

        @RequestMapping("/conflict")
        public String conflict() {
            throw new DuplicateEmailException("test@example.com");
        }

        @RequestMapping("/bad-request")
        public String badRequest() {
            throw new BadRequestException("At least one search parameter required");
        }

        @RequestMapping("/server-error")
        public String serverError() {
            throw new RuntimeException("Unexpected error");
        }

        @PostMapping("/validate")
        public ResponseEntity<String> validate(@Valid @RequestBody EmployeeRequest request) {
            return ResponseEntity.ok("ok");
        }
    }

    @Before
    public void setUp() {
        mockMvc = MockMvcBuilders
                .standaloneSetup(new TestController())
                .setControllerAdvice(new GlobalExceptionHandler())
                .build();
    }

    @Test
    public void notFound_returns404WithJson() throws Exception {
        mockMvc.perform(get("/test/not-found"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.status").value(404))
                .andExpect(jsonPath("$.message").value("Employee not found: 999"))
                .andExpect(jsonPath("$.timestamp").isString());
    }

    @Test
    public void duplicateEmail_returns409WithJson() throws Exception {
        mockMvc.perform(get("/test/conflict"))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.status").value(409))
                .andExpect(jsonPath("$.message").value("Email already exists: test@example.com"))
                .andExpect(jsonPath("$.timestamp").isString());
    }

    @Test
    public void badRequest_returns400WithJson() throws Exception {
        mockMvc.perform(get("/test/bad-request"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400))
                .andExpect(jsonPath("$.message").value("At least one search parameter required"))
                .andExpect(jsonPath("$.timestamp").isString());
    }

    @Test
    public void genericException_returns500WithJson() throws Exception {
        mockMvc.perform(get("/test/server-error"))
                .andExpect(status().isInternalServerError())
                .andExpect(jsonPath("$.status").value(500))
                .andExpect(jsonPath("$.message").value("Internal server error"))
                .andExpect(jsonPath("$.timestamp").isString());
    }

    @Test
    public void validationFailure_returns400WithFieldErrors() throws Exception {
        String invalidJson = "{\"name\":\"\",\"email\":\"not-an-email\","
                + "\"department\":\"IT\",\"salary\":-1}";
        mockMvc.perform(post("/test/validate")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(invalidJson))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400))
                .andExpect(jsonPath("$.message").value("Validation failed"))
                .andExpect(jsonPath("$.fieldErrors").isArray())
                .andExpect(jsonPath("$.fieldErrors", hasSize(greaterThan(0))))
                .andExpect(jsonPath("$.timestamp").isString());
    }

    @Test
    public void validationFailure_fieldErrorsContainFieldAndMessage() throws Exception {
        // Send a request with blank name to get a specific fieldError for "name"
        String invalidJson = "{\"name\":\"\",\"email\":\"valid@example.com\","
                + "\"department\":\"IT\",\"salary\":1000,\"hireDate\":\"2020-01-01\"}";
        mockMvc.perform(post("/test/validate")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(invalidJson))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.fieldErrors[*].field", hasItem("name")))
                .andExpect(jsonPath("$.fieldErrors[*].message", hasItem("Name is required")));
    }
}
