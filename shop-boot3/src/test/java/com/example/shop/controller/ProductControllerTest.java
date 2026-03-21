package com.example.shop.controller;

import com.example.shop.entity.Member;
import com.example.shop.entity.MemberRole;
import com.example.shop.entity.Product;
import com.example.shop.entity.ProductStatus;
import com.example.shop.mapper.MemberMapper;
import com.example.shop.mapper.ProductMapper;
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
class ProductControllerTest {

    @Autowired
    private MockMvc mvc;

    @Autowired
    private ProductMapper productMapper;

    @Autowired
    private MemberMapper memberMapper;

    @Autowired
    private PasswordEncoder passwordEncoder;

    private static final String ADMIN_EMAIL = "admin@shop.com";
    private static final String ADMIN_PASSWORD = "admin1234";
    private static final String USER_EMAIL = "user@prod-test.com";
    private static final String USER_PASSWORD = "password123";

    @BeforeEach
    void setUp() {
        if (memberMapper.findByEmail(USER_EMAIL) == null) {
            Member user = new Member();
            user.setEmail(USER_EMAIL);
            user.setPassword(passwordEncoder.encode(USER_PASSWORD));
            user.setName("Product Test User");
            user.setPhone("01011112222");
            user.setAddress("Seoul");
            user.setRole(MemberRole.USER);
            user.setActive(true);
            memberMapper.insert(user);
        }
    }

    // ── List ──────────────────────────────────────────────────────────────────

