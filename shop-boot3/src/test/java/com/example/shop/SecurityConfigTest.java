package com.example.shop;

import com.example.shop.entity.Member;
import com.example.shop.entity.MemberRole;
import com.example.shop.mapper.MemberMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import java.util.Base64;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
class SecurityConfigTest {

    @Autowired
    private MockMvc mvc;

    @Autowired
    private MemberMapper memberMapper;

    @Autowired
    private PasswordEncoder passwordEncoder;

    // Public product listing — security allows through (reaches controller which is absent → 404, not 401)
    @Test
    void publicProductEndpoint_noAuth_notBlockedBySecurity() throws Exception {
        mvc.perform(get("/api/products"))
           .andExpect(result ->
               assertThat(result.getResponse().getStatus())
                   .isNotEqualTo(HttpStatus.UNAUTHORIZED.value()));
    }

    // Public product search — security allows through
    @Test
    void publicProductSearch_noAuth_notBlockedBySecurity() throws Exception {
        mvc.perform(get("/api/products/search"))
           .andExpect(result ->
               assertThat(result.getResponse().getStatus())
                   .isNotEqualTo(HttpStatus.UNAUTHORIZED.value()));
    }

    // POST /api/members (registration) is open — no auth required
    @Test
    void registrationEndpoint_noAuth_notBlockedBySecurity() throws Exception {
        mvc.perform(post("/api/members")
               .contentType(MediaType.APPLICATION_JSON)
               .content("{}"))
           .andExpect(result ->
               assertThat(result.getResponse().getStatus())
                   .isNotEqualTo(HttpStatus.UNAUTHORIZED.value()));
    }

    // Cart endpoint requires authentication — returns 401 without credentials
    @Test
    void cartEndpoint_noAuth_returns401() throws Exception {
        mvc.perform(get("/api/cart"))
           .andExpect(status().isUnauthorized());
    }

    // Admin endpoint returns 403 when authenticated as USER role
    @Test
    void adminEndpoint_userRole_returns403() throws Exception {
        Member user = buildMember("user@security-test.com", MemberRole.USER, true);
        memberMapper.insert(user);

        mvc.perform(get("/api/admin/orders")
               .header("Authorization", basicAuth("user@security-test.com", "password")))
           .andExpect(status().isForbidden());
    }

    // Admin endpoint accessible with ADMIN role (gets through security → 404 since no controller yet)
    @Test
    void adminEndpoint_adminRole_notBlockedBySecurity() throws Exception {
        // admin@shop.com / admin1234 seeded by AdminDataInitializer
        mvc.perform(get("/api/admin/orders")
               .header("Authorization", basicAuth("admin@shop.com", "admin1234")))
           .andExpect(result ->
               assertThat(result.getResponse().getStatus())
                   .isNotEqualTo(HttpStatus.FORBIDDEN.value()));
    }

    // Inactive member credentials rejected — returns 401
    @Test
    void inactiveMember_returns401() throws Exception {
        Member inactive = buildMember("inactive@security-test.com", MemberRole.USER, false);
        memberMapper.insert(inactive);

        mvc.perform(get("/api/cart")
               .header("Authorization", basicAuth("inactive@security-test.com", "password")))
           .andExpect(status().isUnauthorized());
    }

    private Member buildMember(String email, MemberRole role, boolean active) {
        Member m = new Member();
        m.setEmail(email);
        m.setPassword(passwordEncoder.encode("password"));
        m.setName("Test");
        m.setPhone("01012345678");
        m.setAddress("Seoul");
        m.setRole(role);
        m.setActive(active);
        return m;
    }

    private String basicAuth(String username, String password) {
        String credentials = username + ":" + password;
        return "Basic " + Base64.getEncoder().encodeToString(credentials.getBytes());
    }
}
