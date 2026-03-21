package com.example.shop.config;

import com.example.shop.domain.Member;
import com.example.shop.mapper.MemberMapper;
import com.example.shop.security.CustomUserDetailsService;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.annotation.Rollback;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;
import org.springframework.test.context.web.WebAppConfiguration;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.context.WebApplicationContext;
import org.springframework.web.servlet.config.annotation.EnableWebMvc;

import static org.junit.Assert.*;
import static org.springframework.security.test.web.servlet.setup.SecurityMockMvcConfigurers.springSecurity;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration(classes = SecurityConfigTest.TestWebConfig.class)
@WebAppConfiguration
@Transactional
public class SecurityConfigTest {

    /**
     * Minimal web configuration for security tests.
     * Combines TestConfig (H2/MyBatis), SecurityConfig (HTTP security rules),
     * and a minimal set of test controllers for exercising the auth rules.
     */
    @Configuration
    @EnableWebMvc
    @ComponentScan("com.example.shop.security")
    @Import({TestConfig.class, SecurityConfig.class})
    static class TestWebConfig {
        @Bean
        public TestApiController testApiController() {
            return new TestApiController();
        }
    }

    /**
     * Minimal controllers representing the three access tiers:
     * public (products), user-only (me, cart), and admin-only (admin/orders).
     */
    @RestController
    static class TestApiController {
        @GetMapping("/api/products") public String products() { return "ok"; }
        @GetMapping("/api/members/me") public String me() { return "ok"; }
        @GetMapping("/api/cart") public String cart() { return "ok"; }
        @GetMapping("/api/admin/orders") public String adminOrders() { return "ok"; }
    }

    @Autowired private WebApplicationContext wac;
    @Autowired private MemberMapper memberMapper;
    @Autowired private PasswordEncoder passwordEncoder;
    @Autowired private CustomUserDetailsService userDetailsService;

    private MockMvc mockMvc;

    @Before
    public void setUp() {
        mockMvc = MockMvcBuilders.webAppContextSetup(wac)
                .apply(springSecurity())
                .build();
    }

    // --- Authorization rule tests (use @WithMockUser — no DB needed) ---

    @Test
    public void unauthenticatedRequestToUserEndpointReturns401() throws Exception {
        mockMvc.perform(get("/api/members/me"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    public void publicProductsEndpointAccessibleWithoutAuth() throws Exception {
        mockMvc.perform(get("/api/products"))
                .andExpect(status().isOk());
    }

    @Test
    @WithMockUser(roles = "USER")
    public void userCanAccessOwnProfile() throws Exception {
        mockMvc.perform(get("/api/members/me"))
                .andExpect(status().isOk());
    }

    @Test
    @WithMockUser(roles = "USER")
    public void userCanAccessCart() throws Exception {
        mockMvc.perform(get("/api/cart"))
                .andExpect(status().isOk());
    }

    @Test
    @WithMockUser(roles = "USER")
    public void userCannotAccessAdminEndpointReturns403() throws Exception {
        mockMvc.perform(get("/api/admin/orders"))
                .andExpect(status().isForbidden());
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    public void adminCanAccessAdminOrders() throws Exception {
        mockMvc.perform(get("/api/admin/orders"))
                .andExpect(status().isOk());
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    public void adminCanAlsoAccessUserProfileEndpoint() throws Exception {
        mockMvc.perform(get("/api/members/me"))
                .andExpect(status().isOk());
    }

    // --- BCrypt tests ---

    @Test
    public void bcryptPasswordEncoderMatchesCorrectPassword() {
        String raw = "password123";
        String encoded = passwordEncoder.encode(raw);
        assertTrue(passwordEncoder.matches(raw, encoded));
    }

    @Test
    public void bcryptPasswordEncoderRejectsWrongPassword() {
        String encoded = passwordEncoder.encode("correct");
        assertFalse(passwordEncoder.matches("wrong", encoded));
    }

    // --- CustomUserDetailsService tests (use @Transactional — same tx as mapper insert) ---

    @Test
    public void userDetailsServiceLoadsUserByEmail() {
        Member member = new Member();
        member.setEmail("sectest_user@example.com");
        member.setPassword(passwordEncoder.encode("pass123"));
        member.setName("Security Test User");
        member.setRole(Member.Role.USER);
        memberMapper.insert(member);

        UserDetails details = userDetailsService.loadUserByUsername("sectest_user@example.com");

        assertEquals("sectest_user@example.com", details.getUsername());
        assertTrue(passwordEncoder.matches("pass123", details.getPassword()));
        assertTrue(details.getAuthorities().stream()
                .anyMatch(a -> a.getAuthority().equals("ROLE_USER")));
    }

    @Test
    public void userDetailsServiceLoadsAdminWithAdminRole() {
        Member admin = new Member();
        admin.setEmail("sectest_admin@example.com");
        admin.setPassword(passwordEncoder.encode("admin123"));
        admin.setName("Security Test Admin");
        admin.setRole(Member.Role.ADMIN);
        memberMapper.insert(admin);

        UserDetails details = userDetailsService.loadUserByUsername("sectest_admin@example.com");

        assertTrue(details.getAuthorities().stream()
                .anyMatch(a -> a.getAuthority().equals("ROLE_ADMIN")));
    }

    @Test(expected = UsernameNotFoundException.class)
    public void userDetailsServiceThrowsForUnknownEmail() {
        userDetailsService.loadUserByUsername("nobody_at_all@example.com");
    }
}
