package com.example.shop.controller;

import com.example.shop.config.SecurityConfig;
import com.example.shop.config.TestConfig;
import com.example.shop.domain.Member;
import com.example.shop.domain.Product;
import com.example.shop.dto.ProductResponse;
import com.example.shop.mapper.MemberMapper;
import com.example.shop.mapper.ProductMapper;
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
import static org.springframework.security.test.web.servlet.setup.SecurityMockMvcConfigurers.springSecurity;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration(classes = ProductControllerTest.TestWebConfig.class)
@WebAppConfiguration
@Transactional
public class ProductControllerTest {

    @Configuration
    @EnableWebMvc
    @ComponentScan({"com.example.shop.security", "com.example.shop.service", "com.example.shop.controller"})
    @Import({TestConfig.class, SecurityConfig.class})
    static class TestWebConfig {}

    @Autowired private WebApplicationContext wac;
    @Autowired private ProductMapper productMapper;
    @Autowired private MemberMapper memberMapper;
    @Autowired private PasswordEncoder passwordEncoder;

    private MockMvc mockMvc;
    private ObjectMapper objectMapper;

    @Before
    public void setUp() {
        objectMapper = new ObjectMapper();
        mockMvc = MockMvcBuilders.webAppContextSetup(wac)
                .apply(springSecurity())
                .build();
    }

    private Product insertProduct(String name, String category, BigDecimal price, int stock) {
        Product p = new Product();
        p.setName(name);
        p.setDescription("Description for " + name);
        p.setPrice(price);
        p.setStockQuantity(stock);
        p.setCategory(category);
        p.setStatus(Product.Status.ACTIVE);
        productMapper.insert(p);
        return p;
    }

    // ──────────────────────────────────────────────────────────────────────
    // GET /api/products — public, paginated list
    // ──────────────────────────────────────────────────────────────────────

    @Test
    public void listProductsPaginated() throws Exception {
        insertProduct("Laptop", "Electronics", new BigDecimal("999.99"), 10);
        insertProduct("Book", "Books", new BigDecimal("19.99"), 100);

        MvcResult result = mockMvc.perform(get("/api/products")
                .param("page", "0")
                .param("size", "10"))
                .andExpect(status().isOk())
                .andReturn();

        String body = result.getResponse().getContentAsString();
        assertTrue(body.contains("Laptop"));
        assertTrue(body.contains("Book"));
        assertTrue(body.contains("totalElements"));
        assertTrue(body.contains("content"));
    }

    @Test
    public void listProductsExcludesInactive() throws Exception {
        insertProduct("ActiveProduct", "Electronics", new BigDecimal("100.00"), 5);
        Product inactive = insertProduct("InactiveProduct", "Electronics", new BigDecimal("200.00"), 5);
        inactive.setStatus(Product.Status.INACTIVE);
        productMapper.update(inactive);

        MvcResult result = mockMvc.perform(get("/api/products"))
                .andExpect(status().isOk())
                .andReturn();

        String body = result.getResponse().getContentAsString();
        assertTrue(body.contains("ActiveProduct"));
        assertFalse(body.contains("InactiveProduct"));
    }

    // ──────────────────────────────────────────────────────────────────────
    // GET /api/products/{id}
    // ──────────────────────────────────────────────────────────────────────

    @Test
    public void getProductById200() throws Exception {
        Product product = insertProduct("Widget", "Tools", new BigDecimal("49.99"), 20);

        MvcResult result = mockMvc.perform(get("/api/products/" + product.getId()))
                .andExpect(status().isOk())
                .andReturn();

        ProductResponse response = objectMapper.readValue(result.getResponse().getContentAsString(), ProductResponse.class);
        assertEquals(product.getId(), response.getId());
        assertEquals("Widget", response.getName());
        assertEquals("Tools", response.getCategory());
        assertEquals(0, new BigDecimal("49.99").compareTo(response.getPrice()));
    }

    @Test
    public void getProductByIdNotFound404() throws Exception {
        mockMvc.perform(get("/api/products/999999"))
                .andExpect(status().isNotFound());
    }

