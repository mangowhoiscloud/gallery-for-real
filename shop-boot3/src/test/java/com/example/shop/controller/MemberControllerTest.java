package com.example.shop.controller;

import com.example.shop.entity.Member;
import com.example.shop.entity.MemberRole;
import com.example.shop.mapper.MemberMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import java.util.Base64;

import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
class MemberControllerTest {

    @Autowired
    private MockMvc mvc;

    @Autowired
    private MemberMapper memberMapper;

    @Autowired
    private PasswordEncoder passwordEncoder;

    private static final String USER_EMAIL = "user@test.com";
    private static final String USER_PASSWORD = "password123";
    private static final String ADMIN_EMAIL = "admin@shop.com";
    private static final String ADMIN_PASSWORD = "admin1234";

    @BeforeEach
    void setUp() {
        // Insert a regular user for tests
        if (memberMapper.findByEmail(USER_EMAIL) == null) {
            Member user = new Member();
            user.setEmail(USER_EMAIL);
            user.setPassword(passwordEncoder.encode(USER_PASSWORD));
            user.setName("Test User");
            user.setPhone("01012345678");
            user.setAddress("Seoul");
            user.setRole(MemberRole.USER);
            user.setActive(true);
            memberMapper.insert(user);
        }
    }

    // ── Registration ──────────────────────────────────────────────────────────

    @Test
    void register_success_returns201() throws Exception {
        mvc.perform(post("/api/members")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {
                          "email": "new@example.com",
                          "password": "secret99",
                          "name": "Alice",
                          "phone": "01099991111",
                          "address": "Busan"
                        }
                        """))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.email").value("new@example.com"))
                .andExpect(jsonPath("$.name").value("Alice"))
                .andExpect(jsonPath("$.role").value("USER"))
                .andExpect(jsonPath("$.active").value(true))
                .andExpect(jsonPath("$.password").doesNotExist());
    }

    @Test
    void register_duplicateEmail_returns409() throws Exception {
        // USER_EMAIL already inserted in setUp
        mvc.perform(post("/api/members")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {
                          "email": "%s",
                          "password": "secret99",
                          "name": "Dup",
                          "phone": "01099991111"
                        }
                        """.formatted(USER_EMAIL)))
                .andExpect(status().isConflict());
    }

    @Test
    void register_validationErrors_returns400() throws Exception {
        mvc.perform(post("/api/members")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {
                          "email": "not-an-email",
                          "password": "short",
                          "name": ""
                        }
                        """))
                .andExpect(status().isBadRequest());
    }

    // ── Login ────────────────────────────────────────────────────────────────

    @Test
    void login_success_returns200WithMemberData() throws Exception {
        mvc.perform(post("/api/members/login")
                .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.email").value(USER_EMAIL))
                .andExpect(jsonPath("$.role").value("USER"));
    }

    @Test
    void login_wrongPassword_returns401() throws Exception {
        mvc.perform(post("/api/members/login")
                .header("Authorization", basicAuth(USER_EMAIL, "wrongpassword")))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void login_inactiveMember_returns401() throws Exception {
        Member inactive = new Member();
        inactive.setEmail("inactive@test.com");
        inactive.setPassword(passwordEncoder.encode("password123"));
        inactive.setName("Inactive");
        inactive.setPhone("01012345678");
        inactive.setAddress("Seoul");
        inactive.setRole(MemberRole.USER);
        inactive.setActive(false);
        memberMapper.insert(inactive);

        mvc.perform(post("/api/members/login")
                .header("Authorization", basicAuth("inactive@test.com", "password123")))
                .andExpect(status().isUnauthorized());
    }

    // ── Profile ───────────────────────────────────────────────────────────────

    @Test
    void getProfile_success_returns200() throws Exception {
        mvc.perform(get("/api/members/me")
                .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.email").value(USER_EMAIL))
                .andExpect(jsonPath("$.name").value("Test User"));
    }

    @Test
    void updateProfile_success_returns200AndReflectsChanges() throws Exception {
        mvc.perform(put("/api/members/me")
                .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {
                          "name": "Updated Name",
                          "phone": "01099998888",
                          "address": "Incheon"
                        }
                        """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name").value("Updated Name"))
                .andExpect(jsonPath("$.phone").value("01099998888"))
                .andExpect(jsonPath("$.address").value("Incheon"));
    }

    @Test
    void deactivateAccount_returns204_andSubsequentLoginFails() throws Exception {
        // Deactivate
        mvc.perform(delete("/api/members/me")
                .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD)))
                .andExpect(status().isNoContent());

        // Subsequent login attempt should fail with 401
        mvc.perform(post("/api/members/login")
                .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD)))
                .andExpect(status().isUnauthorized());
    }

    // ── Admin endpoints ───────────────────────────────────────────────────────

    @Test
    void adminListMembers_returns200Paginated() throws Exception {
        mvc.perform(get("/api/members")
                .header("Authorization", basicAuth(ADMIN_EMAIL, ADMIN_PASSWORD))
                .param("page", "0")
                .param("size", "10"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content").isArray())
                .andExpect(jsonPath("$.currentPage").value(0))
                .andExpect(jsonPath("$.pageSize").value(10))
                .andExpect(jsonPath("$.totalElements").isNumber());
    }

    @Test
    void adminGetMemberById_returns200() throws Exception {
        Member user = memberMapper.findByEmail(USER_EMAIL);

        mvc.perform(get("/api/members/{id}", user.getId())
                .header("Authorization", basicAuth(ADMIN_EMAIL, ADMIN_PASSWORD)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(user.getId()))
                .andExpect(jsonPath("$.email").value(USER_EMAIL));
    }

    @Test
    void adminGetMemberById_notFound_returns404() throws Exception {
        mvc.perform(get("/api/members/99999")
                .header("Authorization", basicAuth(ADMIN_EMAIL, ADMIN_PASSWORD)))
                .andExpect(status().isNotFound());
    }

    @Test
    void userCannotAccessAdminListEndpoint_returns403() throws Exception {
        mvc.perform(get("/api/members")
                .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD)))
                .andExpect(status().isForbidden());
    }

    @Test
    void userCannotAccessAdminGetByIdEndpoint_returns403() throws Exception {
        Member user = memberMapper.findByEmail(USER_EMAIL);
        mvc.perform(get("/api/members/{id}", user.getId())
                .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD)))
                .andExpect(status().isForbidden());
    }

    @Test
    void unauthenticated_profileEndpoint_returns401() throws Exception {
        mvc.perform(get("/api/members/me"))
                .andExpect(status().isUnauthorized());
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private String basicAuth(String username, String password) {
        String credentials = username + ":" + password;
        return "Basic " + Base64.getEncoder().encodeToString(credentials.getBytes());
    }
}
