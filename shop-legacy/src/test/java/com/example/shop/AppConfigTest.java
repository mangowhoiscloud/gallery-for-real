package com.example.shop;

import com.example.shop.config.TestConfig;
import org.apache.ibatis.session.SqlSessionFactory;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mybatis.spring.mapper.MapperScannerConfigurer;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationContext;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;
import org.springframework.transaction.PlatformTransactionManager;

import javax.sql.DataSource;
import java.sql.Connection;

import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

/**
 * Smoke test verifying the Spring application context loads correctly
 * and all core infrastructure beans are present and functional.
 */
@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration(classes = TestConfig.class)
public class AppConfigTest {

    @Autowired
    private ApplicationContext applicationContext;

    @Autowired
    private DataSource dataSource;

    @Autowired
    private SqlSessionFactory sqlSessionFactory;

    @Autowired
    private PlatformTransactionManager transactionManager;

    @Test
    public void contextLoads() {
        assertNotNull("ApplicationContext must not be null", applicationContext);
    }

    @Test
    public void dataSourceBeanExists() {
        assertNotNull("DataSource bean must exist", dataSource);
    }

    @Test
    public void dataSourceCanConnect() throws Exception {
        try (Connection conn = dataSource.getConnection()) {
            assertNotNull("Connection must be established", conn);
            assertTrue("Connection must be valid", conn.isValid(2));
        }
    }

    @Test
    public void sqlSessionFactoryBeanExists() {
        assertNotNull("SqlSessionFactory bean must exist", sqlSessionFactory);
    }

    @Test
    public void transactionManagerBeanExists() {
        assertNotNull("PlatformTransactionManager bean must exist", transactionManager);
    }

    @Test
    public void mapperScannerConfigurerRegistered() {
        // MapperScannerConfigurer is a BeanDefinitionRegistryPostProcessor;
        // verify it was declared and processed by checking it's in the context
        assertTrue("MapperScannerConfigurer must be registered",
                applicationContext.containsBean("mapperScannerConfigurer"));
    }

    @Test
    public void schemaTablesCreated() throws Exception {
        // Verify the 6 schema tables exist in H2
        // With DATABASE_TO_LOWER=TRUE, table names are stored in lowercase — no toUpperCase()
        String[] tables = {"members", "products", "carts", "cart_items", "orders", "order_items"};
        try (Connection conn = dataSource.getConnection()) {
            for (String table : tables) {
                try (java.sql.ResultSet rs = conn.getMetaData()
                        .getTables(null, null, table, new String[]{"TABLE"})) {
                    assertTrue("Table '" + table + "' must exist in schema", rs.next());
                }
            }
        }
    }
}
