package com.example.legacy.dto;

import org.junit.BeforeClass;
import org.junit.Test;

import javax.validation.ConstraintViolation;
import javax.validation.Validation;
import javax.validation.Validator;
import javax.validation.ValidatorFactory;
import java.math.BigDecimal;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Set;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

/**
 * Tests for EmployeeRequest JSR-303 / Hibernate Validator annotation constraints.
 * Uses Hibernate Validator 5.x directly (no Spring context needed).
 * Note: @NotBlank and @Email come from org.hibernate.validator.constraints because
 * javax.validation 1.1 does not include them.
 */
public class EmployeeRequestValidationTest {

    private static Validator validator;

    @BeforeClass
    public static void setUpValidator() {
        ValidatorFactory factory = Validation.buildDefaultValidatorFactory();
        validator = factory.getValidator();
    }

    private EmployeeRequest validRequest() throws Exception {
        EmployeeRequest req = new EmployeeRequest();
        req.setName("Alice Smith");
        req.setEmail("alice@example.com");
        req.setDepartment("Engineering");
        req.setSalary(new BigDecimal("75000.00"));
        req.setHireDate(new SimpleDateFormat("yyyy-MM-dd").parse("2020-01-01"));
        return req;
    }

    private boolean hasViolationOnField(Set<ConstraintViolation<EmployeeRequest>> violations, String field) {
        for (ConstraintViolation<EmployeeRequest> v : violations) {
            if (field.equals(v.getPropertyPath().toString())) {
                return true;
            }
        }
        return false;
    }

    @Test
    public void validRequest_passesValidation() throws Exception {
        Set<ConstraintViolation<EmployeeRequest>> violations = validator.validate(validRequest());
        assertEquals("fully valid request should have no violations", 0, violations.size());
    }

    @Test
    public void blankName_failsValidation() throws Exception {
        EmployeeRequest req = validRequest();
        req.setName("   ");
        Set<ConstraintViolation<EmployeeRequest>> violations = validator.validate(req);
        assertTrue("blank name should produce violation on 'name'", hasViolationOnField(violations, "name"));
    }

    @Test
    public void nullName_failsValidation() throws Exception {
        EmployeeRequest req = validRequest();
        req.setName(null);
        Set<ConstraintViolation<EmployeeRequest>> violations = validator.validate(req);
        assertTrue("null name should produce violation on 'name'", hasViolationOnField(violations, "name"));
    }

    @Test
    public void nameTooLong_failsValidation() throws Exception {
        EmployeeRequest req = validRequest();
        // 101 characters
        req.setName(new String(new char[101]).replace('\0', 'A'));
        Set<ConstraintViolation<EmployeeRequest>> violations = validator.validate(req);
        assertTrue("name > 100 chars should produce violation on 'name'", hasViolationOnField(violations, "name"));
    }

    @Test
    public void nameAtMaxLength_passesValidation() throws Exception {
        EmployeeRequest req = validRequest();
        // exactly 100 characters — boundary passes
        req.setName(new String(new char[100]).replace('\0', 'A'));
        Set<ConstraintViolation<EmployeeRequest>> violations = validator.validate(req);
        assertTrue("name exactly 100 chars should not produce violation on 'name'",
                !hasViolationOnField(violations, "name"));
    }

    @Test
    public void blankEmail_failsValidation() throws Exception {
        EmployeeRequest req = validRequest();
        req.setEmail("   ");
        Set<ConstraintViolation<EmployeeRequest>> violations = validator.validate(req);
        assertTrue("blank email should produce violation on 'email'", hasViolationOnField(violations, "email"));
    }

    @Test
    public void nullEmail_failsValidation() throws Exception {
        EmployeeRequest req = validRequest();
        req.setEmail(null);
        Set<ConstraintViolation<EmployeeRequest>> violations = validator.validate(req);
        assertTrue("null email should produce violation on 'email'", hasViolationOnField(violations, "email"));
    }

    @Test
    public void invalidEmailFormat_failsValidation() throws Exception {
        EmployeeRequest req = validRequest();
        req.setEmail("not-an-email");
        Set<ConstraintViolation<EmployeeRequest>> violations = validator.validate(req);
        assertTrue("malformed email should produce violation on 'email'", hasViolationOnField(violations, "email"));
    }

    @Test
    public void blankDepartment_failsValidation() throws Exception {
        EmployeeRequest req = validRequest();
        req.setDepartment("");
        Set<ConstraintViolation<EmployeeRequest>> violations = validator.validate(req);
        assertTrue("blank department should produce violation on 'department'", hasViolationOnField(violations, "department"));
    }

    @Test
    public void departmentTooLong_failsValidation() throws Exception {
        EmployeeRequest req = validRequest();
        // 51 characters
        req.setDepartment(new String(new char[51]).replace('\0', 'D'));
        Set<ConstraintViolation<EmployeeRequest>> violations = validator.validate(req);
        assertTrue("department > 50 chars should produce violation on 'department'",
                hasViolationOnField(violations, "department"));
    }

    @Test
    public void nullSalary_failsValidation() throws Exception {
        EmployeeRequest req = validRequest();
        req.setSalary(null);
        Set<ConstraintViolation<EmployeeRequest>> violations = validator.validate(req);
        assertTrue("null salary should produce violation on 'salary'", hasViolationOnField(violations, "salary"));
    }

    @Test
    public void negativeSalary_failsValidation() throws Exception {
        EmployeeRequest req = validRequest();
        req.setSalary(new BigDecimal("-0.01"));
        Set<ConstraintViolation<EmployeeRequest>> violations = validator.validate(req);
        assertTrue("negative salary should produce violation on 'salary'", hasViolationOnField(violations, "salary"));
    }

    @Test
    public void zeroSalary_passesValidation() throws Exception {
        EmployeeRequest req = validRequest();
        req.setSalary(BigDecimal.ZERO);
        Set<ConstraintViolation<EmployeeRequest>> violations = validator.validate(req);
        assertTrue("zero salary should not produce violation on 'salary'",
                !hasViolationOnField(violations, "salary"));
    }

    @Test
    public void nullHireDate_failsValidation() throws Exception {
        EmployeeRequest req = validRequest();
        req.setHireDate(null);
        Set<ConstraintViolation<EmployeeRequest>> violations = validator.validate(req);
        assertTrue("null hireDate should produce violation on 'hireDate'", hasViolationOnField(violations, "hireDate"));
    }
}
