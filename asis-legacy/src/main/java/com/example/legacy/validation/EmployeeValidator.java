package com.example.legacy.validation;

import com.example.legacy.exception.DuplicateEmailException;
import com.example.legacy.mapper.EmployeeMapper;
import com.example.legacy.model.Employee;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

@Component
public class EmployeeValidator {

    private final EmployeeMapper employeeMapper;

    @Autowired
    public EmployeeValidator(EmployeeMapper employeeMapper) {
        this.employeeMapper = employeeMapper;
    }

    /**
     * Validates that the email is not already used by any employee.
     * Throws DuplicateEmailException (409) if the email exists.
     */
    public void validateCreate(String email) {
        Employee existing = employeeMapper.findByEmail(email);
        if (existing != null) {
            throw new DuplicateEmailException(email);
        }
    }

    /**
     * Validates that the email is not used by a different employee.
     * It is valid for an employee to retain their own email on update.
     * Throws DuplicateEmailException (409) if the email belongs to a different employee.
     */
    public void validateUpdate(Long currentId, String email) {
        Employee existing = employeeMapper.findByEmail(email);
        if (existing != null && !existing.getId().equals(currentId)) {
            throw new DuplicateEmailException(email);
        }
    }
}
