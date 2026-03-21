package com.example.shop.config;

import com.example.shop.security.CustomUserDetailsService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.authentication.builders.AuthenticationManagerBuilder;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;

@Configuration
@EnableWebSecurity
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    @Autowired
    private CustomUserDetailsService userDetailsService;

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Override
    protected void configure(AuthenticationManagerBuilder auth) throws Exception {
        auth.userDetailsService(userDetailsService)
                .passwordEncoder(passwordEncoder());
    }

    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http
            .csrf().disable()
            .sessionManagement()
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            .and()
            .httpBasic()
            .and()
            .authorizeRequests()
                // Public endpoints
                .antMatchers(HttpMethod.POST, "/api/members").permitAll()
                .antMatchers(HttpMethod.POST, "/api/members/login").permitAll()
                .antMatchers(HttpMethod.GET, "/api/products", "/api/products/**").permitAll()
                // User profile endpoints — must precede generic /api/members/* admin rule
                .antMatchers("/api/members/me").hasAnyRole("USER", "ADMIN")
                // Cart and orders — authenticated users only
                .antMatchers("/api/cart/**").hasAnyRole("USER", "ADMIN")
                .antMatchers("/api/orders/**").hasAnyRole("USER", "ADMIN")
                // Admin member management
                .antMatchers(HttpMethod.GET, "/api/members", "/api/members/*").hasRole("ADMIN")
                // Admin product management
                .antMatchers(HttpMethod.POST, "/api/products", "/api/products/**").hasRole("ADMIN")
                .antMatchers(HttpMethod.PUT, "/api/products/**").hasRole("ADMIN")
                .antMatchers(HttpMethod.DELETE, "/api/products/**").hasRole("ADMIN")
                // Admin order management
                .antMatchers("/api/admin/**").hasRole("ADMIN")
                // Static resources
                .antMatchers("/static/**").permitAll()
                // All other requests require authentication
                .anyRequest().authenticated();
    }
}
