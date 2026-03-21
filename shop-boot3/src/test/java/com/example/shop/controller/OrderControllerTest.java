package com.example.shop.controller;

import com.example.shop.entity.*;
import com.example.shop.mapper.*;
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
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
class OrderControllerTest {

    @Autowired private MockMvc mvc;
    @Autowired private MemberMapper memberMapper;
    @Autowired private ProductMapper productMapper;
    @Autowired private CartMapper cartMapper;
    @Autowired private CartItemMapper cartItemMapper;
    @Autowired private OrderMapper orderMapper;
    @Autowired private PasswordEncoder passwordEncoder;

    private static final String USER_EMAIL = "orderuser@test.com";
    private static final String USER_PASSWORD = "password123";
    private static final String USER2_EMAIL = "orderuser2@test.com";
    private static final String USER2_PASSWORD = "password456";
    private static final String ADMIN_EMAIL = "admin@shop.com";
    private static final String ADMIN_PASSWORD = "admin1234";

    private Member user;
    private Member user2;

    @BeforeEach
    void setUp() {
        user = ensureMember(USER_EMAIL, USER_PASSWORD, "Order User 1", MemberRole.USER);
        user2 = ensureMember(USER2_EMAIL, USER2_PASSWORD, "Order User 2", MemberRole.USER);
    }

    // ── Create Order ────────────────────────────────────────────────────────────

