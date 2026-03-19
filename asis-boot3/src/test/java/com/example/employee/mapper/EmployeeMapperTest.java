package com.example.employee.mapper;

import com.example.employee.entity.Employee;
import org.apache.ibatis.builder.xml.XMLMapperBuilder;
import org.apache.ibatis.mapping.Environment;
import org.apache.ibatis.session.Configuration;
import org.apache.ibatis.session.SqlSession;
import org.apache.ibatis.session.SqlSessionFactory;
import org.apache.ibatis.session.SqlSessionFactoryBuilder;
import org.apache.ibatis.transaction.jdbc.JdbcTransactionFactory;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabase;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseBuilder;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseType;

import java.io.InputStream;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;

class EmployeeMapperTest {

    private EmbeddedDatabase db;
    private SqlSession session;
    private EmployeeMapper mapper;

    @BeforeEach
    void setUp() throws Exception {
        db = new EmbeddedDatabaseBuilder()
                .setType(EmbeddedDatabaseType.H2)
                .generateUniqueName(true)
                .addScript("classpath:schema.sql")
                .addScript("classpath:data.sql")
                .build();

        Environment env = new Environment("test", new JdbcTransactionFactory(), db);
        Configuration config = new Configuration(env);
        config.setMapUnderscoreToCamelCase(true);

        try (InputStream is = Thread.currentThread().getContextClassLoader()
                .getResourceAsStream("mapper/EmployeeMapper.xml")) {
            new XMLMapperBuilder(is, config, "mapper/EmployeeMapper.xml",
                    config.getSqlFragments()).parse();
        }

        SqlSessionFactory factory = new SqlSessionFactoryBuilder().build(config);
        session = factory.openSession(true); // auto-commit
        mapper = session.getMapper(EmployeeMapper.class);
    }

    @AfterEach
    void tearDown() {
        if (session != null) session.close();
        if (db != null) db.shutdown();
    }

    @Test
    void count_returnsFive_withSeedData() {
        assertThat(mapper.count()).isEqualTo(5);
    }

    @Test
    void findAll_firstPage_returnsPagedResults() {
        List<Employee> page = mapper.findAll(0, 3);
        assertThat(page).hasSize(3);
        assertThat(page.get(0).getName()).isNotNull();
        assertThat(page.get(0).getHireDate()).isNotNull();
    }

    @Test
    void findAll_secondPage_returnsRemainingResults() {
        List<Employee> page = mapper.findAll(3, 3);
        assertThat(page).hasSize(2);
    }

    @Test
    void findById_returnsEmployee() {
        List<Employee> all = mapper.findAll(0, 10);
        Long id = all.get(0).getId();
        Optional<Employee> found = mapper.findById(id);
        assertThat(found).isPresent();
        assertThat(found.get().getId()).isEqualTo(id);
        assertThat(found.get().getHireDate()).isNotNull();
        assertThat(found.get().getCreatedAt()).isNotNull();
    }

    @Test
    void findById_notFound_returnsEmpty() {
        Optional<Employee> found = mapper.findById(999999L);
        assertThat(found).isEmpty();
    }

    @Test
    void insert_generatesId_andPersists() {
        long beforeCount = mapper.count();
        Employee emp = buildEmployee("Test User", "test@example.com");
        mapper.insert(emp);
        assertThat(emp.getId()).isNotNull().isPositive();
        assertThat(mapper.count()).isEqualTo(beforeCount + 1);
    }

    @Test
    void findByEmail_returnsEmployee() {
        Employee emp = buildEmployee("Email Test", "emailtest@example.com");
        mapper.insert(emp);
        Optional<Employee> found = mapper.findByEmail("emailtest@example.com");
        assertThat(found).isPresent();
        assertThat(found.get().getName()).isEqualTo("Email Test");
    }

    @Test
    void findByEmail_notFound_returnsEmpty() {
        Optional<Employee> found = mapper.findByEmail("nosuch@example.com");
        assertThat(found).isEmpty();
    }

    @Test
    void update_modifiesEmployee() {
        Employee emp = buildEmployee("Before Update", "before@example.com");
        mapper.insert(emp);
        emp.setName("After Update");
        emp.setDepartment("HR");
        emp.setUpdatedAt(LocalDateTime.now());
        int rows = mapper.update(emp);
        assertThat(rows).isEqualTo(1);
        Optional<Employee> found = mapper.findById(emp.getId());
        assertThat(found).isPresent();
        assertThat(found.get().getName()).isEqualTo("After Update");
        assertThat(found.get().getDepartment()).isEqualTo("HR");
    }

    @Test
    void deleteById_removesEmployee() {
        Employee emp = buildEmployee("Delete Me", "deleteme@example.com");
        mapper.insert(emp);
        long beforeCount = mapper.count();
        int rows = mapper.deleteById(emp.getId());
        assertThat(rows).isEqualTo(1);
        assertThat(mapper.count()).isEqualTo(beforeCount - 1);
        assertThat(mapper.findById(emp.getId())).isEmpty();
    }

    @Test
    void search_byName_caseInsensitive_returnsMatches() {
        List<Employee> results = mapper.search("alice", null, 0, 10);
        assertThat(results).isNotEmpty();
        results.forEach(e -> assertThat(e.getName().toLowerCase()).contains("alice"));
    }

    @Test
    void search_byDepartment_returnsMatches() {
        List<Employee> results = mapper.search(null, "Engineering", 0, 10);
        assertThat(results).isNotEmpty();
        results.forEach(e -> assertThat(e.getDepartment()).isEqualToIgnoringCase("Engineering"));
    }

    @Test
    void search_byNameAndDepartment_andLogic() {
        // Alice Johnson is in Engineering — both filters must match
        List<Employee> results = mapper.search("Alice", "Engineering", 0, 10);
        assertThat(results).hasSize(1);
        assertThat(results.get(0).getName()).contains("Alice");

        // Bob Smith is in Marketing, not Engineering — should return nothing
        List<Employee> noMatch = mapper.search("Bob", "Engineering", 0, 10);
        assertThat(noMatch).isEmpty();
    }

    @Test
    void search_noParams_returnsAll() {
        assertThat(mapper.countSearch(null, null)).isEqualTo(5);
        assertThat(mapper.search(null, null, 0, 10)).hasSize(5);
    }

    @Test
    void search_noMatch_returnsEmpty() {
        List<Employee> results = mapper.search("zzznomatch", null, 0, 10);
        assertThat(results).isEmpty();
        assertThat(mapper.countSearch("zzznomatch", null)).isEqualTo(0);
    }

    @Test
    void search_pagination_worksCorrectly() {
        // 5 seed employees; search all, take page of 2
        List<Employee> page1 = mapper.search(null, null, 0, 2);
        List<Employee> page2 = mapper.search(null, null, 2, 2);
        assertThat(page1).hasSize(2);
        assertThat(page2).hasSize(2);
        assertThat(page1.get(0).getId()).isNotEqualTo(page2.get(0).getId());
    }

    private Employee buildEmployee(String name, String email) {
        Employee e = new Employee();
        e.setName(name);
        e.setEmail(email);
        e.setDepartment("Engineering");
        e.setSalary(new BigDecimal("60000.00"));
        e.setHireDate(LocalDate.of(2024, 1, 15));
        e.setCreatedAt(LocalDateTime.now());
        e.setUpdatedAt(LocalDateTime.now());
        return e;
    }
}
