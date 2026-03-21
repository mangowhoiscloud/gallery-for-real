package com.example.shop.mapper;

import com.example.shop.config.TestConfig;
import com.example.shop.domain.Product;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.Assert.*;

@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration(classes = TestConfig.class)
@Transactional
public class ProductMapperTest {

    @Autowired
    private ProductMapper productMapper;

    private Product buildProduct(String name, String category, BigDecimal price) {
        Product p = new Product();
        p.setName(name);
        p.setDescription("Description for " + name);
        p.setPrice(price);
        p.setStockQuantity(100);
        p.setCategory(category);
        p.setImageUrl("http://example.com/img/" + name + ".jpg");
        p.setStatus(Product.Status.ACTIVE);
        return p;
    }

    @Test
    public void insertAndSelectById() {
        Product p = buildProduct("Test Product", "Electronics", new BigDecimal("99.99"));
        productMapper.insert(p);

        assertNotNull("Generated key must be set", p.getId());

        Product found = productMapper.selectById(p.getId());
        assertNotNull(found);
        assertEquals("Test Product", found.getName());
        assertEquals("Electronics", found.getCategory());
        assertEquals(0, new BigDecimal("99.99").compareTo(found.getPrice()));
        assertEquals(Integer.valueOf(100), found.getStockQuantity());
        assertEquals(Product.Status.ACTIVE, found.getStatus());
        assertNotNull(found.getCreatedAt());
    }

    @Test
    public void selectActiveByIdReturnsActiveProduct() {
        Product p = buildProduct("Active Product", "Books", new BigDecimal("19.99"));
        productMapper.insert(p);

        Product found = productMapper.selectActiveById(p.getId());
        assertNotNull(found);
        assertEquals(p.getId(), found.getId());
    }

    @Test
    public void selectActiveByIdReturnsNullForInactiveProduct() {
        Product p = buildProduct("Inactive Product", "Books", new BigDecimal("19.99"));
        p.setStatus(Product.Status.INACTIVE);
        productMapper.insert(p);

        Product found = productMapper.selectActiveById(p.getId());
        assertNull(found);
    }

    @Test
    public void searchByKeyword() {
        productMapper.insert(buildProduct("Laptop Pro", "Electronics", new BigDecimal("1200.00")));
        productMapper.insert(buildProduct("Phone Ultra", "Electronics", new BigDecimal("800.00")));
        productMapper.insert(buildProduct("Coffee Mug", "Kitchen", new BigDecimal("15.00")));

        Map<String, Object> params = new HashMap<String, Object>();
        params.put("keyword", "%Laptop%");
        params.put("limit", 10);
        params.put("offset", 0);

        List<Product> results = productMapper.search(params);
        assertEquals(1, results.size());
        assertEquals("Laptop Pro", results.get(0).getName());
    }

    @Test
    public void searchByCategory() {
        productMapper.insert(buildProduct("Laptop", "Electronics", new BigDecimal("1000.00")));
        productMapper.insert(buildProduct("Phone", "Electronics", new BigDecimal("500.00")));
        productMapper.insert(buildProduct("Book", "Books", new BigDecimal("20.00")));

        Map<String, Object> params = new HashMap<String, Object>();
        params.put("category", "Electronics");
        params.put("limit", 10);
        params.put("offset", 0);

        List<Product> results = productMapper.search(params);
        assertEquals(2, results.size());
        for (Product p : results) {
            assertEquals("Electronics", p.getCategory());
        }
    }

    @Test
    public void searchByPriceRange() {
        productMapper.insert(buildProduct("Cheap Item", "General", new BigDecimal("5.00")));
        productMapper.insert(buildProduct("Mid Item", "General", new BigDecimal("50.00")));
        productMapper.insert(buildProduct("Expensive Item", "General", new BigDecimal("500.00")));

        Map<String, Object> params = new HashMap<String, Object>();
        params.put("minPrice", new BigDecimal("10.00"));
        params.put("maxPrice", new BigDecimal("100.00"));
        params.put("limit", 10);
        params.put("offset", 0);

        List<Product> results = productMapper.search(params);
        assertEquals(1, results.size());
        assertEquals("Mid Item", results.get(0).getName());
    }

