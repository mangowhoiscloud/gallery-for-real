package com.example.legacy.validation;

import com.example.legacy.exception.DuplicateEmailException;
import com.example.legacy.mapper.EmployeeMapper;
import com.example.legacy.model.Employee;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.Mock;
import org.mockito.runners.MockitoJUnitRunner;

import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@RunWith(MockitoJUnitRunner.class)
public class EmployeeValidatorTest {

    @Mock
    private EmployeeMapper employeeMapper;

    private EmployeeValidator validator;

    @Before
    public void setUp() {
        validator = new EmployeeValidator(employeeMapper);
    }

    // --- validateCreate ---

    @Test
    public void validateCreate_uniqueEmail_noException() {
        when(employeeMapper.findByEmail("new@example.com")).thenReturn(null);

        validator.validateCreate("new@example.com");

        verify(employeeMapper).findByEmail("new@example.com");
    }

    @Test(expected = DuplicateEmailException.class)
    public void validateCreate_duplicateEmail_throwsDuplicateEmailException() {
        Employee existing = new Employee();
        existing.setId(1L);
        when(employeeMapper.findByEmail("taken@example.com")).thenReturn(existing);

        validator.validateCreate("taken@example.com");
    }

    // --- validateUpdate ---

    @Test
    public void validateUpdate_ownEmail_noException() {
        Employee existing = new Employee();
        existing.setId(42L);
        when(employeeMapper.findByEmail("own@example.com")).thenReturn(existing);

        // Same id → employee keeping their own email, must not throw
        validator.validateUpdate(42L, "own@example.com");

        verify(employeeMapper).findByEmail("own@example.com");
    }

    @Test(expected = DuplicateEmailException.class)
    public void validateUpdate_emailOfDifferentEmployee_throwsDuplicateEmailException() {
        Employee existing = new Employee();
        existing.setId(99L);
        when(employeeMapper.findByEmail("other@example.com")).thenReturn(existing);

        // Different id → email belongs to someone else
        validator.validateUpdate(1L, "other@example.com");
    }

    @Test
    public void validateUpdate_uniqueNewEmail_noException() {
        when(employeeMapper.findByEmail("unique@example.com")).thenReturn(null);

        validator.validateUpdate(1L, "unique@example.com");

        verify(employeeMapper).findByEmail("unique@example.com");
    }
}
