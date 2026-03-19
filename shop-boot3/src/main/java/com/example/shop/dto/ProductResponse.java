package com.example.shop.dto;

import com.example.shop.entity.Product;
import com.example.shop.entity.ProductStatus;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public record ProductResponse(
        Long id,
        String name,
        String description,
        BigDecimal price,
        Integer stockQuantity,
        String category,
        String imageUrl,
        ProductStatus status,
        LocalDateTime createdAt,
        LocalDateTime updatedAt
) {
    public static ProductResponse from(Product p) {
        return new ProductResponse(
                p.getId(), p.getName(), p.getDescription(), p.getPrice(),
                p.getStockQuantity(), p.getCategory(), p.getImageUrl(),
                p.getStatus(), p.getCreatedAt(), p.getUpdatedAt()
        );
    }
}
