package com.example.shop.config;

import org.springframework.security.web.context.AbstractSecurityWebApplicationInitializer;

/**
 * Registers the Spring Security DelegatingFilterProxy in the servlet container.
 * AbstractSecurityWebApplicationInitializer handles all filter chain registration.
 */
public class SecurityWebApplicationInitializer extends AbstractSecurityWebApplicationInitializer {
    // No-arg constructor: inherits all filter registration logic from super class.
}
