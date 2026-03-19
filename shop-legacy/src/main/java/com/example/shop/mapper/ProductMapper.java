package com.example.shop.mapper;

import com.example.shop.domain.Product;

import java.util.List;
import java.util.Map;

public interface ProductMapper {

    void insert(Product product);

    Product selectById(Long id);

    Product selectActiveById(Long id);

    List<Product> search(Map<String, Object> params);

    int countBySearch(Map<String, Object> params);

    void update(Product product);

    void updateStock(Map<String, Object> params);

    List<String> selectDistinctCategories();
}
