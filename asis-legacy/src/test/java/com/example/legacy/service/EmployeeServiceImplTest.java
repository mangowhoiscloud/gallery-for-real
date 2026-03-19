package com.example.legacy.service;

import com.example.legacy.dto.EmployeeRequest;
import com.example.legacy.exception.BadRequestException;
import com.example.legacy.exception.DuplicateEmailException;
import com.example.legacy.exception.NotFoundException;
import com.example.legacy.mapper.EmployeeMapper;
import com.example.legacy.model.Employee;
import com.example.legacy.model.PageResult;
import com.example.legacy.validation.EmployeeValidator;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.Mock;
import org.mockito.invocation.InvocationOnMock;
import org.mockito.runners.MockitoJUnitRunner;
import org.mockito.stubbing.Answer;

import java.math.BigDecimal;
import java.util.Arrays;
import java.util.Collections;
import java.util.Date;
import java.util.List;

import static org.junit.Assert.*;
import static org.mockito.Matchers.*;
import static org.mockito.Mockito.*;

@RunWith(MockitoJUnitRunner.class)
public class EmployeeServiceImplTest {

    @Mock
    private EmployeeMapper employeeMapper;

    @Mock
    private EmployeeValidator employeeValidator;

    private EmployeeServiceImpl service;

    @Before
    public void setUp() {
        service = new EmployeeServiceImpl(employeeMapper, employeeValidator);
    }

    // ── getAllEmployees ──────────────────────────────────────────────────────

    @Test
    public void getAllEmployees_returnsPageResultWithCorrectTotalPages() {
        List<Employee> employees = Arrays.asList(newEmployee(1L, "Alice"), newEmployee(2L, "Bob"));
        when(employeeMapper.findAll(0, 2)).thenReturn(employees);
        when(employeeMapper.countAll()).thenReturn(5);

        PageResult<Employee> result = service.getAllEmployees(0, 2);

        assertEquals(2, result.getContent().size());
        assertEquals(5L, result.getTotalElements());
        assertEquals(0, result.getCurrentPage());
        assertEquals(3, result.getTotalPages()); // ceil(5/2) = 3
    }

    @Test
    public void getAllEmployees_emptyTable_returnsZeroTotals() {
        when(employeeMapper.findAll(0, 10)).thenReturn(Collections.<Employee>emptyList());
        when(employeeMapper.countAll()).thenReturn(0);

        PageResult<Employee> result = service.getAllEmployees(0, 10);

        assertEquals(0, result.getContent().size());
        assertEquals(0L, result.getTotalElements());
        assertEquals(0, result.getTotalPages());
    }

    @Test
    public void getAllEmployees_page1_computesOffsetCorrectly() {
        when(employeeMapper.findAll(10, 10)).thenReturn(Collections.<Employee>emptyList());
        when(employeeMapper.countAll()).thenReturn(10);

        service.getAllEmployees(1, 10);

        verify(employeeMapper).findAll(10, 10); // offset = page * size = 1 * 10 = 10
    }

    // ── getEmployeeById ──────────────────────────────────────────────────────

    @Test
    public void getEmployeeById_found_returnsEmployee() {
        Employee emp = newEmployee(42L, "Charlie");
        when(employeeMapper.findById(42L)).thenReturn(emp);

        Employee result = service.getEmployeeById(42L);

        assertEquals("Charlie", result.getName());
    }

    @Test(expected = NotFoundException.class)
    public void getEmployeeById_notFound_throwsNotFoundException() {
        when(employeeMapper.findById(99L)).thenReturn(null);

        service.getEmployeeById(99L);
    }

    // ── createEmployee ──────────────────────────────────────────────────────

    @Test
    public void createEmployee_validRequest_callsValidatorAndReturnsEmployee() {
        EmployeeRequest req = newRequest("Dave", "dave@test.com");
        Employee inserted = newEmployee(10L, "Dave");

        // Simulate insert setting the generated id on the Employee arg
        doAnswer(new Answer<Void>() {
            @Override
            public Void answer(InvocationOnMock invocation) {
                Employee e = (Employee) invocation.getArguments()[0];
                e.setId(10L);
                return null;
            }
        }).when(employeeMapper).insert(any(Employee.class));

        when(employeeMapper.findById(10L)).thenReturn(inserted);

        Employee result = service.createEmployee(req);

        verify(employeeValidator).validateCreate("dave@test.com");
        verify(employeeMapper).insert(any(Employee.class));
        verify(employeeMapper).findById(10L);
        assertEquals(10L, (long) result.getId());
        assertEquals("Dave", result.getName());
    }

    @Test(expected = DuplicateEmailException.class)
    public void createEmployee_duplicateEmail_throwsDuplicateEmailException() {
        EmployeeRequest req = newRequest("Eve", "existing@test.com");
        doThrow(new DuplicateEmailException("existing@test.com"))
                .when(employeeValidator).validateCreate("existing@test.com");

        service.createEmployee(req);
    }

    // ── updateEmployee ──────────────────────────────────────────────────────

