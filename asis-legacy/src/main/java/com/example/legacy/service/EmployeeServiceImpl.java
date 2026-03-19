package com.example.legacy.service;

import com.example.legacy.dto.EmployeeRequest;
import com.example.legacy.exception.BadRequestException;
import com.example.legacy.exception.NotFoundException;
import com.example.legacy.mapper.EmployeeMapper;
import com.example.legacy.model.Employee;
import com.example.legacy.model.PageResult;
import com.example.legacy.validation.EmployeeValidator;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@Transactional
public class EmployeeServiceImpl implements EmployeeService {

    private final EmployeeMapper employeeMapper;
    private final EmployeeValidator employeeValidator;

    @Autowired
    public EmployeeServiceImpl(EmployeeMapper employeeMapper, EmployeeValidator employeeValidator) {
        this.employeeMapper = employeeMapper;
        this.employeeValidator = employeeValidator;
    }

    @Override
    @Transactional(readOnly = true)
    public PageResult<Employee> getAllEmployees(int page, int size) {
        int offset = page * size;
        List<Employee> content = employeeMapper.findAll(offset, size);
        long totalElements = employeeMapper.countAll();
        return new PageResult<Employee>(content, totalElements, page, size);
    }

    @Override
    @Transactional(readOnly = true)
    public Employee getEmployeeById(Long id) {
        Employee employee = employeeMapper.findById(id);
        if (employee == null) {
            throw new NotFoundException("Employee not found with id: " + id);
        }
        return employee;
    }

    @Override
    public Employee createEmployee(EmployeeRequest request) {
        employeeValidator.validateCreate(request.getEmail());

        Employee employee = toEmployee(request);
        employeeMapper.insert(employee);

        // Re-fetch to get DB-generated createdAt, updatedAt, and confirmed id
        return employeeMapper.findById(employee.getId());
    }

    @Override
    public Employee updateEmployee(Long id, EmployeeRequest request) {
        Employee existing = employeeMapper.findById(id);
        if (existing == null) {
            throw new NotFoundException("Employee not found with id: " + id);
        }

        employeeValidator.validateUpdate(id, request.getEmail());

        Employee updated = toEmployee(request);
        updated.setId(id);
        employeeMapper.update(updated);

        // Re-fetch to get DB-updated updatedAt
        return employeeMapper.findById(id);
    }

    @Override
    public void deleteEmployee(Long id) {
        Employee existing = employeeMapper.findById(id);
        if (existing == null) {
            throw new NotFoundException("Employee not found with id: " + id);
        }
        employeeMapper.delete(id);
    }

    @Override
    @Transactional(readOnly = true)
    public PageResult<Employee> searchEmployees(String name, String department, int page, int size) {
        if ((name == null || name.trim().isEmpty()) && (department == null || department.trim().isEmpty())) {
            throw new BadRequestException("At least one of name or department must be provided for search");
        }

        // Normalize empty strings to null so mapper <choose> logic works correctly
        String searchName = (name != null && !name.trim().isEmpty()) ? name : null;
        String searchDept = (department != null && !department.trim().isEmpty()) ? department : null;

        int offset = page * size;
        List<Employee> content = employeeMapper.searchByNameOrDepartment(searchName, searchDept, offset, size);
        long totalElements = employeeMapper.countBySearch(searchName, searchDept);
        return new PageResult<Employee>(content, totalElements, page, size);
    }

    private Employee toEmployee(EmployeeRequest request) {
        Employee employee = new Employee();
        employee.setName(request.getName());
        employee.setEmail(request.getEmail());
        employee.setDepartment(request.getDepartment());
        employee.setSalary(request.getSalary());
        employee.setHireDate(request.getHireDate());
        return employee;
    }
}
