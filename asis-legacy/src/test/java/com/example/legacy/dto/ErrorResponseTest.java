package com.example.legacy.dto;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.Before;
import org.junit.Test;

import java.util.Arrays;
import java.util.Collections;

import static org.junit.Assert.*;

/**
 * Tests for ErrorResponse DTO construction and Jackson JSON serialization.
 * Verifies that status, message, timestamp, and fieldErrors serialize correctly.
 */
public class ErrorResponseTest {

    private ObjectMapper objectMapper;

    @Before
    public void setUp() {
        objectMapper = new ObjectMapper();
    }

    @Test
    public void constructor_setsFields() {
        ErrorResponse response = new ErrorResponse(400, "Bad Request", "2023-06-15T10:00:00");
        assertEquals(400, response.getStatus());
        assertEquals("Bad Request", response.getMessage());
        assertEquals("2023-06-15T10:00:00", response.getTimestamp());
        assertNull("fieldErrors should be null when not set", response.getFieldErrors());
    }

    @Test
    public void setFieldErrors_storesAndRetrievesErrors() {
        ErrorResponse response = new ErrorResponse(400, "Validation failed", "2023-06-15T10:00:00");
        ErrorResponse.FieldError fe1 = new ErrorResponse.FieldError("name", "Name is required");
        ErrorResponse.FieldError fe2 = new ErrorResponse.FieldError("email", "Email must be valid");
        response.setFieldErrors(Arrays.asList(fe1, fe2));

        assertNotNull(response.getFieldErrors());
        assertEquals(2, response.getFieldErrors().size());
        assertEquals("name", response.getFieldErrors().get(0).getField());
        assertEquals("Name is required", response.getFieldErrors().get(0).getMessage());
        assertEquals("email", response.getFieldErrors().get(1).getField());
        assertEquals("Email must be valid", response.getFieldErrors().get(1).getMessage());
    }

    @Test
    public void fieldError_constructorAndGetters() {
        ErrorResponse.FieldError fe = new ErrorResponse.FieldError("salary", "Salary must be zero or greater");
        assertEquals("salary", fe.getField());
        assertEquals("Salary must be zero or greater", fe.getMessage());
    }

    @Test
    public void fieldError_settersUpdateFields() {
        ErrorResponse.FieldError fe = new ErrorResponse.FieldError();
        fe.setField("department");
        fe.setMessage("Department is required");
        assertEquals("department", fe.getField());
        assertEquals("Department is required", fe.getMessage());
    }

    @Test
    public void jsonSerialization_includesStatusMessageTimestamp() throws Exception {
        ErrorResponse response = new ErrorResponse(404, "Not Found", "2023-06-15T12:00:00");
        String json = objectMapper.writeValueAsString(response);
        JsonNode node = objectMapper.readTree(json);

        assertEquals(404, node.get("status").asInt());
        assertEquals("Not Found", node.get("message").asText());
        assertEquals("2023-06-15T12:00:00", node.get("timestamp").asText());
    }

    @Test
    public void jsonSerialization_fieldErrorsAsArray() throws Exception {
        ErrorResponse response = new ErrorResponse(400, "Validation failed", "2023-06-15T10:00:00");
        response.setFieldErrors(Arrays.asList(
                new ErrorResponse.FieldError("name", "Name is required"),
                new ErrorResponse.FieldError("email", "Email must be valid")
        ));

        String json = objectMapper.writeValueAsString(response);
        JsonNode node = objectMapper.readTree(json);

        assertTrue("fieldErrors should be an array", node.get("fieldErrors").isArray());
        assertEquals(2, node.get("fieldErrors").size());
        assertEquals("name", node.get("fieldErrors").get(0).get("field").asText());
        assertEquals("Name is required", node.get("fieldErrors").get(0).get("message").asText());
        assertEquals("email", node.get("fieldErrors").get(1).get("field").asText());
        assertEquals("Email must be valid", node.get("fieldErrors").get(1).get("message").asText());
    }

    @Test
    public void jsonSerialization_emptyFieldErrorsAsEmptyArray() throws Exception {
        ErrorResponse response = new ErrorResponse(400, "Error", "2023-06-15T10:00:00");
        response.setFieldErrors(Collections.<ErrorResponse.FieldError>emptyList());

        String json = objectMapper.writeValueAsString(response);
        JsonNode node = objectMapper.readTree(json);

        assertTrue("empty fieldErrors should be an empty array", node.get("fieldErrors").isArray());
        assertEquals(0, node.get("fieldErrors").size());
    }

    @Test
    public void jsonSerialization_nullFieldErrorsAsNull() throws Exception {
        ErrorResponse response = new ErrorResponse(500, "Internal Server Error", "2023-06-15T10:00:00");
        // fieldErrors not set — remains null

        String json = objectMapper.writeValueAsString(response);
        JsonNode node = objectMapper.readTree(json);

        assertTrue("null fieldErrors should serialize as JSON null", node.get("fieldErrors").isNull());
    }
}
