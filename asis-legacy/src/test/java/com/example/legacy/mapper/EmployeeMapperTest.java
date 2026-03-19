package com.example.legacy.mapper;

import com.example.legacy.model.Employee;
import com.example.legacy.support.BaseIntegrationTest;
import org.junit.Test;
import org.springframework.beans.factory.annotation.Autowired;

import java.math.BigDecimal;
import java.sql.Date;
import java.util.List;

import static org.junit.Assert.*;

public class EmployeeMapperTest extends BaseIntegrationTest {

    @Autowired
    private EmployeeMapper employeeMapper;

    private Employee buildEmployee(String name, String email, String department) {
        Employee emp = new Employee();
        emp.setName(name);
        emp.setEmail(email);
        emp.setDepartment(department);
        emp.setSalary(new BigDecimal("50000.00"));
        emp.setHireDate(Date.valueOf("2023-01-15"));
        return emp;
    }

    // ── insert ────────────────────────────────────────────────────────────────

    @Test
    public void insert_generatesIdAndPersistsRecord() {
        Employee emp = buildEmployee("Alice", "alice@example.com", "Engineering");
        assertNull(emp.getId());

        employeeMapper.insert(emp);

        assertNotNull(emp.getId());
        assertTrue(emp.getId() > 0);
    }

    // ── findById ──────────────────────────────────────────────────────────────

    @Test
    public void findById_returnsEmployee_withAllFields() {
        Employee emp = buildEmployee("Bob", "bob@example.com", "Sales");
        employeeMapper.insert(emp);

        Employee found = employeeMapper.findById(emp.getId());

        assertNotNull(found);
        assertEquals(emp.getId(), found.getId());
        assertEquals("Bob", found.getName());
        assertEquals("bob@example.com", found.getEmail());
        assertEquals("Sales", found.getDepartment());
        assertEquals(new BigDecimal("50000.00"), found.getSalary());
        assertNotNull(found.getHireDate());
        assertNotNull(found.getCreatedAt());
        assertNotNull(found.getUpdatedAt());
    }

    @Test
    public void findById_returnsNull_whenNotExists() {
        assertNull(employeeMapper.findById(9999L));
    }

    // ── findAll ───────────────────────────────────────────────────────────────

    @Test
    public void findAll_respectsOffsetAndLimit() {
        employeeMapper.insert(buildEmployee("Alice", "alice@example.com", "Engineering"));
        employeeMapper.insert(buildEmployee("Bob", "bob@example.com", "Sales"));
        employeeMapper.insert(buildEmployee("Carol", "carol@example.com", "HR"));

        List<Employee> page1 = employeeMapper.findAll(0, 2);
        assertEquals(2, page1.size());

        List<Employee> page2 = employeeMapper.findAll(2, 2);
        assertEquals(1, page2.size());
    }

    @Test
    public void findAll_returnsEmpty_whenOffsetBeyondData() {
        employeeMapper.insert(buildEmployee("Alice", "alice@example.com", "Engineering"));

        List<Employee> result = employeeMapper.findAll(100, 10);
        assertTrue(result.isEmpty());
    }

    // ── update ────────────────────────────────────────────────────────────────

    @Test
    public void update_modifiesAllFields() {
        Employee emp = buildEmployee("Alice", "alice@example.com", "Engineering");
        employeeMapper.insert(emp);

        emp.setName("Alice Updated");
        emp.setEmail("alice.updated@example.com");
        emp.setDepartment("Management");
        emp.setSalary(new BigDecimal("75000.00"));
        emp.setHireDate(Date.valueOf("2024-06-01"));
        employeeMapper.update(emp);

        Employee updated = employeeMapper.findById(emp.getId());
        assertEquals("Alice Updated", updated.getName());
        assertEquals("alice.updated@example.com", updated.getEmail());
        assertEquals("Management", updated.getDepartment());
        assertEquals(new BigDecimal("75000.00"), updated.getSalary());
    }

    // ── delete ────────────────────────────────────────────────────────────────

    @Test
    public void delete_removesRecord() {
        Employee emp = buildEmployee("Alice", "alice@example.com", "Engineering");
        employeeMapper.insert(emp);
        assertNotNull(employeeMapper.findById(emp.getId()));

        employeeMapper.delete(emp.getId());

        assertNull(employeeMapper.findById(emp.getId()));
    }

    @Test
    public void delete_nonExistentId_doesNothing() {
        // No exception expected
        employeeMapper.delete(9999L);
    }

    // ── countAll ──────────────────────────────────────────────────────────────

    @Test
    public void countAll_returnsZero_whenEmpty() {
        assertEquals(0, employeeMapper.countAll());
    }