    @Test
    void listProducts_returns200WithPageStructure() throws Exception {
        insertProduct("Gadget A", "Electronics", new BigDecimal("99.99"), 10);
        insertProduct("Gadget B", "Electronics", new BigDecimal("49.99"), 5);

        mvc.perform(get("/api/products").param("page", "0").param("size", "10"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content").isArray())
                .andExpect(jsonPath("$.currentPage").value(0))
                .andExpect(jsonPath("$.pageSize").value(10))
                .andExpect(jsonPath("$.totalElements").isNumber())
                .andExpect(jsonPath("$.totalPages").isNumber());
    }

    @Test
    void listProducts_noAuth_returns200() throws Exception {
        mvc.perform(get("/api/products"))
                .andExpect(status().isOk());
    }

    // ── Get by ID ─────────────────────────────────────────────────────────────

    @Test
    void getProduct_returns200() throws Exception {
        Product p = insertProduct("Widget", "Tools", new BigDecimal("19.99"), 20);

        mvc.perform(get("/api/products/{id}", p.getId()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(p.getId()))
                .andExpect(jsonPath("$.name").value("Widget"))
                .andExpect(jsonPath("$.category").value("Tools"))
                .andExpect(jsonPath("$.price").value(19.99))
                .andExpect(jsonPath("$.stockQuantity").value(20))
                .andExpect(jsonPath("$.status").value("ACTIVE"));
    }

    @Test
    void getProduct_notFound_returns404() throws Exception {
        mvc.perform(get("/api/products/99999"))
                .andExpect(status().isNotFound());
    }

    @Test
    void getProduct_inactiveProduct_returns200() throws Exception {
        Product p = insertProduct("Hidden", "Books", new BigDecimal("5.00"), 1);
        productMapper.softDelete(p.getId());

        mvc.perform(get("/api/products/{id}", p.getId()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("INACTIVE"));
    }

    // ── Admin Create ──────────────────────────────────────────────────────────

    @Test
    void adminCreate_returns201() throws Exception {
        mvc.perform(post("/api/products")
                .header("Authorization", basicAuth(ADMIN_EMAIL, ADMIN_PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {
                          "name": "New Product",
                          "description": "A great product",
                          "price": 29.99,
                          "stockQuantity": 50,
                          "category": "Books",
                          "imageUrl": "https://example.com/img.jpg"
                        }
                        """))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.name").value("New Product"))
                .andExpect(jsonPath("$.category").value("Books"))
                .andExpect(jsonPath("$.status").value("ACTIVE"))
                .andExpect(jsonPath("$.id").isNumber());
    }

    @Test
    void adminCreate_validationErrors_returns400() throws Exception {
        mvc.perform(post("/api/products")
                .header("Authorization", basicAuth(ADMIN_EMAIL, ADMIN_PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {
                          "name": "",
                          "price": -1,
                          "stockQuantity": -5,
                          "category": ""
                        }
                        """))
                .andExpect(status().isBadRequest());
    }

    // ── Admin Update ──────────────────────────────────────────────────────────

    @Test
    void adminUpdate_returns200() throws Exception {
        Product p = insertProduct("Old Name", "Clothing", new BigDecimal("30.00"), 10);

        mvc.perform(put("/api/products/{id}", p.getId())
                .header("Authorization", basicAuth(ADMIN_EMAIL, ADMIN_PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {
                          "name": "New Name",
                          "description": "Updated desc",
                          "price": 35.00,
                          "stockQuantity": 15,
                          "category": "Clothing",
                          "imageUrl": "https://example.com/new.jpg"
                        }
                        """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name").value("New Name"))
                .andExpect(jsonPath("$.price").value(35.0))
                .andExpect(jsonPath("$.stockQuantity").value(15));
    }

    @Test
    void adminUpdate_notFound_returns404() throws Exception {
        mvc.perform(put("/api/products/99999")
                .header("Authorization", basicAuth(ADMIN_EMAIL, ADMIN_PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {
                          "name": "X",
                          "price": 1.00,
                          "stockQuantity": 1,
                          "category": "X"
                        }
                        """))
                .andExpect(status().isNotFound());
    }

    // ── Admin Soft Delete ─────────────────────────────────────────────────────

    @Test
    void adminSoftDelete_returns204AndExcludedFromListing() throws Exception {
        Product p = insertProduct("To Delete", "Electronics", new BigDecimal("9.99"), 5);

        mvc.perform(delete("/api/products/{id}", p.getId())
                .header("Authorization", basicAuth(ADMIN_EMAIL, ADMIN_PASSWORD)))
                .andExpect(status().isNoContent());

        // Verify excluded from active listing
        mvc.perform(get("/api/products").param("size", "100"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content[?(@.id == " + p.getId() + ")]").isEmpty());

        // But still retrievable by ID
        mvc.perform(get("/api/products/{id}", p.getId()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("INACTIVE"));
    }

    @Test
    void adminSoftDelete_notFound_returns404() throws Exception {
        mvc.perform(delete("/api/products/99999")
                .header("Authorization", basicAuth(ADMIN_EMAIL, ADMIN_PASSWORD)))
                .andExpect(status().isNotFound());
    }

    // ── Search ────────────────────────────────────────────────────────────────

    @Test
    void searchByKeyword_returns200WithMatchingResults() throws Exception {
        insertProduct("Java Programming", "Books", new BigDecimal("39.99"), 30);
        insertProduct("Python Basics", "Books", new BigDecimal("29.99"), 20);
        insertProduct("Coffee Maker", "Kitchen", new BigDecimal("59.99"), 10);

        mvc.perform(get("/api/products/search").param("keyword", "Java"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content").isArray())
                .andExpect(jsonPath("$.content[?(@.name =~ /.*Java.*/)]").isNotEmpty())
                .andExpect(jsonPath("$.content[?(@.name == 'Coffee Maker')]").isEmpty());
    }

    @Test
    void searchByCategory_returns200() throws Exception {
        insertProduct("Book One", "Books", new BigDecimal("15.00"), 10);
        insertProduct("Book Two", "Books", new BigDecimal("20.00"), 5);
        insertProduct("Laptop", "Electronics", new BigDecimal("999.00"), 3);

        mvc.perform(get("/api/products/search").param("category", "Books"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content").isArray())
                .andExpect(jsonPath("$.content[?(@.category == 'Books')]").isNotEmpty())
                .andExpect(jsonPath("$.content[?(@.category == 'Electronics')]").isEmpty());
    }

    @Test
    void searchByPriceRange_returns200() throws Exception {
        insertProduct("Cheap Item", "Misc", new BigDecimal("5.00"), 100);
        insertProduct("Mid Item", "Misc", new BigDecimal("50.00"), 50);
        insertProduct("Expensive Item", "Misc", new BigDecimal("500.00"), 10);

        mvc.perform(get("/api/products/search")
                .param("minPrice", "10")
                .param("maxPrice", "100"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content[?(@.name == 'Mid Item')]").isNotEmpty())
                .andExpect(jsonPath("$.content[?(@.name == 'Cheap Item')]").isEmpty())
                .andExpect(jsonPath("$.content[?(@.name == 'Expensive Item')]").isEmpty());
    }

    @Test
    void searchCombinedFilters_returns200() throws Exception {
        insertProduct("Spring Boot Guide", "Books", new BigDecimal("45.00"), 20);
        insertProduct("Spring Framework", "Books", new BigDecimal("55.00"), 15);
        insertProduct("Spring Boots", "Clothing", new BigDecimal("40.00"), 30);

        mvc.perform(get("/api/products/search")
                .param("keyword", "Spring")
                .param("category", "Books")
                .param("maxPrice", "50"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content[?(@.name == 'Spring Boot Guide')]").isNotEmpty())
                .andExpect(jsonPath("$.content[?(@.name == 'Spring Framework')]").isEmpty())
                .andExpect(jsonPath("$.content[?(@.name == 'Spring Boots')]").isEmpty());
    }

    @Test
    void searchNoAuth_returns200() throws Exception {
        mvc.perform(get("/api/products/search"))
                .andExpect(status().isOk());
    }

    // ── Authorization ─────────────────────────────────────────────────────────

    @Test
    void userCannotCreate_returns403() throws Exception {
        mvc.perform(post("/api/products")
                .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {
                          "name": "Hacked Product",
                          "price": 0.01,
                          "stockQuantity": 1,
                          "category": "Misc"
                        }
                        """))
                .andExpect(status().isForbidden());
    }

    @Test
    void userCannotUpdate_returns403() throws Exception {
        Product p = insertProduct("Protected", "Misc", new BigDecimal("10.00"), 5);

        mvc.perform(put("/api/products/{id}", p.getId())
                .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD))
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {
                          "name": "Hacked",
                          "price": 1.00,
                          "stockQuantity": 1,
                          "category": "Misc"
                        }
                        """))
                .andExpect(status().isForbidden());
    }

    @Test
    void userCannotDelete_returns403() throws Exception {
        Product p = insertProduct("Protected", "Misc", new BigDecimal("10.00"), 5);

        mvc.perform(delete("/api/products/{id}", p.getId())
                .header("Authorization", basicAuth(USER_EMAIL, USER_PASSWORD)))
                .andExpect(status().isForbidden());
    }

    // ── Pagination Cap ────────────────────────────────────────────────────────

    @Test
    void paginationSizeCappedAt100() throws Exception {
        mvc.perform(get("/api/products").param("size", "200"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.pageSize").value(lessThanOrEqualTo(100)));
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
