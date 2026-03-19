package com.example.legacy.config;

import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.PropertySource;

@Configuration
@ComponentScan(basePackages = "com.example.legacy")
@PropertySource("classpath:application.properties")
public class AppConfig {
}