    @Test
    public void countAll_returnsCorrectCount() {
        employeeMapper.insert(buildEmployee("Alice", "alice@example.com", "Engineering"));
        employeeMapper.insert(buildEmployee("Bob", "bob@example.com", "Sales"));
        assertEquals(2, employeeMapper.countAll());
    }

    // ── searchByNameOrDepartment ──────────────────────────────────────────────

    @Test
    public void search_byName_caseInsensitive() {
        employeeMapper.insert(buildEmployee("Alice Smith", "alice@example.com", "Engineering"));
        employeeMapper.insert(buildEmployee("Bob Jones", "bob@example.com", "Sales"));

        List<Employee> results = employeeMapper.searchByNameOrDepartment("ALICE", null, 0, 10);

        assertEquals(1, results.size());
        assertEquals("Alice Smith", results.get(0).getName());
    }

    @Test
    public void search_byDepartment_caseInsensitive() {
        employeeMapper.insert(buildEmployee("Alice", "alice@example.com", "Engineering"));
        employeeMapper.insert(buildEmployee("Bob", "bob@example.com", "Sales"));

        List<Employee> results = employeeMapper.searchByNameOrDepartment(null, "ENGINEERING", 0, 10);

        assertEquals(1, results.size());
        assertEquals("Alice", results.get(0).getName());
    }

    @Test
    public void search_byNameAndDepartment_returnsOrResults() {
        employeeMapper.insert(buildEmployee("Alice", "alice@example.com", "Engineering"));
        employeeMapper.insert(buildEmployee("Bob", "bob@example.com", "Sales"));
        employeeMapper.insert(buildEmployee("Carol", "carol@example.com", "HR"));

        // name matches "alice" → Alice; department matches "sales" → Bob; Carol excluded
        List<Employee> results = employeeMapper.searchByNameOrDepartment("alice", "sales", 0, 10);

        assertEquals(2, results.size());
    }

    @Test
    public void search_returnsEmpty_whenNoMatch() {
        employeeMapper.insert(buildEmployee("Alice", "alice@example.com", "Engineering"));

        List<Employee> results = employeeMapper.searchByNameOrDepartment("nonexistent", null, 0, 10);

        assertTrue(results.isEmpty());
    }

    @Test
    public void search_respectsPagination() {
        employeeMapper.insert(buildEmployee("Alice", "alice@example.com", "Engineering"));
        employeeMapper.insert(buildEmployee("Charlie", "charlie@example.com", "Engineering"));
        employeeMapper.insert(buildEmployee("Dave", "dave@example.com", "Engineering"));

        List<Employee> page = employeeMapper.searchByNameOrDepartment(null, "Engineering", 0, 2);
        assertEquals(2, page.size());

        List<Employee> page2 = employeeMapper.searchByNameOrDepartment(null, "Engineering", 2, 2);
        assertEquals(1, page2.size());
    }

    // ── countBySearch ─────────────────────────────────────────────────────────

    @Test
    public void countBySearch_nameOnly_returnsMatchCount() {
        employeeMapper.insert(buildEmployee("Alice", "alice@example.com", "Engineering"));
        employeeMapper.insert(buildEmployee("Alice2", "alice2@example.com", "Sales"));
        employeeMapper.insert(buildEmployee("Bob", "bob@example.com", "HR"));

        assertEquals(2, employeeMapper.countBySearch("alice", null));
    }

    @Test
    public void countBySearch_departmentOnly_returnsMatchCount() {
        employeeMapper.insert(buildEmployee("Alice", "alice@example.com", "Engineering"));
        employeeMapper.insert(buildEmployee("Bob", "bob@example.com", "Sales"));

        assertEquals(1, employeeMapper.countBySearch(null, "Sales"));
    }

    @Test
    public void countBySearch_nameAndDepartment_returnsOrCount() {
        employeeMapper.insert(buildEmployee("Alice", "alice@example.com", "Engineering"));
        employeeMapper.insert(buildEmployee("Bob", "bob@example.com", "Sales"));

        assertEquals(2, employeeMapper.countBySearch("alice", "sales"));
    }

    // ── findByEmail ───────────────────────────────────────────────────────────

    @Test
    public void findByEmail_returnsEmployee_whenExists() {
        Employee emp = buildEmployee("Alice", "alice@example.com", "Engineering");
        employeeMapper.insert(emp);

        Employee found = employeeMapper.findByEmail("alice@example.com");

        assertNotNull(found);
        assertEquals(emp.getId(), found.getId());
        assertEquals("alice@example.com", found.getEmail());
    }

    @Test
    public void findByEmail_returnsNull_whenNotExists() {
        assertNull(employeeMapper.findByEmail("noone@example.com"));
    }
}
