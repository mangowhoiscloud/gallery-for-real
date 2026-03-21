package com.example.shop.controller;

import com.example.shop.dto.ErrorResponse;
import com.example.shop.exception.BusinessException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.Before;
import org.junit.Test;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.NoHandlerFoundException;

import javax.validation.Valid;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Size;

import static org.junit.Assert.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

public class GlobalExceptionHandlerTest {

    private MockMvc mockMvc;
    private ObjectMapper objectMapper;

    @RestController
    static class TestController {

        @GetMapping("/test/business-conflict")
        public void throwConflict() {
            throw new BusinessException(HttpStatus.CONFLICT, "Email already exists");
        }

        @GetMapping("/test/business-bad-request")
        public void throwBadRequest() {
            throw new BusinessException(HttpStatus.BAD_REQUEST, "Invalid cart state");
        }

        @GetMapping("/test/access-denied")
        public void throwAccessDenied() {
            throw new AccessDeniedException("Forbidden resource");
        }

        @GetMapping("/test/no-handler")
        public void throwNoHandler() throws NoHandlerFoundException {
            throw new NoHandlerFoundException("GET", "/api/unknown", null);
        }

        @GetMapping("/test/generic-error")
        public void throwGeneric() {
            throw new RuntimeException("Unexpected failure");
        }

        @PostMapping("/test/validate")
        public void validateBody(@Valid @RequestBody ValidatedRequest req) {}
    }

    static class ValidatedRequest {
        @NotNull(message = "may not be null")
        @Size(min = 1, max = 50, message = "size must be between 1 and 50")
        private String name;

        public String getName() { return name; }
        public void setName(String name) { this.name = name; }
    }

    @Before
    public void setUp() {
        objectMapper = new ObjectMapper();
        mockMvc = MockMvcBuilders
                .standaloneSetup(new TestController())
                .setControllerAdvice(new GlobalExceptionHandler())
                .build();
    }

    @Test
    public void businessExceptionConflictReturns409() throws Exception {
        MvcResult result = mockMvc.perform(get("/test/business-conflict"))
                .andExpect(status().isConflict())
                .andReturn();

        ErrorResponse body = objectMapper.readValue(result.getResponse().getContentAsString(), ErrorResponse.class);
        assertEquals(409, body.getStatus());
        assertEquals("Conflict", body.getError());
        assertEquals("Email already exists", body.getMessage());
        assertNotNull(body.getTimestamp());
    }

    @Test
    public void businessExceptionBadRequestReturns400() throws Exception {
        MvcResult result = mockMvc.perform(get("/test/business-bad-request"))
                .andExpect(status().isBadRequest())
                .andReturn();

        ErrorResponse body = objectMapper.readValue(result.getResponse().getContentAsString(), ErrorResponse.class);
        assertEquals(400, body.getStatus());
        assertEquals("Bad Request", body.getError());
        assertEquals("Invalid cart state", body.getMessage());
    }

    @Test
    public void accessDeniedReturns403() throws Exception {
        MvcResult result = mockMvc.perform(get("/test/access-denied"))
                .andExpect(status().isForbidden())
                .andReturn();

        ErrorResponse body = objectMapper.readValue(result.getResponse().getContentAsString(), ErrorResponse.class);
        assertEquals(403, body.getStatus());
        assertEquals("Forbidden", body.getError());
        assertEquals("Access denied", body.getMessage());
    }

    @Test
    public void noHandlerFoundReturns404() throws Exception {
        MvcResult result = mockMvc.perform(get("/test/no-handler"))
                .andExpect(status().isNotFound())
                .andReturn();

        ErrorResponse body = objectMapper.readValue(result.getResponse().getContentAsString(), ErrorResponse.class);
        assertEquals(404, body.getStatus());
        assertEquals("Not Found", body.getError());
        assertNotNull(body.getMessage());
    }

    @Test
    public void genericExceptionReturns500() throws Exception {
        MvcResult result = mockMvc.perform(get("/test/generic-error"))
                .andExpect(status().isInternalServerError())
                .andReturn();

        ErrorResponse body = objectMapper.readValue(result.getResponse().getContentAsString(), ErrorResponse.class);
        assertEquals(500, body.getStatus());
        assertEquals("Internal Server Error", body.getError());
        assertEquals("An unexpected error occurred", body.getMessage());
    }

    @Test
    public void validationFailureReturns400WithFieldMessage() throws Exception {
        String requestJson = "{}";

        MvcResult result = mockMvc.perform(post("/test/validate")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
                .andExpect(status().isBadRequest())
                .andReturn();

        ErrorResponse body = objectMapper.readValue(result.getResponse().getContentAsString(), ErrorResponse.class);
        assertEquals(400, body.getStatus());
        assertEquals("Bad Request", body.getError());
        assertTrue("Message should contain field name", body.getMessage().contains("name"));
        assertTrue("Message should contain constraint message", body.getMessage().contains("null"));
    }
}
