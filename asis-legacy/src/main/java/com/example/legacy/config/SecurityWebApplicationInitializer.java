package com.example.legacy.config;

import org.springframework.security.web.context.AbstractSecurityWebApplicationInitializer;

/**
 * Registers the Spring Security DelegatingFilterProxy (springSecurityFilterChain)
 * with the servlet container. Required for Java-based config (no web.xml).
 * Must exist alongside WebInitializer; Spring Boot does this automatically,
 * but in plain Spring MVC it must be explicit.
 */
public class SecurityWebApplicationInitializer extends AbstractSecurityWebApplicationInitializer {
    // No content needed — superclass registers springSecurityFilterChain filter
}
