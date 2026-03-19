package com.example.shop.mapper;

import com.example.shop.entity.Product;
import com.example.shop.entity.ProductStatus;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
@ActiveProfiles("test")
@Transactional
class ProductMapperTest {

    @Autowired
    ProductMapper productMapper;

    private Product buildProduct(String name, String category, BigDecimal price, int stock) {
        Product p = new Product();
        p.setName(name);
        p.setDescription("Description for " + name);
        p.setPrice(price);
        p.setStockQuantity(stock);
        p.setCategory(category);
        p.setImageUrl("https://example.com/img/" + name + ".jpg");
        p.setStatus(ProductStatus.ACTIVE);
        return p;
    }

    @Test
    void insertAndFindById() {
        Product p = buildProduct("Widget A", "Electronics", new BigDecimal("29.99"), 100);
        productMapper.insert(p);

        assertThat(p.getId()).isNotNull();

        Product found = productMapper.findById(p.getId());
        assertThat(found).isNotNull();
        assertThat(found.getName()).isEqualTo("Widget A");
        assertThat(found.getCategory()).isEqualTo("Electronics");
        assertThat(found.getPrice()).isEqualByComparingTo(new BigDecimal("29.99"));
        assertThat(found.getStockQuantity()).isEqualTo(100);
        assertThat(found.getStatus()).isEqualTo(ProductStatus.ACTIVE);
        assertThat(found.getCreatedAt()).isNotNull();
        assertThat(found.getUpdatedAt()).isNotNull();
    }

    @Test
    void findAllActive_excludesInactive() {
        productMapper.insert(buildProduct("Active Product", "Books", new BigDecimal("9.99"), 10));
        Product inactive = buildProduct("Inactive Product", "Books", new BigDecimal("5.00"), 5);
        inactive.setStatus(ProductStatus.INACTIVE);
        productMapper.insert(inactive);

        List<Product> active = productMapper.findAllActive(0, 100);
        long activeCount = active.stream()
                .filter(pr -> pr.getStatus() == ProductStatus.ACTIVE).count();
        long inactiveCount = active.stream()
                .filter(pr -> pr.getStatus() == ProductStatus.INACTIVE).count();

        assertThat(activeCount).isGreaterThanOrEqualTo(1);
        assertThat(inactiveCount).isZero();
    }

    @Test
    void softDelete_changesStatusToInactive() {
        Product p = buildProduct("To Delete", "Clothing", new BigDecimal("49.99"), 20);
        productMapper.insert(p);
        assertThat(productMapper.findById(p.getId()).getStatus()).isEqualTo(ProductStatus.ACTIVE);

        productMapper.softDelete(p.getId());

        Product found = productMapper.findById(p.getId());
        assertThat(found.getStatus()).isEqualTo(ProductStatus.INACTIVE);
    }

    @Test
    void search_withKeywordCategoryPriceFilters() {
        productMapper.insert(buildProduct("Java Book", "Books", new BigDecimal("35.00"), 50));
        productMapper.insert(buildProduct("Python Book", "Books", new BigDecimal("25.00"), 30));
        productMapper.insert(buildProduct("Laptop Stand", "Electronics", new BigDecimal("55.00"), 15));

        // keyword search
        List<Product> byKeyword = productMapper.search("Java", null, null, null, "name", "asc", 0, 10);
        assertThat(byKeyword).anyMatch(pr -> pr.getName().contains("Java"));
        assertThat(byKeyword).noneMatch(pr -> pr.getName().equals("Laptop Stand"));

        // category filter
        List<Product> byCategory = productMapper.search(null, "Electronics", null, null, "name", "asc", 0, 10);
        assertThat(byCategory).allMatch(pr -> pr.getCategory().equals("Electronics"));

        // price range
        List<Product> byPrice = productMapper.search(null, null, new BigDecimal("30.00"), new BigDecimal("60.00"), "price", "asc", 0, 10);
        assertThat(byPrice).allMatch(pr -> pr.getPrice().compareTo(new BigDecimal("30.00")) >= 0
                && pr.getPrice().compareTo(new BigDecimal("60.00")) <= 0);

        // combined: category + max price
        List<Product> combined = productMapper.search(null, "Books", null, new BigDecimal("30.00"), "price", "asc", 0, 10);
        assertThat(combined).allMatch(pr -> pr.getCategory().equals("Books")
                && pr.getPrice().compareTo(new BigDecimal("30.00")) <= 0);
    }

    @Test
    void decreaseStock_reducesStockQuantity() {
        Product p = buildProduct("Stock Item", "Electronics", new BigDecimal("99.99"), 50);
        productMapper.insert(p);

        int updated = productMapper.decreaseStock(p.getId(), 10);
        assertThat(updated).isEqualTo(1);

        Product found = productMapper.findById(p.getId());
        assertThat(found.getStockQuantity()).isEqualTo(40);
    }

    @Test
    void decreaseStock_failsWhenInsufficientStock() {
        Product p = buildProduct("Low Stock Item", "Electronics", new BigDecimal("9.99"), 5);
        productMapper.insert(p);

        int updated = productMapper.decreaseStock(p.getId(), 10);
        assertThat(updated).isZero(); // WHERE stock_quantity >= quantity fails

        Product found = productMapper.findById(p.getId());
        assertThat(found.getStockQuantity()).isEqualTo(5); // unchanged
    }

    @Test
    void pagination_returnsCorrectSlices() {
        for (int i = 1; i <= 5; i++) {
            productMapper.insert(buildProduct("Product " + i, "Test", new BigDecimal(i * 10), i * 5));
        }

        List<Product> page0 = productMapper.findAllActive(0, 2);
        List<Product> page1 = productMapper.findAllActive(2, 2);
        List<Product> page2 = productMapper.findAllActive(4, 2);

        assertThat(page0).hasSize(2);
        assertThat(page1).hasSize(2);
        assertThat(page2).hasSizeGreaterThanOrEqualTo(1);

        // no overlap between pages
        List<Long> ids0 = page0.stream().map(Product::getId).toList();
        List<Long> ids1 = page1.stream().map(Product::getId).toList();
        assertThat(ids0).doesNotContainAnyElementsOf(ids1);

        int total = productMapper.countAllActive();
        assertThat(total).isGreaterThanOrEqualTo(5);
    }
}