    @Test
    void createOrder_returns201WithStockDecreasedAndCartCleared() throws Exception {
        Product p1 = insertProduct("Widget A", "Gadgets", new BigDecimal("10.00"), 50);
        Product p2 = insertProduct("Widget B", "Gadgets", new BigDecimal("25.00"), 30);
        addToCart(user, p1.getId(), 3);
        addToCart(user, p2.getId(), 2);

        mvc.perform(post("/api/orders")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"shippingAddress": "123 Main St"}
                                """))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").isNumber())
                .andExpect(jsonPath("$.status").value("PENDING"))
                .andExpect(jsonPath("$.shippingAddress").value("123 Main St"))
                .andExpect(jsonPath("$.totalAmount").value(closeTo(80.00, 0.01)))
                .andExpect(jsonPath("$.items.length()").value(2));

        // Verify stock decreased
        Product updated1 = productMapper.findById(p1.getId());
        Product updated2 = productMapper.findById(p2.getId());
        assertEquals(47, updated1.getStockQuantity());
        assertEquals(28, updated2.getStockQuantity());

        // Verify cart cleared
        mvc.perform(get("/api/cart")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD)))
                .andExpect(jsonPath("$.items").isEmpty());
    }

    @Test
    void createOrder_snapshotsPrices() throws Exception {
        Product p = insertProduct("Snapshotted", "Misc", new BigDecimal("99.99"), 10);
        addToCart(user, p.getId(), 1);

        String body = mvc.perform(post("/api/orders")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"shippingAddress": "456 Elm St"}
                                """))
                .andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();

        // Order items have snapshotted name and price
        String itemName = JsonPath.read(body, "$.items[0].productName");
        double unitPrice = ((Number) JsonPath.read(body, "$.items[0].unitPrice")).doubleValue();
        assertEquals("Snapshotted", itemName);
        assertEquals(99.99, unitPrice, 0.01);
    }

    @Test
    void createOrderWithEmptyCart_returns400() throws Exception {
        mvc.perform(post("/api/orders")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"shippingAddress": "789 Oak Ave"}
                                """))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.detail", containsString("Cart is empty")));
    }

    @Test
    void createOrderWithInactiveProduct_returns400() throws Exception {
        Product p = insertProduct("Soon Gone", "Misc", new BigDecimal("10.00"), 100);
        addToCart(user, p.getId(), 1);
        productMapper.softDelete(p.getId());

        mvc.perform(post("/api/orders")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"shippingAddress": "Dead Product Lane"}
                                """))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.detail", containsString("not available")));
    }

    @Test
    void createOrderWithInsufficientStock_returns400() throws Exception {
        Product p = insertProduct("Low Stock", "Misc", new BigDecimal("5.00"), 2);
        addToCart(user, p.getId(), 2);
        // Reduce stock after adding to cart
        productMapper.decreaseStock(p.getId(), 1);

        mvc.perform(post("/api/orders")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"shippingAddress": "No Stock Blvd"}
                                """))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.detail", containsString("Insufficient stock")));
    }

    // ── Get My Orders ───────────────────────────────────────────────────────────

    @Test
    void getMyOrders_returnsPaginated() throws Exception {
        Product p = insertProduct("Repeated", "Misc", new BigDecimal("10.00"), 100);
        // Create 3 orders
        for (int i = 0; i < 3; i++) {
            addToCart(user, p.getId(), 1);
            mvc.perform(post("/api/orders")
                            .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                            .contentType(MediaType.APPLICATION_JSON)
                            .content("""
                                    {"shippingAddress": "Addr %d"}
                                    """.formatted(i)))
                    .andExpect(status().isCreated());
        }

        mvc.perform(get("/api/orders")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .param("page", "0")
                        .param("size", "2"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content.length()").value(2))
                .andExpect(jsonPath("$.totalElements").value(3))
                .andExpect(jsonPath("$.totalPages").value(2))
                .andExpect(jsonPath("$.currentPage").value(0));
    }

    // ── Get Order Detail ────────────────────────────────────────────────────────

    @Test
    void getOrderDetail_returnsOrderWithItems() throws Exception {
        Product p = insertProduct("Detail Item", "Misc", new BigDecimal("15.00"), 10);
        addToCart(user, p.getId(), 2);

        String createBody = mvc.perform(post("/api/orders")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"shippingAddress": "Detail St"}
                                """))
                .andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();

        long orderId = ((Number) JsonPath.read(createBody, "$.id")).longValue();

        mvc.perform(get("/api/orders/{id}", orderId)
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(orderId))
                .andExpect(jsonPath("$.items.length()").value(1))
                .andExpect(jsonPath("$.items[0].productName").value("Detail Item"))
                .andExpect(jsonPath("$.items[0].quantity").value(2))
                .andExpect(jsonPath("$.items[0].unitPrice").value(closeTo(15.00, 0.01)));
    }

    @Test
    void getOrderDetail_otherUserCannotSee() throws Exception {
        Product p = insertProduct("Private Item", "Misc", new BigDecimal("10.00"), 10);
        addToCart(user, p.getId(), 1);

        String createBody = mvc.perform(post("/api/orders")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"shippingAddress": "Private St"}
                                """))
                .andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();

        long orderId = ((Number) JsonPath.read(createBody, "$.id")).longValue();

        // User2 tries to view User1's order → 404 (treated as not found)
        mvc.perform(get("/api/orders/{id}", orderId)
                        .header("Authorization", basicAuth(USER2_EMAIL, USER2_PASSWORD)))
                .andExpect(status().isNotFound());
    }

    // ── Admin Status Update ─────────────────────────────────────────────────────

    @Test
    void adminUpdateStatus_pendingToConfirmed() throws Exception {
        Product p = insertProduct("Admin Item", "Misc", new BigDecimal("10.00"), 10);
        addToCart(user, p.getId(), 1);

        String createBody = mvc.perform(post("/api/orders")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"shippingAddress": "Admin St"}
                                """))
                .andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();

        long orderId = ((Number) JsonPath.read(createBody, "$.id")).longValue();

        mvc.perform(put("/api/orders/{id}/status", orderId)
                        .header("Authorization", basicAuth(ADMIN_EMAIL, ADMIN_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"status": "CONFIRMED"}
                                """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("CONFIRMED"));
    }

    @Test
    void adminSkipStatus_pendingToShipped_returns400() throws Exception {
        Product p = insertProduct("Skip Item", "Misc", new BigDecimal("10.00"), 10);
        addToCart(user, p.getId(), 1);

        String createBody = mvc.perform(post("/api/orders")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"shippingAddress": "Skip St"}
                                """))
                .andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();

        long orderId = ((Number) JsonPath.read(createBody, "$.id")).longValue();

        mvc.perform(put("/api/orders/{id}/status", orderId)
                        .header("Authorization", basicAuth(ADMIN_EMAIL, ADMIN_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"status": "SHIPPED"}
                                """))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.detail", containsString("Invalid status transition")));
    }

    @Test
    void adminBackwardTransition_returns400() throws Exception {
        Product p = insertProduct("Backward Item", "Misc", new BigDecimal("10.00"), 10);
        addToCart(user, p.getId(), 1);

        String createBody = mvc.perform(post("/api/orders")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"shippingAddress": "Backward St"}
                                """))
                .andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();

        long orderId = ((Number) JsonPath.read(createBody, "$.id")).longValue();

        // Advance to CONFIRMED
        mvc.perform(put("/api/orders/{id}/status", orderId)
                        .header("Authorization", basicAuth(ADMIN_EMAIL, ADMIN_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"status": "CONFIRMED"}
                                """))
                .andExpect(status().isOk());

        // Try backward to PENDING
        mvc.perform(put("/api/orders/{id}/status", orderId)
                        .header("Authorization", basicAuth(ADMIN_EMAIL, ADMIN_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"status": "PENDING"}
                                """))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.detail", containsString("Invalid status transition")));
    }

    // ── User Cancel ─────────────────────────────────────────────────────────────

    @Test
    void userCancelPendingOrder_restoresStock() throws Exception {
        Product p = insertProduct("Cancellable", "Misc", new BigDecimal("10.00"), 20);
        addToCart(user, p.getId(), 5);

        String createBody = mvc.perform(post("/api/orders")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"shippingAddress": "Cancel St"}
                                """))
                .andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();

        long orderId = ((Number) JsonPath.read(createBody, "$.id")).longValue();
        assertEquals(15, productMapper.findById(p.getId()).getStockQuantity());

        mvc.perform(put("/api/orders/{id}/cancel", orderId)
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("CANCELLED"));

        // Stock restored
        assertEquals(20, productMapper.findById(p.getId()).getStockQuantity());
    }

    @Test
    void userCancelNonPendingOrder_returns400() throws Exception {
        Product p = insertProduct("Non Cancel", "Misc", new BigDecimal("10.00"), 10);
        addToCart(user, p.getId(), 1);

        String createBody = mvc.perform(post("/api/orders")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"shippingAddress": "No Cancel St"}
                                """))
                .andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();

        long orderId = ((Number) JsonPath.read(createBody, "$.id")).longValue();

        // Advance to CONFIRMED
        orderMapper.updateStatus(orderId, OrderStatus.CONFIRMED);

        mvc.perform(put("/api/orders/{id}/cancel", orderId)
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.detail", containsString("Only PENDING")));
    }

    // ── Admin List All Orders ───────────────────────────────────────────────────

    @Test
    void adminListAllOrders_paginated() throws Exception {
        Product p = insertProduct("Admin List", "Misc", new BigDecimal("10.00"), 100);
        addToCart(user, p.getId(), 1);
        mvc.perform(post("/api/orders")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"shippingAddress": "Addr A"}
                                """))
                .andExpect(status().isCreated());

        addToCart(user2, p.getId(), 1);
        mvc.perform(post("/api/orders")
                        .header("Authorization", basicAuth(USER2_EMAIL, USER2_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"shippingAddress": "Addr B"}
                                """))
                .andExpect(status().isCreated());

        mvc.perform(get("/api/admin/orders")
                        .header("Authorization", basicAuth(ADMIN_EMAIL, ADMIN_PASSWORD)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content.length()").value(2))
                .andExpect(jsonPath("$.totalElements").value(2));
    }

    @Test
    void adminFilterByStatus() throws Exception {
        Product p = insertProduct("Filter Item", "Misc", new BigDecimal("10.00"), 100);
        addToCart(user, p.getId(), 1);

        String body1 = mvc.perform(post("/api/orders")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"shippingAddress": "Filter A"}
                                """))
                .andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();

        long orderId1 = ((Number) JsonPath.read(body1, "$.id")).longValue();

        addToCart(user, p.getId(), 1);
        mvc.perform(post("/api/orders")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"shippingAddress": "Filter B"}
                                """))
                .andExpect(status().isCreated());

        // Confirm first order
        orderMapper.updateStatus(orderId1, OrderStatus.CONFIRMED);

        mvc.perform(get("/api/admin/orders")
                        .header("Authorization", basicAuth(ADMIN_EMAIL, ADMIN_PASSWORD))
                        .param("status", "PENDING"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content.length()").value(1))
                .andExpect(jsonPath("$.totalElements").value(1));

        mvc.perform(get("/api/admin/orders")
                        .header("Authorization", basicAuth(ADMIN_EMAIL, ADMIN_PASSWORD))
                        .param("status", "CONFIRMED"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content.length()").value(1));
    }

    // ── Auth Tests ──────────────────────────────────────────────────────────────

    @Test
    void unauthenticatedOrderAccess_returns401() throws Exception {
        mvc.perform(post("/api/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"shippingAddress": "No Auth St"}
                                """))
                .andExpect(status().isUnauthorized());

        mvc.perform(get("/api/orders"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void userCannotAccessAdminOrderEndpoint_returns403() throws Exception {
        mvc.perform(get("/api/admin/orders")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD)))
                .andExpect(status().isForbidden());
    }

    @Test
    void userCannotUpdateStatus_returns403() throws Exception {
        Product p = insertProduct("Auth Test", "Misc", new BigDecimal("10.00"), 10);
        addToCart(user, p.getId(), 1);

        String body = mvc.perform(post("/api/orders")
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"shippingAddress": "Auth St"}
                                """))
                .andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();

        long orderId = ((Number) JsonPath.read(body, "$.id")).longValue();

        mvc.perform(put("/api/orders/{id}/status", orderId)
                        .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"status": "CONFIRMED"}
                                """))
                .andExpect(status().isForbidden());
    }

    // ── Helpers ─────────────────────────────────────────────────────────────────

    private Member ensureMember(String email, String password, String name, MemberRole role) {
        Member existing = memberMapper.findByEmail(email);
        if (existing != null) return existing;
        Member m = new Member();
        m.setEmail(email);
        m.setPassword(passwordEncoder.encode(password));
        m.setName(name);
        m.setPhone("01012345678");
        m.setAddress("Seoul");
        m.setRole(role);
        m.setActive(true);
        memberMapper.insert(m);
        return memberMapper.findByEmail(email);
    }

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

    private void addToCart(Member member, Long productId, int quantity) {
        Cart cart = cartMapper.findByMemberId(member.getId());
        if (cart == null) {
            cart = new Cart();
            cart.setMemberId(member.getId());
            cartMapper.insertCart(cart);
        }
        CartItem item = new CartItem();
        item.setCartId(cart.getId());
        item.setProductId(productId);
        item.setQuantity(quantity);
        cartItemMapper.insertItem(item);
    }

    private String basicAuth(String username, String password) {
        return "Basic " + Base64.getEncoder().encodeToString((username + ":" + password).getBytes());
    }
}
