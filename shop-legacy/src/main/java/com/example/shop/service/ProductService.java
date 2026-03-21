package com.example.shop.service;

import com.example.shop.domain.Product;
import com.example.shop.dto.PageResponse;
import com.example.shop.dto.ProductCreateRequest;
import com.example.shop.dto.ProductResponse;
import com.example.shop.dto.ProductUpdateRequest;
import com.example.shop.exception.BusinessException;
import com.example.shop.mapper.ProductMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@Transactional
public class ProductService {

    @Autowired private ProductMapper productMapper;

    public ProductResponse create(ProductCreateRequest request) {
        Product product = new Product();
        product.setName(request.getName());
        product.setDescription(request.getDescription());
        product.setPrice(request.getPrice());
        product.setStockQuantity(request.getStockQuantity());
        product.setCategory(request.getCategory());
        product.setImageUrl(request.getImageUrl());
        product.setStatus(Product.Status.ACTIVE);
        productMapper.insert(product);
        return toResponse(product);
    }

    public ProductResponse getById(Long id) {
        Product product = productMapper.selectById(id);
        if (product == null) {
            throw new BusinessException(HttpStatus.NOT_FOUND, "Product not found");
        }
        return toResponse(product);
    }

    public PageResponse<ProductResponse> search(String keyword, String category,
                                                 String minPrice, String maxPrice,
                                                 String sortBy, String sortDir,
                                                 int page, int size) {
        Map<String, Object> params = new HashMap<String, Object>();
        params.put("keyword", keyword != null && !keyword.isEmpty() ? "%" + keyword + "%" : null);
        params.put("category", category);
        params.put("minPrice", minPrice != null ? new java.math.BigDecimal(minPrice) : null);
        params.put("maxPrice", maxPrice != null ? new java.math.BigDecimal(maxPrice) : null);
        // Mapper uses combined sort key: price_asc, price_desc, name_asc, name_desc
        String sort = (sortBy != null && sortDir != null) ? sortBy + "_" + sortDir : null;
        params.put("sort", sort);
        params.put("limit", size);
        params.put("offset", page * size);

        List<Product> products = productMapper.search(params);
        int total = productMapper.countBySearch(params);

        List<ProductResponse> content = new ArrayList<ProductResponse>();
        for (Product p : products) {
            content.add(toResponse(p));
        }
        return new PageResponse<ProductResponse>(content, total, page, size);
    }

    public ProductResponse update(Long id, ProductUpdateRequest request) {
        Product product = productMapper.selectById(id);
        if (product == null) {
            throw new BusinessException(HttpStatus.NOT_FOUND, "Product not found");
        }
        if (request.getName() != null) product.setName(request.getName());
        if (request.getDescription() != null) product.setDescription(request.getDescription());
        if (request.getPrice() != null) product.setPrice(request.getPrice());
        if (request.getStockQuantity() != null) product.setStockQuantity(request.getStockQuantity());
        if (request.getCategory() != null) product.setCategory(request.getCategory());
        if (request.getImageUrl() != null) product.setImageUrl(request.getImageUrl());
        productMapper.update(product);
        return toResponse(product);
    }

    public void delete(Long id) {
        Product product = productMapper.selectById(id);
        if (product == null) {
            throw new BusinessException(HttpStatus.NOT_FOUND, "Product not found");
        }
        product.setStatus(Product.Status.INACTIVE);
        productMapper.update(product);
    }

    public List<String> getCategories() {
        return productMapper.selectDistinctCategories();
    }

    private ProductResponse toResponse(Product product) {
        ProductResponse response = new ProductResponse();
        response.setId(product.getId());
        response.setName(product.getName());
        response.setDescription(product.getDescription());
        response.setPrice(product.getPrice());
        response.setStockQuantity(product.getStockQuantity());
        response.setCategory(product.getCategory());
        response.setImageUrl(product.getImageUrl());
        response.setStatus(product.getStatus() != null ? product.getStatus().name() : null);
        response.setCreatedAt(product.getCreatedAt());
        response.setUpdatedAt(product.getUpdatedAt());
        return response;
    }
}
