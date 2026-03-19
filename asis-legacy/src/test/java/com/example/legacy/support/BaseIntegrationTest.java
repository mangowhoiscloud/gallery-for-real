package com.example.legacy.support;

import com.example.legacy.config.TestAppConfig;
import org.junit.runner.RunWith;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;
import org.springframework.transaction.annotation.Transactional;

/**
 * Base class for Spring integration tests that require a real database.
 *
 * Loads TestAppConfig which wires up an H2 in-memory DataSource (PostgreSQL mode),
 * runs schema.sql on startup, and configures MyBatis mapper beans.
 *
 * @Transactional causes each test method to run in a transaction that is
 * automatically rolled back on completion, ensuring test isolation without
 * requiring manual cleanup between tests.
 *
 * Usage:
 *   public class EmployeeMapperTest extends BaseIntegrationTest {
 *       @Autowired private EmployeeMapper employeeMapper;
 *       // tests...
 *   }
 */
@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration(classes = TestAppConfig.class)
@Transactional
public abstract class BaseIntegrationTest {
}
