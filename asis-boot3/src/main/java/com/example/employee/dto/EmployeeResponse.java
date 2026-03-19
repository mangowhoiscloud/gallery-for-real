package com.example.employee.dto;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

public record EmployeeResponse(
        Long id,
        String name,
        String email,
        String department,
        BigDecimal salary,
        LocalDate hireDate,
        LocalDateTime createdAt,
        LocalDateTime updatedAt
) {
}
