package com.example.shop.mapper;

import com.example.shop.entity.Product;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.math.BigDecimal;
import java.util.List;

@Mapper
public interface ProductMapper {

    void insert(Product product);

    Product findById(Long id);

    List<Product> findAllActive(@Param("offset") int offset, @Param("limit") int limit);

    int countAllActive();

    void update(Product product);

    void softDelete(Long id);

    List<Product> search(
            @Param("keyword") String keyword,
            @Param("category") String category,
            @Param("minPrice") BigDecimal minPrice,
            @Param("maxPrice") BigDecimal maxPrice,
            @Param("sortBy") String sortBy,
            @Param("sortDir") String sortDir,
            @Param("offset") int offset,
            @Param("limit") int limit
    );

    int countSearch(
            @Param("keyword") String keyword,
            @Param("category") String category,
            @Param("minPrice") BigDecimal minPrice,
            @Param("maxPrice") BigDecimal maxPrice
    );

    int decreaseStock(@Param("id") Long id, @Param("quantity") int quantity);

    int increaseStock(@Param("id") Long id, @Param("quantity") int quantity);

    List<String> findDistinctCategories();
}