    // ──────────────────────────────────────────────────────────────────────
    // POST /api/products — ADMIN only
    // ──────────────────────────────────────────────────────────────────────

    @Test
    @WithMockUser(roles = "ADMIN")
    public void createProductAsAdmin201() throws Exception {
        String json = "{\"name\":\"New Phone\",\"price\":599.99,\"stockQuantity\":50," +
                "\"category\":\"Electronics\",\"description\":\"A new phone\"}";

        MvcResult result = mockMvc.perform(post("/api/products")
                .contentType(MediaType.APPLICATION_JSON)
                .content(json))
                .andExpect(status().isCreated())
                .andReturn();

        ProductResponse response = objectMapper.readValue(result.getResponse().getContentAsString(), ProductResponse.class);
        assertNotNull(response.getId());
        assertEquals("New Phone", response.getName());
        assertEquals("ACTIVE", response.getStatus());
        assertEquals(50, (int) response.getStockQuantity());
    }

    @Test
    @WithMockUser(roles = "USER")
    public void createProductAsUser403() throws Exception {
        String json = "{\"name\":\"Unauthorized\",\"price\":9.99,\"stockQuantity\":10,\"category\":\"Misc\"}";

        mockMvc.perform(post("/api/products")
                .contentType(MediaType.APPLICATION_JSON)
                .content(json))
                .andExpect(status().isForbidden());
    }

