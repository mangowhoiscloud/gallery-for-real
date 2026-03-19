package com.example.employee.mapper;

import com.example.employee.entity.Employee;
import org.apache.ibatis.annotations.*;

import java.util.List;
import java.util.Optional;

@Mapper
public interface EmployeeMapper {

    @Insert("INSERT INTO employees (name, email, department, salary, hire_date, created_at, updated_at) " +
            "VALUES (#{name}, #{email}, #{department}, #{salary}, #{hireDate}, #{createdAt}, #{updatedAt})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    void insert(Employee employee);

    @Select("SELECT * FROM employees WHERE id = #{id}")
    Optional<Employee> findById(Long id);

    @Select("SELECT * FROM employees ORDER BY id LIMIT #{size} OFFSET #{offset}")
    List<Employee> findAll(@Param("offset") int offset, @Param("size") int size);

    @Select("SELECT COUNT(*) FROM employees")
    long count();

    @Update("UPDATE employees SET name = #{name}, email = #{email}, department = #{department}, " +
            "salary = #{salary}, hire_date = #{hireDate}, updated_at = #{updatedAt} WHERE id = #{id}")
    int update(Employee employee);

    @Delete("DELETE FROM employees WHERE id = #{id}")
    int deleteById(Long id);

    @Select("SELECT * FROM employees WHERE email = #{email}")
    Optional<Employee> findByEmail(String email);

    List<Employee> search(@Param("name") String name, @Param("department") String department,
                          @Param("offset") int offset, @Param("size") int size);

    long countSearch(@Param("name") String name, @Param("department") String department);
}
