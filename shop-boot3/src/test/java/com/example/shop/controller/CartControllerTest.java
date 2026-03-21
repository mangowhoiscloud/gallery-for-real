package com.example.shop.controller;

import com.example.shop.entity.Member;
import com.example.shop.entity.MemberRole;
import com.example.shop.entity.Product;
import com.example.shop.entity.ProductStatus;
import com.example.shop.mapper.MemberMapper;
import com.example.shop.mapper.ProductMapper;
import com.jayway.jsonpath.JsonPath;
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

import java.math.BigDecimal;
import java.util.Base64;

import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
class CartControllerTest {

    @Autowired
    private MockMvc mvc;

    @Autowired
    private ProductMapper productMapper;

    @Autowired
    private MemberMapper memberMapper;

    @Autowired
    private PasswordEncoder passwordEncoder;

    private static final String USER_EMAIL = "cartuser@test.com";
    private static final String USER_PASSWORD = "password123";

    @BeforeEach
    void setUp() {
        if (memberMapper.findByEmail(USER_EMAIL) == null) {
            Member user = new Member();
            user.setEmail(USER_EMAIL);
            user.setPassword(passwordEncoder.encode(USER_PASSWORD));
            user.setName("Cart Test User");
            user.setPhone("01099998888");
            user.setAddress("Seoul");
            user.setRole(MemberRole.USER);
            user.setActive(true);
            memberMapper.insert(user);
        }
    }

    // ── Get Cart ──────────────────────────────────────────────────────────────

    @Test
    void getEmptyCart_returns200WithEmptyItemsAndZeroTotal() throws Exception {
        mvc.perform(get("/api/cart")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.cartId").isNumber())
                .andExpect(jsonPath("$.items").isArray())
                .andExpect(jsonPath("$.items").isEmpty())
                .andExpect(jsonPath("$.cartTotal").value(0));
    }

    @Test
    void unauthenticatedAccess_returns401() throws Exception {
        mvc.perform(get("/api/cart"))
                .andExpect(status().isUnauthorized());
    }

    // ── Add Item ──────────────────────────────────────────────────────────────

    @Test
    void addItem_returns201WithEnrichedResponse() throws Exception {
        Product p = insertProduct("Laptop", "Electronics", new BigDecimal("999.99"), 10);

        mvc.perform(post("/api/cart/items")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"productId": %d, "quantity": 2}
                                """.formatted(p.getId())))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.items").isArray())
                .andExpect(jsonPath("$.items.length()").value(1))
                .andExpect(jsonPath("$.items[0].productId").value(p.getId().intValue()))
                .andExpect(jsonPath("$.items[0].productName").value("Laptop"))
                .andExpect(jsonPath("$.items[0].quantity").value(2))
                .andExpect(jsonPath("$.items[0].productStatus").value("ACTIVE"))
                .andExpect(jsonPath("$.items[0].subtotal").value(closeTo(1999.98, 0.01)))
                .andExpect(jsonPath("$.cartTotal").value(closeTo(1999.98, 0.01)));
    }

    @Test
    void addSameProductAgain_incrementsQuantity() throws Exception {
        Product p = insertProduct("Widget", "Misc", new BigDecimal("10.00"), 20);

        // First add: qty = 3
        mvc.perform(post("/api/cart/items")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"productId": %d, "quantity": 3}
                                """.formatted(p.getId())))
                .andExpect(status().isCreated());

