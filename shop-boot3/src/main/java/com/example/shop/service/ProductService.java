package com.example.shop.service;

import com.example.shop.dto.ProductCreateRequest;
import com.example.shop.dto.ProductPageResponse;
import com.example.shop.dto.ProductResponse;
import com.example.shop.dto.ProductUpdateRequest;
import com.example.shop.entity.Product;
import com.example.shop.entity.ProductStatus;
import com.example.shop.mapper.ProductMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;
import java.util.NoSuchElementException;

@Service
@Transactional(readOnly = true)
public class ProductService {

    private final ProductMapper productMapper;

    public ProductService(ProductMapper productMapper) {
        this.productMapper = productMapper;
    }

    public ProductPageResponse listActive(int page, int size) {
        if (size > 100) size = 100;
        int offset = page * size;
        List<ProductResponse> content = productMapper.findAllActive(offset, size)
                .stream()
                .map(ProductResponse::from)
                .toList();
        int totalElements = productMapper.countAllActive();
        int totalPages = (int) Math.ceil((double) totalElements / size);
        return new ProductPageResponse(content, totalPages, totalElements, page, size);
    }

    public ProductResponse getById(Long id) {
        Product product = productMapper.findById(id);
        if (product == null) {
            throw new NoSuchElementException("Product not found: " + id);
        }
        return ProductResponse.from(product);
    }

    @Transactional
    public ProductResponse create(ProductCreateRequest request) {
        Product product = new Product();
        product.setName(request.name());
        product.setDescription(request.description());
        product.setPrice(request.price());
        product.setStockQuantity(request.stockQuantity());
        product.setCategory(request.category());
        product.setImageUrl(request.imageUrl());
        product.setStatus(ProductStatus.ACTIVE);
        productMapper.insert(product);
        return ProductResponse.from(productMapper.findById(product.getId()));
    }

    @Transactional
    public ProductResponse update(Long id, ProductUpdateRequest request) {
        Product product = productMapper.findById(id);
        if (product == null) {
            throw new NoSuchElementException("Product not found: " + id);
        }
        product.setName(request.name());
        product.setDescription(request.description());
        product.setPrice(request.price());
        product.setStockQuantity(request.stockQuantity());
        product.setCategory(request.category());
        product.setImageUrl(request.imageUrl());
        productMapper.update(product);
        return ProductResponse.from(productMapper.findById(id));
    }

    @Transactional
    public void softDelete(Long id) {
        if (productMapper.findById(id) == null) {
            throw new NoSuchElementException("Product not found: " + id);
        }
        productMapper.softDelete(id);
    }

    public ProductPageResponse search(
            String keyword, String category,
            BigDecimal minPrice, BigDecimal maxPrice,
            String sortBy, String sortDir,
            int page, int size) {
        if (size > 100) size = 100;
        int offset = page * size;
        List<ProductResponse> content = productMapper.search(
                        keyword, category, minPrice, maxPrice, sortBy, sortDir, offset, size)
                .stream()
                .map(ProductResponse::from)
                .toList();
        int totalElements = productMapper.countSearch(keyword, category, minPrice, maxPrice);
        int totalPages = (int) Math.ceil((double) totalElements / size);
        return new ProductPageResponse(content, totalPages, totalElements, page, size);
    }
}
