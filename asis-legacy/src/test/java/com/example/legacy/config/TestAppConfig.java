package com.example.legacy.config;

import org.apache.commons.dbcp2.BasicDataSource;
import org.mybatis.spring.SqlSessionFactoryBean;
import org.mybatis.spring.mapper.MapperScannerConfigurer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.ClassPathResource;
import org.springframework.core.io.support.PathMatchingResourcePatternResolver;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.jdbc.datasource.init.DataSourceInitializer;
import org.springframework.jdbc.datasource.init.ResourceDatabasePopulator;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.annotation.EnableTransactionManagement;

import javax.sql.DataSource;

/**
 * Spring configuration for integration tests.
 *
 * Provides an H2 in-memory DataSource in PostgreSQL-compatibility mode,
 * bootstraps the schema from test/resources/schema.sql via DataSourceInitializer,
 * and wires up the same SqlSessionFactory, TransactionManager, and
 * MapperScannerConfigurer used in production — keeping mapper XML paths identical.
 *
 * Transactions are managed by DataSourceTransactionManager so @Transactional
 * tests can roll back after each test method, guaranteeing test isolation.
 */
@Configuration
@EnableTransactionManagement
public class TestAppConfig {

    @Bean
    public DataSource dataSource() {
        BasicDataSource ds = new BasicDataSource();
        ds.setDriverClassName("org.h2.Driver");
        // MODE=PostgreSQL: enables PostgreSQL-dialect compatibility in H2
        // DB_CLOSE_DELAY=-1: keeps the in-memory DB alive for the JVM lifetime
        // DB_CLOSE_ON_EXIT=FALSE: prevents H2 from closing on JVM shutdown hook
        ds.setUrl("jdbc:h2:mem:testdb;MODE=PostgreSQL;DB_CLOSE_DELAY=-1;DB_CLOSE_ON_EXIT=FALSE");
        ds.setUsername("sa");
        ds.setPassword("");
        ds.setInitialSize(1);
        ds.setMaxTotal(5);
        return ds;
    }

    /**
     * Runs src/test/resources/schema.sql when the application context loads.
     * The H2 schema uses BIGINT AUTO_INCREMENT instead of PostgreSQL BIGSERIAL,
     * and starts with DROP TABLE IF EXISTS to ensure a clean slate on every
     * context reload (e.g., when multiple test classes force context refresh).
     */
    @Bean
    public DataSourceInitializer dataSourceInitializer() {
        ResourceDatabasePopulator populator = new ResourceDatabasePopulator();
        populator.addScript(new ClassPathResource("schema.sql"));

        DataSourceInitializer initializer = new DataSourceInitializer();
        initializer.setDataSource(dataSource());
        initializer.setDatabasePopulator(populator);
        return initializer;
    }

    @Bean
    public SqlSessionFactoryBean sqlSessionFactory() throws Exception {
        SqlSessionFactoryBean factory = new SqlSessionFactoryBean();
        factory.setDataSource(dataSource());
        factory.setTypeAliasesPackage("com.example.legacy.model");
        PathMatchingResourcePatternResolver resolver = new PathMatchingResourcePatternResolver();
        factory.setMapperLocations(resolver.getResources("classpath:mappers/*.xml"));
        return factory;
    }

    @Bean
    public PlatformTransactionManager transactionManager() {
        return new DataSourceTransactionManager(dataSource());
    }

    // static: MapperScannerConfigurer is a BeanDefinitionRegistryPostProcessor —
    // same reasoning as production DatabaseConfig.
    @Bean
    public static MapperScannerConfigurer mapperScannerConfigurer() {
        MapperScannerConfigurer configurer = new MapperScannerConfigurer();
        configurer.setBasePackage("com.example.legacy.mapper");
        configurer.setSqlSessionFactoryBeanName("sqlSessionFactory");
        return configurer;
    }
}
