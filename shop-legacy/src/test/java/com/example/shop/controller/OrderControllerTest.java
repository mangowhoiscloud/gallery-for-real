package com.example.shop.controller;

import com.example.shop.config.SecurityConfig;
import com.example.shop.config.TestConfig;
import com.example.shop.domain.Cart;
import com.example.shop.domain.CartItem;
import com.example.shop.domain.Member;
import com.example.shop.domain.Order;
import com.example.shop.domain.OrderItem;
import com.example.shop.domain.Product;
import com.example.shop.mapper.CartItemMapper;
import com.example.shop.mapper.CartMapper;
import com.example.shop.mapper.MemberMapper;
import com.example.shop.mapper.OrderItemMapper;
import com.example.shop.mapper.OrderMapper;
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
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.Assert.*;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.httpBasic;
import static org.springframework.security.test.web.servlet.setup.SecurityMockMvcConfigurers.springSecurity;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration(classes = OrderControllerTest.TestWebConfig.class)
@WebAppConfiguration
@Transactional
public class OrderControllerTest {

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
    @Autowired private OrderMapper orderMapper;
    @Autowired private OrderItemMapper orderItemMapper;
    @Autowired private PasswordEncoder passwordEncoder;

    private MockMvc mockMvc;

    private static final String USER_EMAIL = "order_user@example.com";
    private static final String ADMIN_EMAIL = "order_admin@example.com";
    private static final String PASSWORD = "password123";

    @Before
    public void setUp() {
        mockMvc = MockMvcBuilders.webAppContextSetup(wac)
                .apply(springSecurity())
                .build();
    }

    private Member insertMember(String email, Member.Role role) {
        Member member = new Member();
        member.setEmail(email);
        member.setPassword(passwordEncoder.encode(PASSWORD));
        member.setName("Test User");
        member.setAddress("123 Default St");
        member.setRole(role);
        memberMapper.insert(member);
        return member;
    }

    private Product insertProduct(String name, int stock, BigDecimal price) {
        Product p = new Product();
        p.setName(name);
        p.setDescription("Desc");
        p.setPrice(price);
        p.setStockQuantity(stock);
        p.setCategory("Test");
        p.setStatus(Product.Status.ACTIVE);
        productMapper.insert(p);
        return p;
    }

    private void addToCart(Member member, Product product, int quantity) {
        Cart cart = cartMapper.selectByMemberId(member.getId());
        if (cart == null) {
            cart = new Cart();
            cart.setMemberId(member.getId());
            cartMapper.insert(cart);
        }
        CartItem item = new CartItem();
        item.setCartId(cart.getId());
        item.setProductId(product.getId());
        item.setQuantity(quantity);
        cartItemMapper.insert(item);
    }

    // ──────────────────────────────────────────────────────────────────────
    // POST /api/orders — create order from cart
    // ──────────────────────────────────────────────────────────────────────

