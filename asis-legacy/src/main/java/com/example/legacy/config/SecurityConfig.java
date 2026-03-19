package com.example.legacy.config;

import com.example.legacy.dto.ErrorResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.config.annotation.authentication.builders.AuthenticationManagerBuilder;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.AuthenticationEntryPoint;
import org.springframework.security.web.access.AccessDeniedHandler;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;

@Configuration
@EnableWebSecurity
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    protected void configure(HttpSecurity http) throws Exception {
        final AuthenticationEntryPoint entryPoint = buildAuthenticationEntryPoint();
        final AccessDeniedHandler deniedHandler = buildAccessDeniedHandler();

        http
            .csrf().disable()
            .sessionManagement()
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
            .httpBasic()
                .authenticationEntryPoint(entryPoint)
                .and()
            .exceptionHandling()
                .authenticationEntryPoint(entryPoint)
                .accessDeniedHandler(deniedHandler)
                .and()
            .authorizeRequests()
                .antMatchers(HttpMethod.GET, "/api/employees/**").hasAnyRole("USER", "ADMIN")
                .antMatchers(HttpMethod.POST, "/api/employees/**").hasRole("ADMIN")
                .antMatchers(HttpMethod.PUT, "/api/employees/**").hasRole("ADMIN")
                .antMatchers(HttpMethod.DELETE, "/api/employees/**").hasRole("ADMIN")
                .anyRequest().authenticated();
    }

    @Override
    protected void configure(AuthenticationManagerBuilder auth) throws Exception {
        auth.inMemoryAuthentication()
            .withUser("admin").password("admin123").roles("ADMIN")
            .and()
            .withUser("user").password("user123").roles("USER");
    }

    private AuthenticationEntryPoint buildAuthenticationEntryPoint() {
        return new AuthenticationEntryPoint() {
            @Override
            public void commence(HttpServletRequest request, HttpServletResponse response,
                    AuthenticationException authException) throws IOException, ServletException {
                response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
                response.setContentType(MediaType.APPLICATION_JSON_VALUE);
                String timestamp = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss").format(new Date());
                ErrorResponse error = new ErrorResponse(
                        HttpServletResponse.SC_UNAUTHORIZED,
                        "Unauthorized",
                        timestamp);
                response.getWriter().write(objectMapper.writeValueAsString(error));
            }
        };
    }

    private AccessDeniedHandler buildAccessDeniedHandler() {
        return new AccessDeniedHandler() {
            @Override
            public void handle(HttpServletRequest request, HttpServletResponse response,
                    AccessDeniedException accessDeniedException) throws IOException, ServletException {
                response.setStatus(HttpServletResponse.SC_FORBIDDEN);
                response.setContentType(MediaType.APPLICATION_JSON_VALUE);
                String timestamp = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss").format(new Date());
                ErrorResponse error = new ErrorResponse(
                        HttpServletResponse.SC_FORBIDDEN,
                        "Forbidden",
                        timestamp);
                response.getWriter().write(objectMapper.writeValueAsString(error));
            }
        };
    }
}
