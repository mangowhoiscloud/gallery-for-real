package com.example.shop.dto;

import java.util.List;

public record OrderPageResponse(
        List<OrderResponse> content,
        int totalPages,
        long totalElements,
        int currentPage,
        int pageSize
) {}
