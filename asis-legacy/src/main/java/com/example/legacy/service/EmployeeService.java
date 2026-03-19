package com.example.legacy.service;

import com.example.legacy.dto.EmployeeRequest;
import com.example.legacy.model.Employee;
import com.example.legacy.model.PageResult;

public interface EmployeeService {

    PageResult<Employee> getAllEmployees(int page, int size);

    Employee getEmployeeById(Long id);

    Employee createEmployee(EmployeeRequest request);

    Employee updateEmployee(Long id, EmployeeRequest request);

    void deleteEmployee(Long id);

    PageResult<Employee> searchEmployees(String name, String department, int page, int size);
}