        // Second add: qty = 2, should become 5 total
        mvc.perform(post("/api/cart/items")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"productId": %d, "quantity": 2}
                                """.formatted(p.getId())))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.items.length()").value(1))
                .andExpect(jsonPath("$.items[0].quantity").value(5));
    }

    @Test
    void addItemExceedingStock_returns400() throws Exception {
        Product p = insertProduct("Limited Stock Item", "Misc", new BigDecimal("50.00"), 5);

        mvc.perform(post("/api/cart/items")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"productId": %d, "quantity": 10}
                                """.formatted(p.getId())))
                .andExpect(status().isBadRequest());
    }

    @Test
    void addInactiveProduct_returns400() throws Exception {
        Product p = insertProduct("Discontinued Item", "Misc", new BigDecimal("20.00"), 100);
        productMapper.softDelete(p.getId());

        mvc.perform(post("/api/cart/items")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"productId": %d, "quantity": 1}
                                """.formatted(p.getId())))
                .andExpect(status().isBadRequest());
    }

    // ── Update Item ───────────────────────────────────────────────────────────

    @Test
    void updateItemQuantity_returns200() throws Exception {
        Product p = insertProduct("Book", "Books", new BigDecimal("20.00"), 10);

        String addBody = mvc.perform(post("/api/cart/items")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"productId": %d, "quantity": 1}
                                """.formatted(p.getId())))
                .andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();

        long itemId = ((Number) JsonPath.read(addBody, "$.items[0].itemId")).longValue();

        mvc.perform(put("/api/cart/items/{itemId}", itemId)
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"quantity": 4}
                                """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.items[0].quantity").value(4))
                .andExpect(jsonPath("$.items[0].subtotal").value(closeTo(80.00, 0.01)))
                .andExpect(jsonPath("$.cartTotal").value(closeTo(80.00, 0.01)));
    }

    @Test
    void updateItemExceedingStock_returns400() throws Exception {
        Product p = insertProduct("Scarce Item", "Misc", new BigDecimal("5.00"), 3);

        String addBody = mvc.perform(post("/api/cart/items")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"productId": %d, "quantity": 1}
                                """.formatted(p.getId())))
                .andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();

        long itemId = ((Number) JsonPath.read(addBody, "$.items[0].itemId")).longValue();

        mvc.perform(put("/api/cart/items/{itemId}", itemId)
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"quantity": 10}
                                """))
                .andExpect(status().isBadRequest());
    }

    // ── Remove Item ───────────────────────────────────────────────────────────

    @Test
    void removeItem_returns204() throws Exception {
        Product p = insertProduct("To Remove", "Misc", new BigDecimal("15.00"), 5);

        String addBody = mvc.perform(post("/api/cart/items")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"productId": %d, "quantity": 1}
                                """.formatted(p.getId())))
                .andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();

        long itemId = ((Number) JsonPath.read(addBody, "$.items[0].itemId")).longValue();

        mvc.perform(delete("/api/cart/items/{itemId}", itemId)
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD)))
                .andExpect(status().isNoContent());

        // Cart should now be empty
        mvc.perform(get("/api/cart")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.items").isEmpty());
    }

    // ── Clear Cart ────────────────────────────────────────────────────────────

    @Test
    void clearCart_returns204() throws Exception {
        Product p1 = insertProduct("Item A", "Misc", new BigDecimal("10.00"), 5);
        Product p2 = insertProduct("Item B", "Misc", new BigDecimal("20.00"), 5);

        mvc.perform(post("/api/cart/items")
                .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {"productId": %d, "quantity": 1}
                        """.formatted(p1.getId())));
        mvc.perform(post("/api/cart/items")
                .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {"productId": %d, "quantity": 1}
                        """.formatted(p2.getId())));

        mvc.perform(delete("/api/cart")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD)))
                .andExpect(status().isNoContent());

        mvc.perform(get("/api/cart")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.items").isEmpty())
                .andExpect(jsonPath("$.cartTotal").value(0));
    }

    // ── Inactive Product in Cart ──────────────────────────────────────────────

    @Test
    void cartShowsInactiveProductStatus() throws Exception {
        Product p = insertProduct("Soon Inactive", "Misc", new BigDecimal("30.00"), 10);

        mvc.perform(post("/api/cart/items")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"productId": %d, "quantity": 2}
                                """.formatted(p.getId())))
                .andExpect(status().isCreated());

        // Product becomes inactive (e.g. admin soft-deletes it)
        productMapper.softDelete(p.getId());

        // Cart still shows the item but with INACTIVE status
        mvc.perform(get("/api/cart")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.items.length()").value(1))
                .andExpect(jsonPath("$.items[0].productStatus").value("INACTIVE"));
    }

    // ── Subtotal and CartTotal Calculations ───────────────────────────────────

    @Test
    void verifySubtotalAndCartTotalCalculations() throws Exception {
        Product p1 = insertProduct("Product X", "Misc", new BigDecimal("15.00"), 50);
        Product p2 = insertProduct("Product Y", "Misc", new BigDecimal("25.00"), 50);

        mvc.perform(post("/api/cart/items")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"productId": %d, "quantity": 3}
                                """.formatted(p1.getId())))
                .andExpect(status().isCreated());

        mvc.perform(post("/api/cart/items")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"productId": %d, "quantity": 2}
                                """.formatted(p2.getId())))
                .andExpect(status().isCreated());

        // p1: 15.00 * 3 = 45.00, p2: 25.00 * 2 = 50.00, total = 95.00
        mvc.perform(get("/api/cart")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.items.length()").value(2))
                .andExpect(jsonPath("$.items[?(@.productName == 'Product X')].subtotal", hasItem(closeTo(45.00, 0.01))))
                .andExpect(jsonPath("$.items[?(@.productName == 'Product Y')].subtotal", hasItem(closeTo(50.00, 0.01))))
                .andExpect(jsonPath("$.cartTotal").value(closeTo(95.00, 0.01)));
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private Product insertProduct(String name, String category, BigDecimal price, int stock) {
        Product p = new Product();
        p.setName(name);
        p.setDescription("Description for " + name);
        p.setPrice(price);
        p.setStockQuantity(stock);
        p.setCategory(category);
        p.setImageUrl("https://example.com/img/" + name.replace(" ", "_") + ".jpg");
        p.setStatus(ProductStatus.ACTIVE);
        productMapper.insert(p);
        return p;
    }

    private String basicAuth(String username, String password) {
        return "Basic " + Base64.getEncoder().encodeToString((username + ":" + password).getBytes());
    }
}
