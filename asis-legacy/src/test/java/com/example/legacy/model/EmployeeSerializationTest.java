package com.example.legacy.model;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import org.junit.Before;
import org.junit.Test;

import java.math.BigDecimal;
import java.sql.Timestamp;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.TimeZone;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

/**
 * Tests for Employee model Jackson date serialization.
 * Covers Item 11 (partial): hireDate as "yyyy-MM-dd", timestamps as "yyyy-MM-dd'T'HH:mm:ss".
 *
 * ObjectMapper must use local timezone so @JsonFormat annotations inherit server timezone,
 * matching the spec requirement "assume server timezone, no timezone suffix".
 */
public class EmployeeSerializationTest {

    private ObjectMapper objectMapper;

    @Before
    public void setUp() {
        objectMapper = new ObjectMapper();
        objectMapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
        // Use local timezone so @JsonFormat pattern output matches local wall-clock time,
        // consistent with spec: "ISO 8601, no timezone suffix — assume server timezone"
        objectMapper.setTimeZone(TimeZone.getDefault());
    }

    @Test
    public void hireDateSerializesAsYyyyMmDd() throws Exception {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
        Date hireDate = sdf.parse("2023-06-15");

        Employee employee = new Employee();
        employee.setId(1L);
        employee.setName("John Doe");
        employee.setEmail("john@example.com");
        employee.setDepartment("Engineering");
        employee.setSalary(new BigDecimal("75000.00"));
        employee.setHireDate(hireDate);

        String json = objectMapper.writeValueAsString(employee);

        assertTrue("hireDate should be serialized as yyyy-MM-dd string",
                json.contains("\"hireDate\":\"2023-06-15\""));
    }

    @Test
    public void createdAtSerializesAsIso8601WithoutTimezone() throws Exception {
        // Use a fixed timestamp: 2023-01-10 08:30:00
        Timestamp createdAt = Timestamp.valueOf("2023-01-10 08:30:00");

        Employee employee = new Employee();
        employee.setId(2L);
        employee.setName("Jane Smith");
        employee.setEmail("jane@example.com");
        employee.setDepartment("HR");
        employee.setSalary(new BigDecimal("60000.00"));
        employee.setCreatedAt(createdAt);

        String json = objectMapper.writeValueAsString(employee);

        assertTrue("createdAt should be serialized as yyyy-MM-dd'T'HH:mm:ss",
                json.contains("\"createdAt\":\"2023-01-10T08:30:00\""));
    }

    @Test
    public void updatedAtSerializesAsIso8601WithoutTimezone() throws Exception {
        Timestamp updatedAt = Timestamp.valueOf("2024-03-19 14:45:59");

        Employee employee = new Employee();
        employee.setId(3L);
        employee.setName("Bob Brown");
        employee.setEmail("bob@example.com");
        employee.setDepartment("Finance");
        employee.setSalary(new BigDecimal("80000.00"));
        employee.setUpdatedAt(updatedAt);

        String json = objectMapper.writeValueAsString(employee);

        assertTrue("updatedAt should be serialized as yyyy-MM-dd'T'HH:mm:ss",
                json.contains("\"updatedAt\":\"2024-03-19T14:45:59\""));
    }

    @Test
    public void nullDatesSerializeAsNull() throws Exception {
        Employee employee = new Employee();
        employee.setId(4L);
        employee.setName("Alice Green");
        employee.setEmail("alice@example.com");
        employee.setDepartment("Legal");
        employee.setSalary(new BigDecimal("90000.00"));
        // hireDate, createdAt, updatedAt all null

        String json = objectMapper.writeValueAsString(employee);

        assertTrue("null hireDate should serialize as null", json.contains("\"hireDate\":null"));
        assertTrue("null createdAt should serialize as null", json.contains("\"createdAt\":null"));
        assertTrue("null updatedAt should serialize as null", json.contains("\"updatedAt\":null"));
    }

    @Test
    public void allFieldsRoundTrip() throws Exception {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
        Date hireDate = sdf.parse("2020-07-01");
        Timestamp createdAt = Timestamp.valueOf("2020-07-01 09:00:00");
        Timestamp updatedAt = Timestamp.valueOf("2023-12-31 23:59:59");

        Employee original = new Employee();
        original.setId(5L);
        original.setName("Carol White");
        original.setEmail("carol@example.com");
        original.setDepartment("Marketing");
        original.setSalary(new BigDecimal("55000.50"));
        original.setHireDate(hireDate);
        original.setCreatedAt(createdAt);
        original.setUpdatedAt(updatedAt);

        String json = objectMapper.writeValueAsString(original);
        Employee deserialized = objectMapper.readValue(json, Employee.class);

        assertEquals(original.getId(), deserialized.getId());
        assertEquals(original.getName(), deserialized.getName());
        assertEquals(original.getEmail(), deserialized.getEmail());
        assertEquals(original.getDepartment(), deserialized.getDepartment());
        assertEquals(0, original.getSalary().compareTo(deserialized.getSalary()));
        assertEquals("yyyy-MM-dd parse should match",
                sdf.format(original.getHireDate()), sdf.format(deserialized.getHireDate()));
    }
}
