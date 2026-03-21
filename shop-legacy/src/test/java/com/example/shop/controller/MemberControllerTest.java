package com.example.shop.controller;

import com.example.shop.config.SecurityConfig;
import com.example.shop.config.TestConfig;
import com.example.shop.domain.Member;
import com.example.shop.domain.Order;
import com.example.shop.dto.MemberResponse;
import com.example.shop.mapper.MemberMapper;
import com.example.shop.mapper.OrderMapper;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;
import org.springframework.test.context.web.WebAppConfiguration;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.context.WebApplicationContext;
import org.springframework.web.servlet.config.annotation.EnableWebMvc;

import java.math.BigDecimal;

import static org.junit.Assert.*;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.httpBasic;
import static org.springframework.security.test.web.servlet.setup.SecurityMockMvcConfigurers.springSecurity;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration(classes = MemberControllerTest.TestWebConfig.class)
@WebAppConfiguration
@Transactional
public class MemberControllerTest {

    @Configuration
    @EnableWebMvc
    @ComponentScan({"com.example.shop.security", "com.example.shop.service", "com.example.shop.controller"})
    @Import({TestConfig.class, SecurityConfig.class})
    static class TestWebConfig {}

    @Autowired private WebApplicationContext wac;
    @Autowired private MemberMapper memberMapper;
    @Autowired private OrderMapper orderMapper;
    @Autowired private PasswordEncoder passwordEncoder;

    private MockMvc mockMvc;
    private ObjectMapper objectMapper;

    private static final String EMAIL = "ctrl_test@example.com";
    private static final String PASSWORD = "password123";

    @Before
    public void setUp() {
        objectMapper = new ObjectMapper();
        mockMvc = MockMvcBuilders.webAppContextSetup(wac)
                .apply(springSecurity())
                .build();
    }

    private Member insertMember() {
        Member member = new Member();
        member.setEmail(EMAIL);
        member.setPassword(passwordEncoder.encode(PASSWORD));
        member.setName("Test User");
        member.setRole(Member.Role.USER);
        memberMapper.insert(member);
        return member;
    }

    @Test
    public void registerSuccess201() throws Exception {
        String json = "{\"email\":\"new_reg@example.com\",\"password\":\"password123\",\"name\":\"New User\"}";
        MvcResult result = mockMvc.perform(post("/api/members")
                .contentType(MediaType.APPLICATION_JSON)
                .content(json))
                .andExpect(status().isCreated())
                .andReturn();

        String body = result.getResponse().getContentAsString();
        assertFalse("Response must not contain password field", body.contains("\"password\""));

        MemberResponse response = objectMapper.readValue(body, MemberResponse.class);
        assertNotNull(response.getId());
        assertEquals("new_reg@example.com", response.getEmail());
        assertEquals("New User", response.getName());
        assertEquals("USER", response.getRole());
    }

    @Test
    public void registerDuplicateEmail409() throws Exception {
        insertMember();
        String json = "{\"email\":\"" + EMAIL + "\",\"password\":\"password123\",\"name\":\"Duplicate\"}";
        mockMvc.perform(post("/api/members")
                .contentType(MediaType.APPLICATION_JSON)
                .content(json))
                .andExpect(status().isConflict());
    }

    @Test
    public void registerInvalidEmail400() throws Exception {
        String json = "{\"email\":\"not-an-email\",\"password\":\"password123\",\"name\":\"User\"}";
        mockMvc.perform(post("/api/members")
                .contentType(MediaType.APPLICATION_JSON)
                .content(json))
                .andExpect(status().isBadRequest());
    }

    @Test
    public void loginSuccess200() throws Exception {
        insertMember();
        String json = "{\"email\":\"" + EMAIL + "\",\"password\":\"" + PASSWORD + "\"}";
        MvcResult result = mockMvc.perform(post("/api/members/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(json))
                .andExpect(status().isOk())
                .andReturn();

        MemberResponse response = objectMapper.readValue(result.getResponse().getContentAsString(), MemberResponse.class);
        assertEquals(EMAIL, response.getEmail());
        assertEquals("Test User", response.getName());
    }

    @Test
    public void loginWrongPassword401() throws Exception {
        insertMember();
        String json = "{\"email\":\"" + EMAIL + "\",\"password\":\"wrongpassword\"}";
        mockMvc.perform(post("/api/members/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(json))
                .andExpect(status().isUnauthorized());
    }

    @Test
    public void getProfile200() throws Exception {
        insertMember();
        MvcResult result = mockMvc.perform(get("/api/members/me")
                .with(httpBasic(EMAIL, PASSWORD)))
                .andExpect(status().isOk())
                .andReturn();

        MemberResponse response = objectMapper.readValue(result.getResponse().getContentAsString(), MemberResponse.class);
        assertEquals(EMAIL, response.getEmail());
        assertEquals("Test User", response.getName());
    }

    @Test
    public void updateProfile200() throws Exception {
        insertMember();
        String json = "{\"name\":\"Updated Name\",\"phone\":\"01012345678\",\"address\":\"New Street 1\"}";
        MvcResult result = mockMvc.perform(put("/api/members/me")
                .contentType(MediaType.APPLICATION_JSON)
                .content(json)
                .with(httpBasic(EMAIL, PASSWORD)))
                .andExpect(status().isOk())
                .andReturn();

        MemberResponse response = objectMapper.readValue(result.getResponse().getContentAsString(), MemberResponse.class);
        assertEquals("Updated Name", response.getName());
        assertEquals("01012345678", response.getPhone());
        assertEquals("New Street 1", response.getAddress());
    }

    @Test
    public void deleteMember204() throws Exception {
        insertMember();
        mockMvc.perform(delete("/api/members/me")
                .with(httpBasic(EMAIL, PASSWORD)))
                .andExpect(status().isNoContent());
    }

    @Test
    public void deleteMemberWithActiveOrders409() throws Exception {
        Member member = insertMember();

        Order order = new Order();
        order.setMemberId(member.getId());
        order.setTotalAmount(new BigDecimal("100.00"));
        order.setStatus(Order.Status.CONFIRMED);
        order.setShippingAddress("123 Test Street");
        orderMapper.insert(order);

        mockMvc.perform(delete("/api/members/me")
                .with(httpBasic(EMAIL, PASSWORD)))
                .andExpect(status().isConflict());
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    public void adminListMembersPaginated() throws Exception {
        Member m = new Member();
        m.setEmail("admin_list_ctrl@example.com");
        m.setPassword(passwordEncoder.encode("password"));
        m.setName("List User");
        m.setRole(Member.Role.USER);
        memberMapper.insert(m);

        MvcResult result = mockMvc.perform(get("/api/members")
                .param("page", "0")
                .param("size", "10"))
                .andExpect(status().isOk())
                .andReturn();

        String body = result.getResponse().getContentAsString();
        assertTrue(body.contains("admin_list_ctrl@example.com"));
        assertTrue(body.contains("totalElements"));
        assertTrue(body.contains("content"));
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    public void adminGetMemberById() throws Exception {
        Member member = insertMember();

        MvcResult result = mockMvc.perform(get("/api/members/" + member.getId()))
                .andExpect(status().isOk())
                .andReturn();

        MemberResponse response = objectMapper.readValue(result.getResponse().getContentAsString(), MemberResponse.class);
        assertEquals(EMAIL, response.getEmail());
        assertEquals(member.getId(), response.getId());
    }

    @Test
    public void unauthenticatedAccessReturns401() throws Exception {
        mockMvc.perform(get("/api/members/me"))
                .andExpect(status().isUnauthorized());
    }
}
