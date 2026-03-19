package com.example.employee.service;

import com.example.employee.dto.EmployeeRequest;
import com.example.employee.dto.EmployeeResponse;
import com.example.employee.dto.PageResponse;
import com.example.employee.entity.Employee;
import com.example.employee.exception.DuplicateEmailException;
import com.example.employee.exception.EmployeeNotFoundException;
import com.example.employee.mapper.EmployeeMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class EmployeeServiceTest {

    @Mock
    private EmployeeMapper mapper;

    @InjectMocks
    private EmployeeService service;

    private Employee alice;
    private EmployeeRequest aliceRequest;

    @BeforeEach
    void setUp() {
        alice = new Employee();
        alice.setId(1L);
        alice.setName("Alice");
        alice.setEmail("alice@example.com");
        alice.setDepartment("Engineering");
        alice.setSalary(new BigDecimal("80000.00"));
        alice.setHireDate(LocalDate.of(2022, 1, 15));
        alice.setCreatedAt(LocalDateTime.of(2022, 1, 15, 9, 0));
        alice.setUpdatedAt(LocalDateTime.of(2022, 1, 15, 9, 0));

        aliceRequest = new EmployeeRequest(
                "Alice", "alice@example.com", "Engineering",
                new BigDecimal("80000.00"), LocalDate.of(2022, 1, 15));
    }

    // ── findAll ──────────────────────────────────────────────────────────────

    @Test
    void findAll_returnsPaginatedResponse() {
        when(mapper.count()).thenReturn(15L);
        when(mapper.findAll(0, 10)).thenReturn(List.of(alice));

        PageResponse<EmployeeResponse> result = service.findAll(0, 10);

        assertThat(result.currentPage()).isEqualTo(0);
        assertThat(result.totalElements()).isEqualTo(15L);
        assertThat(result.totalPages()).isEqualTo(2);
        assertThat(result.content()).hasSize(1);
        assertThat(result.content().get(0).name()).isEqualTo("Alice");
    }

    @Test
    void findAll_calculatesOffsetCorrectly() {
        when(mapper.count()).thenReturn(25L);
        when(mapper.findAll(10, 10)).thenReturn(List.of());

        service.findAll(1, 10);

        verify(mapper).findAll(10, 10);
    }

    // ── findById ─────────────────────────────────────────────────────────────

    @Test
    void findById_returnsEmployee() {
        when(mapper.findById(1L)).thenReturn(Optional.of(alice));

        EmployeeResponse result = service.findById(1L);

        assertThat(result.id()).isEqualTo(1L);
        assertThat(result.email()).isEqualTo("alice@example.com");
    }

    @Test
    void findById_throwsWhenNotFound() {
        when(mapper.findById(99L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.findById(99L))
                .isInstanceOf(EmployeeNotFoundException.class)
                .hasMessageContaining("99");
    }

    // ── create ───────────────────────────────────────────────────────────────

    @Test
    void create_setsTimestampsAndCallsInsert() {
        when(mapper.findByEmail("alice@example.com")).thenReturn(Optional.empty());
        doAnswer(inv -> {
            Employee e = inv.getArgument(0);
            e.setId(42L);
            return null;
        }).when(mapper).insert(any(Employee.class));

        EmployeeResponse result = service.create(aliceRequest);

        ArgumentCaptor<Employee> captor = ArgumentCaptor.forClass(Employee.class);
        verify(mapper).insert(captor.capture());
        Employee inserted = captor.getValue();

        assertThat(inserted.getCreatedAt()).isNotNull();
        assertThat(inserted.getUpdatedAt()).isNotNull();
        assertThat(inserted.getCreatedAt()).isEqualToIgnoringNanos(inserted.getUpdatedAt());
        assertThat(result.id()).isEqualTo(42L);
    }

    @Test
    void create_throwsDuplicateEmailWhenEmailExists() {
        when(mapper.findByEmail("alice@example.com")).thenReturn(Optional.of(alice));

        assertThatThrownBy(() -> service.create(aliceRequest))
                .isInstanceOf(DuplicateEmailException.class)
                .hasMessageContaining("alice@example.com");

        verify(mapper, never()).insert(any());
    }

    // ── update ───────────────────────────────────────────────────────────────

    @Test
    void update_performsFullReplacement() {
        when(mapper.findById(1L)).thenReturn(Optional.of(alice));
        when(mapper.findByEmail("alice@example.com")).thenReturn(Optional.of(alice));
        when(mapper.update(any())).thenReturn(1);

        EmployeeRequest updateReq = new EmployeeRequest(
                "Alice Updated", "alice@example.com", "HR",
                new BigDecimal("90000.00"), LocalDate.of(2023, 6, 1));

        EmployeeResponse result = service.update(1L, updateReq);

        assertThat(result.name()).isEqualTo("Alice Updated");
        assertThat(result.department()).isEqualTo("HR");
        assertThat(result.salary()).isEqualByComparingTo("90000.00");
    }

    @Test
    void update_setsUpdatedAt() {
        when(mapper.findById(1L)).thenReturn(Optional.of(alice));
        when(mapper.findByEmail(anyString())).thenReturn(Optional.empty());
        when(mapper.update(any())).thenReturn(1);

        LocalDateTime before = LocalDateTime.now();
        service.update(1L, aliceRequest);

        ArgumentCaptor<Employee> captor = ArgumentCaptor.forClass(Employee.class);
        verify(mapper).update(captor.capture());
        assertThat(captor.getValue().getUpdatedAt()).isAfterOrEqualTo(before);
    }

    @Test
    void update_throwsWhenEmployeeNotFound() {
        when(mapper.findById(99L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.update(99L, aliceRequest))
                .isInstanceOf(EmployeeNotFoundException.class)
                .hasMessageContaining("99");
    }

    @Test
    void update_throwsDuplicateEmailWhenAnotherEmployeeHasSameEmail() {
        Employee bob = new Employee();
        bob.setId(2L);
        bob.setEmail("alice@example.com");

        when(mapper.findById(1L)).thenReturn(Optional.of(alice));
        when(mapper.findByEmail("alice@example.com")).thenReturn(Optional.of(bob));

        assertThatThrownBy(() -> service.update(1L, aliceRequest))
                .isInstanceOf(DuplicateEmailException.class)
                .hasMessageContaining("alice@example.com");

        verify(mapper, never()).update(any());
    }

    @Test
    void update_allowsSameEmailForSameEmployee() {
        when(mapper.findById(1L)).thenReturn(Optional.of(alice));
        when(mapper.findByEmail("alice@example.com")).thenReturn(Optional.of(alice));
        when(mapper.update(any())).thenReturn(1);

        // Should NOT throw — same employee keeping same email
        EmployeeResponse result = service.update(1L, aliceRequest);
        assertThat(result.email()).isEqualTo("alice@example.com");
    }

    // ── delete ───────────────────────────────────────────────────────────────

    @Test
    void delete_callsMapperWhenFound() {
        when(mapper.findById(1L)).thenReturn(Optional.of(alice));
        when(mapper.deleteById(1L)).thenReturn(1);

        service.delete(1L);

        verify(mapper).deleteById(1L);
    }

    @Test
    void delete_throwsWhenNotFound() {
        when(mapper.findById(99L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.delete(99L))
                .isInstanceOf(EmployeeNotFoundException.class)
                .hasMessageContaining("99");

        verify(mapper, never()).deleteById(anyLong());
    }

    // ── search ───────────────────────────────────────────────────────────────

    @Test
    void search_byNameAndDepartment() {
        when(mapper.countSearch("alice", "Engineering")).thenReturn(1L);
        when(mapper.search("alice", "Engineering", 0, 10)).thenReturn(List.of(alice));

        PageResponse<EmployeeResponse> result = service.search("alice", "Engineering", 0, 10);

        assertThat(result.totalElements()).isEqualTo(1L);
        assertThat(result.content()).hasSize(1);
        assertThat(result.content().get(0).name()).isEqualTo("Alice");
    }

    @Test
    void search_returnsEmptyPageWhenNoMatches() {
        when(mapper.countSearch("nobody", null)).thenReturn(0L);
        when(mapper.search("nobody", null, 0, 10)).thenReturn(List.of());

        PageResponse<EmployeeResponse> result = service.search("nobody", null, 0, 10);

        assertThat(result.totalElements()).isEqualTo(0L);
        assertThat(result.totalPages()).isEqualTo(0);
        assertThat(result.content()).isEmpty();
    }

    @Test
    void search_calculatesTotalPagesCorrectly() {
        when(mapper.countSearch(null, null)).thenReturn(25L);
        when(mapper.search(null, null, 0, 10)).thenReturn(List.of());

        PageResponse<EmployeeResponse> result = service.search(null, null, 0, 10);

        assertThat(result.totalPages()).isEqualTo(3);
    }
}
