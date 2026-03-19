package com.example.employee.service;

import com.example.employee.dto.EmployeeRequest;
import com.example.employee.dto.EmployeeResponse;
import com.example.employee.dto.PageResponse;
import com.example.employee.entity.Employee;
import com.example.employee.exception.DuplicateEmailException;
import com.example.employee.exception.EmployeeNotFoundException;
import com.example.employee.mapper.EmployeeMapper;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class EmployeeService {

    private final EmployeeMapper mapper;

    public EmployeeService(EmployeeMapper mapper) {
        this.mapper = mapper;
    }

    public PageResponse<EmployeeResponse> findAll(int page, int size) {
        int offset = page * size;
        long totalElements = mapper.count();
        List<EmployeeResponse> content = mapper.findAll(offset, size).stream()
                .map(this::toResponse)
                .toList();
        int totalPages = totalPages(totalElements, size);
        return new PageResponse<>(content, page, totalPages, totalElements);
    }

    public EmployeeResponse findById(Long id) {
        return mapper.findById(id)
                .map(this::toResponse)
                .orElseThrow(() -> new EmployeeNotFoundException(id));
    }

    public EmployeeResponse create(EmployeeRequest request) {
        mapper.findByEmail(request.email()).ifPresent(e -> {
            throw new DuplicateEmailException(request.email());
        });
        LocalDateTime now = LocalDateTime.now();
        Employee employee = new Employee();
        employee.setName(request.name());
        employee.setEmail(request.email());
        employee.setDepartment(request.department());
        employee.setSalary(request.salary());
        employee.setHireDate(request.hireDate());
        employee.setCreatedAt(now);
        employee.setUpdatedAt(now);
        mapper.insert(employee);
        return toResponse(employee);
    }

    public EmployeeResponse update(Long id, EmployeeRequest request) {
        Employee existing = mapper.findById(id)
                .orElseThrow(() -> new EmployeeNotFoundException(id));
        mapper.findByEmail(request.email()).ifPresent(found -> {
            if (!found.getId().equals(id)) {
                throw new DuplicateEmailException(request.email());
            }
        });
        existing.setName(request.name());
        existing.setEmail(request.email());
        existing.setDepartment(request.department());
        existing.setSalary(request.salary());
        existing.setHireDate(request.hireDate());
        existing.setUpdatedAt(LocalDateTime.now());
        mapper.update(existing);
        return toResponse(existing);
    }

    public void delete(Long id) {
        mapper.findById(id).orElseThrow(() -> new EmployeeNotFoundException(id));
        mapper.deleteById(id);
    }

    public PageResponse<EmployeeResponse> search(String name, String department, int page, int size) {
        int offset = page * size;
        long totalElements = mapper.countSearch(name, department);
        List<EmployeeResponse> content = mapper.search(name, department, offset, size).stream()
                .map(this::toResponse)
                .toList();
        int totalPages = totalPages(totalElements, size);
        return new PageResponse<>(content, page, totalPages, totalElements);
    }

    private EmployeeResponse toResponse(Employee e) {
        return new EmployeeResponse(
                e.getId(), e.getName(), e.getEmail(), e.getDepartment(),
                e.getSalary(), e.getHireDate(), e.getCreatedAt(), e.getUpdatedAt()
        );
    }

    private int totalPages(long totalElements, int size) {
        if (size <= 0) return 0;
        return (int) Math.ceil((double) totalElements / size);
    }
}
