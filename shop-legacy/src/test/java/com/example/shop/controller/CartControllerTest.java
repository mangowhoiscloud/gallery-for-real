package com.example.shop.controller;

import com.example.shop.config.SecurityConfig;
import com.example.shop.config.TestConfig;
import com.example.shop.domain.Member;
import com.example.shop.domain.Product;
import com.example.shop.mapper.CartItemMapper;
import com.example.shop.mapper.CartMapper;
import com.example.shop.mapper.MemberMapper;
import com.example.shop.mapper.ProductMapper;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.security.crypto.password.PasswordEncoder;
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
@ContextConfiguration(classes = CartControllerTest.TestWebConfig.class)
@WebAppConfiguration
@Transactional
public class CartControllerTest {

    @Configuration
    @EnableWebMvc
    @ComponentScan({"com.example.shop.security", "com.example.shop.service", "com.example.shop.controller"})
    @Import({TestConfig.class, SecurityConfig.class})
    static class TestWebConfig {}

    @Autowired private WebApplicationContext wac;
    @Autowired private MemberMapper memberMapper;
    @Autowired private ProductMapper productMapper;
    @Autowired private CartMapper cartMapper;
    @Autowired private CartItemMapper cartItemMapper;
    @Autowired private PasswordEncoder passwordEncoder;

    private MockMvc mockMvc;

    private static final String EMAIL = "cart_test@example.com";
    private static final String PASSWORD = "password123";

    @Before
    public void setUp() {
        mockMvc = MockMvcBuilders.webAppContextSetup(wac)
                .apply(springSecurity())
                .build();
    }

    private Member insertMember(String email) {
        Member member = new Member();
        member.setEmail(email);
        member.setPassword(passwordEncoder.encode(PASSWORD));
        member.setName("Test User");
        member.setRole(Member.Role.USER);
        memberMapper.insert(member);
        return member;
    }

    private Product insertProduct(String name, int stock, boolean active) {
        Product p = new Product();
        p.setName(name);
        p.setDescription("Desc");
        p.setPrice(new BigDecimal("10.00"));
        p.setStockQuantity(stock);
        p.setCategory("Test");
        p.setStatus(active ? Product.Status.ACTIVE : Product.Status.INACTIVE);
        productMapper.insert(p);
        return p;
    }

    // ──────────────────────────────────────────────────────────────────────
    // GET /api/cart — auto-creates cart if none exists
    // ──────────────────────────────────────────────────────────────────────

    @Test
    public void getEmptyCartAutoCreates() throws Exception {
        insertMember(EMAIL);

        MvcResult result = mockMvc.perform(get("/api/cart")
                .with(httpBasic(EMAIL, PASSWORD)))
                .andExpect(status().isOk())
                .andReturn();

        String body = result.getResponse().getContentAsString();
        assertTrue(body.contains("items"));
        assertTrue(body.contains("cartTotal"));
        assertTrue(body.contains("[]"));
    }

    // ──────────────────────────────────────────────────────────────────────
    // POST /api/cart/items — add item
    // ──────────────────────────────────────────────────────────────────────

