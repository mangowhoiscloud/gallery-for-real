package com.example.shop.dto;

import java.math.BigDecimal;

public record OrderItemResponse(
        Long id,
        Long orderId,
        Long productId,
        String productName,
        Integer quantity,
        BigDecimal unitPrice
) {}
