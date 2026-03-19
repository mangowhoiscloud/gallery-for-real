package com.example.legacy.mapper;

import com.example.legacy.model.Employee;
import org.apache.ibatis.annotations.Param;

import java.util.List;

public interface EmployeeMapper {

    List<Employee> findAll(@Param("offset") int offset, @Param("limit") int limit);

    Employee findById(@Param("id") Long id);

    void insert(Employee employee);

    void update(Employee employee);

    void delete(@Param("id") Long id);

    int countAll();

    List<Employee> searchByNameOrDepartment(
            @Param("name") String name,
            @Param("department") String department,
            @Param("offset") int offset,
            @Param("limit") int limit);

    int countBySearch(@Param("name") String name, @Param("department") String department);

    Employee findByEmail(@Param("email") String email);
}