    @Test
    public void updateEmployee_validRequest_updatesAndReturnsEmployee() {
        Employee existing = newEmployee(5L, "Frank");
        EmployeeRequest req = newRequest("Frank Updated", "frank@test.com");
        Employee updated = newEmployee(5L, "Frank Updated");

        when(employeeMapper.findById(5L)).thenReturn(existing).thenReturn(updated);

        Employee result = service.updateEmployee(5L, req);

        verify(employeeValidator).validateUpdate(5L, "frank@test.com");
        verify(employeeMapper).update(any(Employee.class));
        assertEquals("Frank Updated", result.getName());
    }

    @Test(expected = NotFoundException.class)
    public void updateEmployee_notFound_throwsNotFoundException() {
        when(employeeMapper.findById(99L)).thenReturn(null);

        service.updateEmployee(99L, newRequest("X", "x@test.com"));
    }

    @Test(expected = DuplicateEmailException.class)
    public void updateEmployee_duplicateEmail_throwsDuplicateEmailException() {
        Employee existing = newEmployee(5L, "Grace");
        when(employeeMapper.findById(5L)).thenReturn(existing);
        doThrow(new DuplicateEmailException("other@test.com"))
                .when(employeeValidator).validateUpdate(5L, "other@test.com");

        service.updateEmployee(5L, newRequest("Grace", "other@test.com"));
    }

    // ── deleteEmployee ──────────────────────────────────────────────────────

    @Test
    public void deleteEmployee_found_deletesRecord() {
        when(employeeMapper.findById(3L)).thenReturn(newEmployee(3L, "Hank"));

        service.deleteEmployee(3L);

        verify(employeeMapper).delete(3L);
    }

    @Test(expected = NotFoundException.class)
    public void deleteEmployee_notFound_throwsNotFoundException() {
        when(employeeMapper.findById(99L)).thenReturn(null);

        service.deleteEmployee(99L);
    }

    // ── searchEmployees ──────────────────────────────────────────────────────

    @Test
    public void searchEmployees_byName_returnsMatches() {
        List<Employee> matches = Arrays.asList(newEmployee(1L, "Ivan"));
        when(employeeMapper.searchByNameOrDepartment("Ivan", null, 0, 10)).thenReturn(matches);
        when(employeeMapper.countBySearch("Ivan", null)).thenReturn(1);

        PageResult<Employee> result = service.searchEmployees("Ivan", null, 0, 10);

        assertEquals(1, result.getContent().size());
        assertEquals(1L, result.getTotalElements());
        assertEquals(1, result.getTotalPages());
    }

    @Test
    public void searchEmployees_byDepartment_returnsMatches() {
        List<Employee> matches = Arrays.asList(newEmployee(2L, "Jane"), newEmployee(3L, "Jake"));
        when(employeeMapper.searchByNameOrDepartment(null, "Engineering", 0, 10)).thenReturn(matches);
        when(employeeMapper.countBySearch(null, "Engineering")).thenReturn(2);

        PageResult<Employee> result = service.searchEmployees(null, "Engineering", 0, 10);

        assertEquals(2, result.getContent().size());
    }

    @Test
    public void searchEmployees_byBoth_returnsOrMatches() {
        List<Employee> matches = Arrays.asList(newEmployee(1L, "Karl"), newEmployee(4L, "Lisa"));
        when(employeeMapper.searchByNameOrDepartment("Karl", "HR", 0, 10)).thenReturn(matches);
        when(employeeMapper.countBySearch("Karl", "HR")).thenReturn(2);

        PageResult<Employee> result = service.searchEmployees("Karl", "HR", 0, 10);

        assertEquals(2, result.getContent().size());
        verify(employeeMapper).searchByNameOrDepartment("Karl", "HR", 0, 10);
    }

    @Test(expected = BadRequestException.class)
    public void searchEmployees_noParams_throwsBadRequestException() {
        service.searchEmployees(null, null, 0, 10);
    }

    @Test(expected = BadRequestException.class)
    public void searchEmployees_emptyStringParams_throwsBadRequestException() {
        service.searchEmployees("  ", "  ", 0, 10);
    }

    @Test
    public void searchEmployees_emptyResult_returnsZeroTotals() {
        when(employeeMapper.searchByNameOrDepartment("NoMatch", null, 0, 10))
                .thenReturn(Collections.<Employee>emptyList());
        when(employeeMapper.countBySearch("NoMatch", null)).thenReturn(0);

        PageResult<Employee> result = service.searchEmployees("NoMatch", null, 0, 10);

        assertEquals(0, result.getContent().size());
        assertEquals(0L, result.getTotalElements());
        assertEquals(0, result.getTotalPages());
    }

    // ── helpers ──────────────────────────────────────────────────────────────

    private Employee newEmployee(Long id, String name) {
        Employee e = new Employee();
        e.setId(id);
        e.setName(name);
        e.setEmail(name.toLowerCase() + "@test.com");
        e.setDepartment("Engineering");
        e.setSalary(new BigDecimal("50000"));
        e.setHireDate(new Date());
        return e;
    }

    private EmployeeRequest newRequest(String name, String email) {
        EmployeeRequest req = new EmployeeRequest();
        req.setName(name);
        req.setEmail(email);
        req.setDepartment("Engineering");
        req.setSalary(new BigDecimal("60000"));
        req.setHireDate(new Date());
        return req;
    }
}
