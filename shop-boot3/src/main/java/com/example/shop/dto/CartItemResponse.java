package com.example.shop.dto;

import java.math.BigDecimal;

public record CartItemResponse(
        Long itemId,
        Long productId,
        String productName,
        BigDecimal productPrice,
        String imageUrl,
        Integer quantity,
        BigDecimal subtotal,
        String productStatus
) {}