    @Test
    public void searchWithSortPriceAsc() {
        productMapper.insert(buildProduct("Expensive", "General", new BigDecimal("300.00")));
        productMapper.insert(buildProduct("Cheap", "General", new BigDecimal("10.00")));
        productMapper.insert(buildProduct("Mid", "General", new BigDecimal("150.00")));

        Map<String, Object> params = new HashMap<String, Object>();
        params.put("sort", "price_asc");
        params.put("limit", 10);
        params.put("offset", 0);

        List<Product> results = productMapper.search(params);
        assertTrue(results.size() >= 3);
        // Verify ascending order among our inserted items
        BigDecimal prev = BigDecimal.ZERO;
        for (Product p : results) {
            assertTrue(p.getPrice().compareTo(prev) >= 0);
            prev = p.getPrice();
        }
    }

    @Test
    public void searchWithSortPriceDesc() {
        productMapper.insert(buildProduct("ItemA", "General", new BigDecimal("100.00")));
        productMapper.insert(buildProduct("ItemB", "General", new BigDecimal("200.00")));
        productMapper.insert(buildProduct("ItemC", "General", new BigDecimal("50.00")));

        Map<String, Object> params = new HashMap<String, Object>();
        params.put("sort", "price_desc");
        params.put("limit", 10);
        params.put("offset", 0);

        List<Product> results = productMapper.search(params);
        assertTrue(results.size() >= 3);
        // Verify descending order
        BigDecimal prev = new BigDecimal("999999");
        for (Product p : results) {
            assertTrue(p.getPrice().compareTo(prev) <= 0);
            prev = p.getPrice();
        }
    }

    @Test
    public void updateStockIncrement() {
        Product p = buildProduct("Stock Item", "General", new BigDecimal("10.00"));
        p.setStockQuantity(50);
        productMapper.insert(p);

        Map<String, Object> params = new HashMap<String, Object>();
        params.put("id", p.getId());
        params.put("delta", 25);
        productMapper.updateStock(params);

        Product updated = productMapper.selectById(p.getId());
        assertEquals(Integer.valueOf(75), updated.getStockQuantity());
    }

    @Test
    public void updateStockDecrement() {
        Product p = buildProduct("Stock Decrement", "General", new BigDecimal("10.00"));
        p.setStockQuantity(50);
        productMapper.insert(p);

        Map<String, Object> params = new HashMap<String, Object>();
        params.put("id", p.getId());
        params.put("delta", -10);
        productMapper.updateStock(params);

        Product updated = productMapper.selectById(p.getId());
        assertEquals(Integer.valueOf(40), updated.getStockQuantity());
    }

    @Test
    public void selectDistinctCategoriesReturnsOnlyActive() {
        productMapper.insert(buildProduct("Active Electronics", "Electronics", new BigDecimal("100.00")));
        productMapper.insert(buildProduct("Active Books", "Books", new BigDecimal("20.00")));

        Product inactive = buildProduct("Inactive Clothing", "Clothing", new BigDecimal("30.00"));
        inactive.setStatus(Product.Status.INACTIVE);
        productMapper.insert(inactive);

        List<String> categories = productMapper.selectDistinctCategories();
        assertTrue(categories.contains("Electronics"));
        assertTrue(categories.contains("Books"));
        assertFalse("Inactive product category must not appear", categories.contains("Clothing"));
    }

    @Test
    public void softDeleteExcludedFromSearch() {
        productMapper.insert(buildProduct("Visible Product", "General", new BigDecimal("10.00")));

        Product deleted = buildProduct("Hidden Product", "General", new BigDecimal("10.00"));
        productMapper.insert(deleted);
        deleted.setStatus(Product.Status.INACTIVE);
        productMapper.update(deleted);

        Map<String, Object> params = new HashMap<String, Object>();
        params.put("category", "General");
        params.put("limit", 10);
        params.put("offset", 0);

        List<Product> results = productMapper.search(params);
        for (Product p : results) {
            assertNotEquals("INACTIVE product must not appear in search", "Hidden Product", p.getName());
        }
        boolean visibleFound = false;
        for (Product p : results) {
            if ("Visible Product".equals(p.getName())) {
                visibleFound = true;
                break;
            }
        }
        assertTrue("Active product must appear in search", visibleFound);
    }

    @Test
    public void countBySearchMatchesSearchResults() {
        productMapper.insert(buildProduct("Count A", "Counted", new BigDecimal("10.00")));
        productMapper.insert(buildProduct("Count B", "Counted", new BigDecimal("20.00")));
        productMapper.insert(buildProduct("Count C", "Counted", new BigDecimal("30.00")));

        Map<String, Object> params = new HashMap<String, Object>();
        params.put("category", "Counted");
        params.put("limit", 2);
        params.put("offset", 0);

        List<Product> page = productMapper.search(params);
        int total = productMapper.countBySearch(params);

        assertEquals(2, page.size());
        assertEquals(3, total);
    }
}