    @Test
    public void createProductUnauthenticated401() throws Exception {
        String json = "{\"name\":\"Anon\",\"price\":9.99,\"stockQuantity\":10,\"category\":\"Misc\"}";

        mockMvc.perform(post("/api/products")
                .contentType(MediaType.APPLICATION_JSON)
                .content(json))
                .andExpect(status().isUnauthorized());
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    public void createProductValidationError400() throws Exception {
        // missing required fields: price, stockQuantity, category
        String json = "{\"name\":\"Only Name\"}";

        mockMvc.perform(post("/api/products")
                .contentType(MediaType.APPLICATION_JSON)
                .content(json))
                .andExpect(status().isBadRequest());
    }

    // ──────────────────────────────────────────────────────────────────────
    // PUT /api/products/{id}
    // ──────────────────────────────────────────────────────────────────────

    @Test
    @WithMockUser(roles = "ADMIN")
    public void updateProduct200() throws Exception {
        Product product = insertProduct("Old Name", "Old Category", new BigDecimal("10.00"), 5);

        String json = "{\"name\":\"New Name\",\"price\":20.00,\"category\":\"New Category\"}";

        MvcResult result = mockMvc.perform(put("/api/products/" + product.getId())
                .contentType(MediaType.APPLICATION_JSON)
                .content(json))
                .andExpect(status().isOk())
                .andReturn();

        ProductResponse response = objectMapper.readValue(result.getResponse().getContentAsString(), ProductResponse.class);
        assertEquals("New Name", response.getName());
        assertEquals("New Category", response.getCategory());
        assertEquals(0, new BigDecimal("20.00").compareTo(response.getPrice()));
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    public void updateProductNotFound404() throws Exception {
        String json = "{\"name\":\"Ghost\"}";

        mockMvc.perform(put("/api/products/999999")
                .contentType(MediaType.APPLICATION_JSON)
                .content(json))
                .andExpect(status().isNotFound());
    }

    // ──────────────────────────────────────────────────────────────────────
    // DELETE /api/products/{id} — soft delete (INACTIVE)
    // ──────────────────────────────────────────────────────────────────────

    @Test
    @WithMockUser(roles = "ADMIN")
    public void deleteProductSoftDelete204() throws Exception {
        Product product = insertProduct("ToDelete", "Electronics", new BigDecimal("5.00"), 1);

        mockMvc.perform(delete("/api/products/" + product.getId()))
                .andExpect(status().isNoContent());

        // Verify product is INACTIVE (not found via search, but selectById still returns it)
        Product deleted = productMapper.selectById(product.getId());
        assertNotNull(deleted);
        assertEquals(Product.Status.INACTIVE, deleted.getStatus());

        // Verify it's excluded from public search
        Product notFound = productMapper.selectActiveById(product.getId());
        assertNull(notFound);
    }

    // ──────────────────────────────────────────────────────────────────────
    // GET /api/products?keyword=... (search)
    // ──────────────────────────────────────────────────────────────────────

    @Test
    public void searchByKeyword() throws Exception {
        insertProduct("Gaming Laptop Pro", "Electronics", new BigDecimal("1200.00"), 5);
        insertProduct("Office Chair", "Furniture", new BigDecimal("300.00"), 10);

        MvcResult result = mockMvc.perform(get("/api/products")
                .param("keyword", "Laptop"))
                .andExpect(status().isOk())
                .andReturn();

        String body = result.getResponse().getContentAsString();
        assertTrue(body.contains("Gaming Laptop Pro"));
        assertFalse(body.contains("Office Chair"));
    }

    @Test
    public void searchByCategory() throws Exception {
        insertProduct("Keyboard", "Electronics", new BigDecimal("80.00"), 30);
        insertProduct("Desk", "Furniture", new BigDecimal("250.00"), 8);

        MvcResult result = mockMvc.perform(get("/api/products")
                .param("category", "Electronics"))
                .andExpect(status().isOk())
                .andReturn();

        String body = result.getResponse().getContentAsString();
        assertTrue(body.contains("Keyboard"));
        assertFalse(body.contains("Desk"));
    }

    @Test
    public void searchByPriceRange() throws Exception {
        insertProduct("CheapItem", "Misc", new BigDecimal("5.00"), 100);
        insertProduct("ExpensiveItem", "Misc", new BigDecimal("500.00"), 1);

        MvcResult result = mockMvc.perform(get("/api/products")
                .param("minPrice", "100")
                .param("maxPrice", "1000"))
                .andExpect(status().isOk())
                .andReturn();

        String body = result.getResponse().getContentAsString();
        assertTrue(body.contains("ExpensiveItem"));
        assertFalse(body.contains("CheapItem"));
    }

    @Test
    public void searchWithSortPriceAsc() throws Exception {
        insertProduct("Mid", "Sort", new BigDecimal("50.00"), 5);
        insertProduct("High", "Sort", new BigDecimal("100.00"), 5);
        insertProduct("Low", "Sort", new BigDecimal("10.00"), 5);

        MvcResult result = mockMvc.perform(get("/api/products")
                .param("category", "Sort")
                .param("sortBy", "price")
                .param("sortDir", "asc"))
                .andExpect(status().isOk())
                .andReturn();

        String body = result.getResponse().getContentAsString();
        int idxLow = body.indexOf("\"Low\"");
        int idxMid = body.indexOf("\"Mid\"");
        int idxHigh = body.indexOf("\"High\"");
        assertTrue("Low should come before Mid", idxLow < idxMid);
        assertTrue("Mid should come before High", idxMid < idxHigh);
    }

    // ──────────────────────────────────────────────────────────────────────
    // GET /api/products/categories
    // ──────────────────────────────────────────────────────────────────────

    @Test
    public void getCategories() throws Exception {
        insertProduct("Phone", "Electronics", new BigDecimal("699.00"), 20);
        insertProduct("Tablet", "Electronics", new BigDecimal("499.00"), 15);
        insertProduct("Sofa", "Furniture", new BigDecimal("899.00"), 3);

        MvcResult result = mockMvc.perform(get("/api/products/categories"))
                .andExpect(status().isOk())
                .andReturn();

        String body = result.getResponse().getContentAsString();
        assertTrue(body.contains("Electronics"));
        assertTrue(body.contains("Furniture"));
    }

    @Test
    public void getCategoriesExcludesInactive() throws Exception {
        insertProduct("ActiveElectronics", "Electronics", new BigDecimal("100.00"), 5);
        Product inactive = insertProduct("InactiveOnly", "HiddenCategory", new BigDecimal("50.00"), 5);
        inactive.setStatus(Product.Status.INACTIVE);
        productMapper.update(inactive);

        MvcResult result = mockMvc.perform(get("/api/products/categories"))
                .andExpect(status().isOk())
                .andReturn();

        String body = result.getResponse().getContentAsString();
        assertTrue(body.contains("Electronics"));
        assertFalse(body.contains("HiddenCategory"));
    }
}