    @Test
    public void createOrderSuccess201() throws Exception {
        Member member = insertMember(USER_EMAIL, Member.Role.USER);
        Product product = insertProduct("OrderProduct", 10, new BigDecimal("25.00"));
        addToCart(member, product, 2);

        String json = "{\"shippingAddress\":\"456 Ship Ave\"}";

        MvcResult result = mockMvc.perform(post("/api/orders")
                .with(httpBasic(USER_EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content(json))
                .andExpect(status().isCreated())
                .andReturn();

        String body = result.getResponse().getContentAsString();
        assertTrue(body.contains("PENDING"));
        assertTrue(body.contains("456 Ship Ave"));
        assertTrue(body.contains("50.00"));
        assertTrue(body.contains("OrderProduct"));
        assertTrue(body.contains("\"quantity\":2"));

        // Verify stock decreased
        Product updated = productMapper.selectById(product.getId());
        assertEquals(8, updated.getStockQuantity().intValue());

        // Verify cart cleared
        Cart cart = cartMapper.selectByMemberId(member.getId());
        List<CartItem> cartItems = cartItemMapper.selectByCartId(cart.getId());
        assertTrue(cartItems.isEmpty());
    }

    @Test
    public void createOrderPricesAreSnapshotted() throws Exception {
        Member member = insertMember(USER_EMAIL, Member.Role.USER);
        Product product = insertProduct("SnapshotProduct", 10, new BigDecimal("30.00"));
        addToCart(member, product, 1);

        MvcResult result = mockMvc.perform(post("/api/orders")
                .with(httpBasic(USER_EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"shippingAddress\":\"Addr\"}"))
                .andExpect(status().isCreated())
                .andReturn();

        // Now change the product price
        product.setPrice(new BigDecimal("99.00"));
        productMapper.update(product);

        // Get the order — should still show original price 30.00
        String body = result.getResponse().getContentAsString();
        assertTrue(body.contains("30.00"));
    }

    @Test
    public void createOrderEmptyCart400() throws Exception {
        insertMember(USER_EMAIL, Member.Role.USER);

        mockMvc.perform(post("/api/orders")
                .with(httpBasic(USER_EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"shippingAddress\":\"Addr\"}"))
                .andExpect(status().isBadRequest());
    }

    @Test
    public void createOrderInactiveProduct400() throws Exception {
        Member member = insertMember(USER_EMAIL, Member.Role.USER);
        Product product = insertProduct("ActiveThenInactive", 10, new BigDecimal("10.00"));
        addToCart(member, product, 1);

        // Deactivate product after adding to cart
        product.setStatus(Product.Status.INACTIVE);
        productMapper.update(product);

        mockMvc.perform(post("/api/orders")
                .with(httpBasic(USER_EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"shippingAddress\":\"Addr\"}"))
                .andExpect(status().isBadRequest());
    }

    @Test
    public void createOrderInsufficientStock400() throws Exception {
        Member member = insertMember(USER_EMAIL, Member.Role.USER);
        Product product = insertProduct("LowStockItem", 2, new BigDecimal("10.00"));
        addToCart(member, product, 5);

        MvcResult result = mockMvc.perform(post("/api/orders")
                .with(httpBasic(USER_EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"shippingAddress\":\"Addr\"}"))
                .andExpect(status().isBadRequest())
                .andReturn();

        // Verify no partial changes — stock should still be 2
        Product updated = productMapper.selectById(product.getId());
        assertEquals(2, updated.getStockQuantity().intValue());
    }

    @Test
    public void createOrderWithShippingAddress() throws Exception {
        Member member = insertMember(USER_EMAIL, Member.Role.USER);
        Product product = insertProduct("AddrProduct", 10, new BigDecimal("10.00"));
        addToCart(member, product, 1);

        MvcResult result = mockMvc.perform(post("/api/orders")
                .with(httpBasic(USER_EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"shippingAddress\":\"789 Custom Blvd\"}"))
                .andExpect(status().isCreated())
                .andReturn();

        assertTrue(result.getResponse().getContentAsString().contains("789 Custom Blvd"));
    }

    @Test
    public void createOrderFallbackToMemberAddress() throws Exception {
        Member member = insertMember(USER_EMAIL, Member.Role.USER);
        Product product = insertProduct("FallbackProduct", 10, new BigDecimal("10.00"));
        addToCart(member, product, 1);

        // Empty shipping address in request — falls back to member.address "123 Default St"
        MvcResult result = mockMvc.perform(post("/api/orders")
                .with(httpBasic(USER_EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{}"))
                .andExpect(status().isCreated())
                .andReturn();

        assertTrue(result.getResponse().getContentAsString().contains("123 Default St"));
    }

    @Test
    public void createOrderNoAddress400() throws Exception {
        // Member with no address
        Member member = new Member();
        member.setEmail("noaddr@example.com");
        member.setPassword(passwordEncoder.encode(PASSWORD));
        member.setName("No Addr");
        member.setRole(Member.Role.USER);
        memberMapper.insert(member);

        Product product = insertProduct("NoAddrProduct", 10, new BigDecimal("10.00"));
        addToCart(member, product, 1);

        mockMvc.perform(post("/api/orders")
                .with(httpBasic("noaddr@example.com", PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{}"))
                .andExpect(status().isBadRequest());
    }

    // ──────────────────────────────────────────────────────────────────────
    // GET /api/orders — list my orders
    // ──────────────────────────────────────────────────────────────────────

    @Test
    public void listMyOrdersPaginated() throws Exception {
        Member member = insertMember(USER_EMAIL, Member.Role.USER);
        Product product = insertProduct("ListProduct", 100, new BigDecimal("10.00"));

        // Create 2 orders
        addToCart(member, product, 1);
        mockMvc.perform(post("/api/orders")
                .with(httpBasic(USER_EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"shippingAddress\":\"Addr\"}"))
                .andExpect(status().isCreated());

        addToCart(member, product, 1);
        mockMvc.perform(post("/api/orders")
                .with(httpBasic(USER_EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"shippingAddress\":\"Addr\"}"))
                .andExpect(status().isCreated());

        MvcResult result = mockMvc.perform(get("/api/orders")
                .with(httpBasic(USER_EMAIL, PASSWORD)))
                .andExpect(status().isOk())
                .andReturn();

        String body = result.getResponse().getContentAsString();
        assertTrue(body.contains("\"totalElements\":2"));
        assertTrue(body.contains("content"));
    }

    // ──────────────────────────────────────────────────────────────────────
    // GET /api/orders/{id} — get order detail
    // ──────────────────────────────────────────────────────────────────────

    @Test
    public void getOrderDetail() throws Exception {
        Member member = insertMember(USER_EMAIL, Member.Role.USER);
        Product product = insertProduct("DetailProduct", 10, new BigDecimal("15.00"));
        addToCart(member, product, 3);

        MvcResult createResult = mockMvc.perform(post("/api/orders")
                .with(httpBasic(USER_EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"shippingAddress\":\"Addr\"}"))
                .andExpect(status().isCreated())
                .andReturn();

        long orderId = extractOrderId(createResult.getResponse().getContentAsString());

        MvcResult result = mockMvc.perform(get("/api/orders/" + orderId)
                .with(httpBasic(USER_EMAIL, PASSWORD)))
                .andExpect(status().isOk())
                .andReturn();

        String body = result.getResponse().getContentAsString();
        assertTrue(body.contains("DetailProduct"));
        assertTrue(body.contains("\"quantity\":3"));
        assertTrue(body.contains("15.00"));
    }

    @Test
    public void getOtherUserOrder403() throws Exception {
        Member owner = insertMember(USER_EMAIL, Member.Role.USER);
        insertMember("other_user@example.com", Member.Role.USER);
        Product product = insertProduct("OwnerProduct", 10, new BigDecimal("10.00"));
        addToCart(owner, product, 1);

        MvcResult createResult = mockMvc.perform(post("/api/orders")
                .with(httpBasic(USER_EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"shippingAddress\":\"Addr\"}"))
                .andExpect(status().isCreated())
                .andReturn();

        long orderId = extractOrderId(createResult.getResponse().getContentAsString());

        mockMvc.perform(get("/api/orders/" + orderId)
                .with(httpBasic("other_user@example.com", PASSWORD)))
                .andExpect(status().isForbidden());
    }

    @Test
    public void adminCanGetAnyOrder() throws Exception {
        Member user = insertMember(USER_EMAIL, Member.Role.USER);
        insertMember(ADMIN_EMAIL, Member.Role.ADMIN);
        Product product = insertProduct("AdminViewProduct", 10, new BigDecimal("10.00"));
        addToCart(user, product, 1);

        MvcResult createResult = mockMvc.perform(post("/api/orders")
                .with(httpBasic(USER_EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"shippingAddress\":\"Addr\"}"))
                .andExpect(status().isCreated())
                .andReturn();

        long orderId = extractOrderId(createResult.getResponse().getContentAsString());

        mockMvc.perform(get("/api/orders/" + orderId)
                .with(httpBasic(ADMIN_EMAIL, PASSWORD)))
                .andExpect(status().isOk());
    }

    // ──────────────────────────────────────────────────────────────────────
    // PUT /api/admin/orders/{id}/status — admin status update
    // ──────────────────────────────────────────────────────────────────────

    @Test
    public void updateStatusValidTransitions() throws Exception {
        Member user = insertMember(USER_EMAIL, Member.Role.USER);
        insertMember(ADMIN_EMAIL, Member.Role.ADMIN);
        Product product = insertProduct("StatusProduct", 10, new BigDecimal("10.00"));
        addToCart(user, product, 1);

        MvcResult createResult = mockMvc.perform(post("/api/orders")
                .with(httpBasic(USER_EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"shippingAddress\":\"Addr\"}"))
                .andExpect(status().isCreated())
                .andReturn();

        long orderId = extractOrderId(createResult.getResponse().getContentAsString());

        // PENDING → CONFIRMED
        MvcResult r1 = mockMvc.perform(put("/api/admin/orders/" + orderId + "/status")
                .with(httpBasic(ADMIN_EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"status\":\"CONFIRMED\"}"))
                .andExpect(status().isOk())
                .andReturn();
        assertTrue(r1.getResponse().getContentAsString().contains("CONFIRMED"));

        // CONFIRMED → SHIPPED
        MvcResult r2 = mockMvc.perform(put("/api/admin/orders/" + orderId + "/status")
                .with(httpBasic(ADMIN_EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"status\":\"SHIPPED\"}"))
                .andExpect(status().isOk())
                .andReturn();
        assertTrue(r2.getResponse().getContentAsString().contains("SHIPPED"));

        // SHIPPED → DELIVERED
        MvcResult r3 = mockMvc.perform(put("/api/admin/orders/" + orderId + "/status")
                .with(httpBasic(ADMIN_EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"status\":\"DELIVERED\"}"))
                .andExpect(status().isOk())
                .andReturn();
        assertTrue(r3.getResponse().getContentAsString().contains("DELIVERED"));
    }

    @Test
    public void updateStatusInvalidTransition400() throws Exception {
        Member user = insertMember(USER_EMAIL, Member.Role.USER);
        insertMember(ADMIN_EMAIL, Member.Role.ADMIN);
        Product product = insertProduct("BadTransProduct", 10, new BigDecimal("10.00"));
        addToCart(user, product, 1);

        MvcResult createResult = mockMvc.perform(post("/api/orders")
                .with(httpBasic(USER_EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"shippingAddress\":\"Addr\"}"))
                .andExpect(status().isCreated())
                .andReturn();

        long orderId = extractOrderId(createResult.getResponse().getContentAsString());

        // Try PENDING → SHIPPED (skipping CONFIRMED)
        mockMvc.perform(put("/api/admin/orders/" + orderId + "/status")
                .with(httpBasic(ADMIN_EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"status\":\"SHIPPED\"}"))
                .andExpect(status().isBadRequest());
    }

    // ──────────────────────────────────────────────────────────────────────
    // PUT /api/orders/{id}/cancel — cancel order
    // ──────────────────────────────────────────────────────────────────────

    @Test
    public void cancelPendingOrderRestoresStock() throws Exception {
        Member member = insertMember(USER_EMAIL, Member.Role.USER);
        Product product = insertProduct("CancelProduct", 10, new BigDecimal("10.00"));
        addToCart(member, product, 3);

        MvcResult createResult = mockMvc.perform(post("/api/orders")
                .with(httpBasic(USER_EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"shippingAddress\":\"Addr\"}"))
                .andExpect(status().isCreated())
                .andReturn();

        // Stock should be 7 after order
        assertEquals(7, productMapper.selectById(product.getId()).getStockQuantity().intValue());

        long orderId = extractOrderId(createResult.getResponse().getContentAsString());

        mockMvc.perform(put("/api/orders/" + orderId + "/cancel")
                .with(httpBasic(USER_EMAIL, PASSWORD)))
                .andExpect(status().isNoContent());

        // Stock should be restored to 10
        assertEquals(10, productMapper.selectById(product.getId()).getStockQuantity().intValue());

        // Order status should be CANCELLED
        Order cancelled = orderMapper.selectById(orderId);
        assertEquals(Order.Status.CANCELLED, cancelled.getStatus());
    }

    @Test
    public void cancelNonPendingOrder400() throws Exception {
        Member user = insertMember(USER_EMAIL, Member.Role.USER);
        insertMember(ADMIN_EMAIL, Member.Role.ADMIN);
        Product product = insertProduct("NonPendProduct", 10, new BigDecimal("10.00"));
        addToCart(user, product, 1);

        MvcResult createResult = mockMvc.perform(post("/api/orders")
                .with(httpBasic(USER_EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"shippingAddress\":\"Addr\"}"))
                .andExpect(status().isCreated())
                .andReturn();

        long orderId = extractOrderId(createResult.getResponse().getContentAsString());

        // Advance to CONFIRMED
        mockMvc.perform(put("/api/admin/orders/" + orderId + "/status")
                .with(httpBasic(ADMIN_EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"status\":\"CONFIRMED\"}"))
                .andExpect(status().isOk());

        // Try to cancel CONFIRMED order — should fail
        mockMvc.perform(put("/api/orders/" + orderId + "/cancel")
                .with(httpBasic(USER_EMAIL, PASSWORD)))
                .andExpect(status().isBadRequest());
    }

    // ──────────────────────────────────────────────────────────────────────
    // GET /api/admin/orders — admin list all orders
    // ──────────────────────────────────────────────────────────────────────

    @Test
    public void adminListAllOrders() throws Exception {
        Member user = insertMember(USER_EMAIL, Member.Role.USER);
        insertMember(ADMIN_EMAIL, Member.Role.ADMIN);
        Product product = insertProduct("AdminListProduct", 100, new BigDecimal("10.00"));

        addToCart(user, product, 1);
        mockMvc.perform(post("/api/orders")
                .with(httpBasic(USER_EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"shippingAddress\":\"Addr\"}"))
                .andExpect(status().isCreated());

        MvcResult result = mockMvc.perform(get("/api/admin/orders")
                .with(httpBasic(ADMIN_EMAIL, PASSWORD)))
                .andExpect(status().isOk())
                .andReturn();

        String body = result.getResponse().getContentAsString();
        assertTrue(body.contains("\"totalElements\":1"));
    }

    // ──────────────────────────────────────────────────────────────────────
    // Auth checks
    // ──────────────────────────────────────────────────────────────────────

    @Test
    public void unauthenticatedAccess401() throws Exception {
        mockMvc.perform(get("/api/orders"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    public void userCannotAccessAdminStatusEndpoint() throws Exception {
        Member user = insertMember(USER_EMAIL, Member.Role.USER);
        Product product = insertProduct("AdminOnlyProduct", 10, new BigDecimal("10.00"));
        addToCart(user, product, 1);

        MvcResult createResult = mockMvc.perform(post("/api/orders")
                .with(httpBasic(USER_EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"shippingAddress\":\"Addr\"}"))
                .andExpect(status().isCreated())
                .andReturn();

        long orderId = extractOrderId(createResult.getResponse().getContentAsString());

        mockMvc.perform(put("/api/admin/orders/" + orderId + "/status")
                .with(httpBasic(USER_EMAIL, PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"status\":\"CONFIRMED\"}"))
                .andExpect(status().isForbidden());
    }

    // ──────────────────────────────────────────────────────────────────────
    // Helper
    // ──────────────────────────────────────────────────────────────────────

    private long extractOrderId(String body) {
        // Finds the first "id": <number> in the response
        int idIdx = body.indexOf("\"id\":");
        if (idIdx == -1) return -1;
        int start = idIdx + 5;
        int end = start;
        while (end < body.length() && Character.isDigit(body.charAt(end))) {
            end++;
        }
        return Long.parseLong(body.substring(start, end));
    }
}