    @Test
    public void addItemToCart() throws Exception {
        insertMember(EMAIL);
        Product product = insertProduct("Gadget", 10, true);

        String json = "{\"productId\":" + product.getId() + ",\"quantity\":2}";

        MvcResult result = mockMvc.perform(post("/api/cart/items")
                .with(httpBasic(EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content(json))
                .andExpect(status().isOk())
                .andReturn();

        String body = result.getResponse().getContentAsString();
        assertTrue(body.contains("Gadget"));
        assertTrue(body.contains("\"quantity\":2"));
    }

    @Test
    public void addSameProductMergesQuantity() throws Exception {
        insertMember(EMAIL);
        Product product = insertProduct("Widget", 10, true);

        String json = "{\"productId\":" + product.getId() + ",\"quantity\":2}";

        // Add once
        mockMvc.perform(post("/api/cart/items")
                .with(httpBasic(EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content(json))
                .andExpect(status().isOk());

        // Add again — should merge
        MvcResult result = mockMvc.perform(post("/api/cart/items")
                .with(httpBasic(EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content(json))
                .andExpect(status().isOk())
                .andReturn();

        String body = result.getResponse().getContentAsString();
        // Quantity should be 4 (2 + 2) and only one item in the list
        assertTrue(body.contains("\"quantity\":4"));
        // Only one item entry
        int count = 0;
        int idx = 0;
        while ((idx = body.indexOf("\"productId\"", idx)) != -1) {
            count++;
            idx++;
        }
        assertEquals(1, count);
    }

    @Test
    public void addInactiveProduct400() throws Exception {
        insertMember(EMAIL);
        Product inactive = insertProduct("Discontinued", 5, false);

        String json = "{\"productId\":" + inactive.getId() + ",\"quantity\":1}";

        mockMvc.perform(post("/api/cart/items")
                .with(httpBasic(EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content(json))
                .andExpect(status().isBadRequest());
    }

    @Test
    public void addExceedingStock400() throws Exception {
        insertMember(EMAIL);
        Product product = insertProduct("LimitedItem", 3, true);

        String json = "{\"productId\":" + product.getId() + ",\"quantity\":5}";

        mockMvc.perform(post("/api/cart/items")
                .with(httpBasic(EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content(json))
                .andExpect(status().isBadRequest());
    }

    // ──────────────────────────────────────────────────────────────────────
    // PUT /api/cart/items/{itemId} — update quantity
    // ──────────────────────────────────────────────────────────────────────

    @Test
    public void updateItemQuantity200() throws Exception {
        insertMember(EMAIL);
        Product product = insertProduct("Updatable", 10, true);

        // Add item first
        String addJson = "{\"productId\":" + product.getId() + ",\"quantity\":2}";
        MvcResult addResult = mockMvc.perform(post("/api/cart/items")
                .with(httpBasic(EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content(addJson))
                .andExpect(status().isOk())
                .andReturn();

        // Extract itemId from response
        String addBody = addResult.getResponse().getContentAsString();
        long itemId = extractFirstItemId(addBody);

        String updateJson = "{\"quantity\":5}";
        MvcResult result = mockMvc.perform(put("/api/cart/items/" + itemId)
                .with(httpBasic(EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content(updateJson))
                .andExpect(status().isOk())
                .andReturn();

        String body = result.getResponse().getContentAsString();
        assertTrue(body.contains("\"quantity\":5"));
    }

    @Test
    public void updateItemExceedingStock400() throws Exception {
        insertMember(EMAIL);
        Product product = insertProduct("StockItem", 3, true);

        // Add item
        String addJson = "{\"productId\":" + product.getId() + ",\"quantity\":1}";
        MvcResult addResult = mockMvc.perform(post("/api/cart/items")
                .with(httpBasic(EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content(addJson))
                .andExpect(status().isOk())
                .andReturn();

        long itemId = extractFirstItemId(addResult.getResponse().getContentAsString());

        String updateJson = "{\"quantity\":10}";
        mockMvc.perform(put("/api/cart/items/" + itemId)
                .with(httpBasic(EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content(updateJson))
                .andExpect(status().isBadRequest());
    }

    // ──────────────────────────────────────────────────────────────────────
    // DELETE /api/cart/items/{itemId} — remove single item
    // ──────────────────────────────────────────────────────────────────────

    @Test
    public void removeSingleItem204() throws Exception {
        insertMember(EMAIL);
        Product product = insertProduct("RemovableItem", 10, true);

        String addJson = "{\"productId\":" + product.getId() + ",\"quantity\":1}";
        MvcResult addResult = mockMvc.perform(post("/api/cart/items")
                .with(httpBasic(EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content(addJson))
                .andExpect(status().isOk())
                .andReturn();

        long itemId = extractFirstItemId(addResult.getResponse().getContentAsString());

        mockMvc.perform(delete("/api/cart/items/" + itemId)
                .with(httpBasic(EMAIL, PASSWORD)))
                .andExpect(status().isNoContent());

        // Verify cart is empty
        MvcResult cartResult = mockMvc.perform(get("/api/cart")
                .with(httpBasic(EMAIL, PASSWORD)))
                .andExpect(status().isOk())
                .andReturn();

        assertTrue(cartResult.getResponse().getContentAsString().contains("[]"));
    }

    // ──────────────────────────────────────────────────────────────────────
    // DELETE /api/cart — clear all items
    // ──────────────────────────────────────────────────────────────────────

    @Test
    public void clearCart204() throws Exception {
        insertMember(EMAIL);
        Product p1 = insertProduct("Item1", 10, true);
        Product p2 = insertProduct("Item2", 10, true);

        mockMvc.perform(post("/api/cart/items")
                .with(httpBasic(EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"productId\":" + p1.getId() + ",\"quantity\":1}"))
                .andExpect(status().isOk());

        mockMvc.perform(post("/api/cart/items")
                .with(httpBasic(EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"productId\":" + p2.getId() + ",\"quantity\":1}"))
                .andExpect(status().isOk());

        mockMvc.perform(delete("/api/cart")
                .with(httpBasic(EMAIL, PASSWORD)))
                .andExpect(status().isNoContent());

        MvcResult cartResult = mockMvc.perform(get("/api/cart")
                .with(httpBasic(EMAIL, PASSWORD)))
                .andExpect(status().isOk())
                .andReturn();

        assertTrue(cartResult.getResponse().getContentAsString().contains("[]"));
    }

    // ──────────────────────────────────────────────────────────────────────
    // Live product data in cart response
    // ──────────────────────────────────────────────────────────────────────

    @Test
    public void cartItemsShowLiveProductData() throws Exception {
        insertMember(EMAIL);
        Product product = insertProduct("LiveDataProduct", 10, true);

        String addJson = "{\"productId\":" + product.getId() + ",\"quantity\":3}";
        mockMvc.perform(post("/api/cart/items")
                .with(httpBasic(EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content(addJson))
                .andExpect(status().isOk());

        MvcResult result = mockMvc.perform(get("/api/cart")
                .with(httpBasic(EMAIL, PASSWORD)))
                .andExpect(status().isOk())
                .andReturn();

        String body = result.getResponse().getContentAsString();
        assertTrue(body.contains("LiveDataProduct"));
        assertTrue(body.contains("unitPrice"));
        assertTrue(body.contains("subtotal"));
        assertTrue(body.contains("ACTIVE"));
        // subtotal = 10.00 * 3 = 30.00
        assertTrue(body.contains("30.00") || body.contains("30"));
    }

    // ──────────────────────────────────────────────────────────────────────
    // Unauthenticated access blocked
    // ──────────────────────────────────────────────────────────────────────

    @Test
    public void unauthenticatedAccess401() throws Exception {
        mockMvc.perform(get("/api/cart"))
                .andExpect(status().isUnauthorized());
    }

    // ──────────────────────────────────────────────────────────────────────
    // Cannot modify another user's cart items
    // ──────────────────────────────────────────────────────────────────────

    @Test
    public void cannotModifyOtherUserCartItem() throws Exception {
        Member owner = insertMember("owner@example.com");
        insertMember("other@example.com");
        Product product = insertProduct("OwnerProduct", 10, true);

        // Owner adds item
        String addJson = "{\"productId\":" + product.getId() + ",\"quantity\":1}";
        MvcResult addResult = mockMvc.perform(post("/api/cart/items")
                .with(httpBasic("owner@example.com", PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content(addJson))
                .andExpect(status().isOk())
                .andReturn();

        long itemId = extractFirstItemId(addResult.getResponse().getContentAsString());

        // Other user tries to update owner's item
        mockMvc.perform(put("/api/cart/items/" + itemId)
                .with(httpBasic("other@example.com", PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"quantity\":5}"))
                .andExpect(status().isNotFound());
    }

    // ──────────────────────────────────────────────────────────────────────
    // Helper
    // ──────────────────────────────────────────────────────────────────────

    private long extractFirstItemId(String body) {
        // Finds the first "id": <number> inside the items array
        int itemsIdx = body.indexOf("\"items\"");
        if (itemsIdx == -1) return -1;
        int idIdx = body.indexOf("\"id\":", itemsIdx);
        if (idIdx == -1) return -1;
        int start = idIdx + 5;
        int end = start;
        while (end < body.length() && Character.isDigit(body.charAt(end))) {
            end++;
        }
        return Long.parseLong(body.substring(start, end));
    }
}
